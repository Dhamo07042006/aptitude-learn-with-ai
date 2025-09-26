import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import time
import os

# Import your report generator
from ml_model import report_generator  # Make sure ml_model/__init__.py exists

app = Flask(__name__)
CORS(app)

# -------------------- Global Variables --------------------
dataset = None
used_questions = {}       # Track used question IDs per difficulty
current_difficulty = "Very easy"
user_sessions = {}        # Track per-user sessions

# -------------------- Utility Functions --------------------
def standardize_dataset(df):
    """
    Normalize and standardize dataset columns.
    Handles multiple variations for column names.
    Ensures all required columns exist.
    """
    # Normalize column names: lowercase, strip spaces
    df.columns = [c.strip().lower() for c in df.columns]

    # Mapping variations to standard names
    rename_map = {
        "question_text": ["question_text","questiontext", "question text", "question", "ques", "q"],
        "option_a": ["optiona", "option a", "a", "a)", "ans_a", "answer_a", "opt1", "option_a"],
        "option_b": ["optionb", "option b", "b", "b)", "ans_b", "answer_b", "opt2", "option_b"],
        "option_c": ["optionc", "option c", "c", "c)", "ans_c", "answer_c", "opt3", "option_c"],
        "option_d": ["optiond", "option d", "d", "d)", "ans_d", "answer_d", "opt4", "option_d"],
        "answer": ["answer", "ans", "solution", "correct answer", "correct", "answer key"],
        "topic": ["topic", "subject", "category", "chapter"],
        "subtopic": ["subtopic", "sub-topic", "section", "sub_section", "subchapter"],
        "difficulty": ["difficulty", "level", "hardness"]
    }

    # Map detected variants to standard names
    new_cols = {}
    for std_col, variants in rename_map.items():
        for variant in variants:
            if variant.lower() in df.columns:
                new_cols[variant.lower()] = std_col
                break
    df.rename(columns=new_cols, inplace=True)

    # Ensure all required columns exist
    defaults = {
        "question_text": "No question text",
        "answer": "a",
        "difficulty": "Very easy",
        "topic": "General",
        "subtopic": "General"
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val

    return df

# -------------------- Upload Dataset --------------------
@app.route("/upload", methods=["POST"])
def upload_dataset():
    global dataset, used_questions, current_difficulty

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # ------------------ Robust File Reading ------------------
    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            # Try multiple delimiters for CSV
            content = file.read().decode()
            file.seek(0)
            delimiters = [';', ',', '\t', '|']
            for delim in delimiters:
                try:
                    df = pd.read_csv(file, sep=delim)
                    if df.shape[1] > 1:  # Ensure multiple columns detected
                        break
                    file.seek(0)
                except Exception:
                    file.seek(0)
            else:
                return jsonify({"error": "Failed to detect delimiter. Please use CSV with ; , \\t or |"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400
    # ----------------------------------------------------------

    # Standardize columns
    dataset = standardize_dataset(df)

    # Add ID column if missing
    if "id" not in dataset.columns:
        dataset.insert(0, "id", range(1, len(dataset)+1))

    # Reset tracking
    used_questions.clear()
    current_difficulty = "Very easy"
    used_questions[current_difficulty] = set()

    # Select 10 questions for the first test
    available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]
    grouped = available.groupby(["topic", "subtopic"], sort=False) if "topic" in available.columns and "subtopic" in available.columns else [(("General","General"), available)]
    selected = pd.DataFrame()
    for _, group in grouped:
        take = min(1, len(group))
        selected = pd.concat([selected, group.sample(take)])
    if len(selected) < 10:
        remaining = available.drop(selected.index, errors="ignore")
        extra_needed = 10 - len(selected)
        selected = pd.concat([selected, remaining.sample(min(extra_needed, len(remaining)))])
    selected = selected.head(10)
    used_questions[current_difficulty].update(selected["id"].tolist())

    # Track session
    user_sessions["test_user"] = {"start_time": time.time(), "time_logs": {}}

    return jsonify({
        "message": "Dataset uploaded successfully!",
        "questions": selected.to_dict(orient="records"),
        "time_limit": 3600
    })

# -------------------- Submit Answers --------------------
@app.route("/submit", methods=["POST"])
def submit_answers():
    global dataset, current_difficulty, used_questions

    data = request.json
    answers = data.get("answers", {})
    time_logs = data.get("time_logs", {})

    session = user_sessions.get("test_user", {})
    start_time = session.get("start_time", time.time())
    elapsed_time = time.time() - start_time
    if elapsed_time > 3600:
        return jsonify({"error": "⏳ Test time exceeded 1 hour. Auto-submitted."}), 403

    correct_count = 0
    solutions = []
    total_time = 0
    max_time_val = -1
    max_time_q = None

    for qid, user_ans in answers.items():
        try:
            qid_int = int(float(qid))
            row = dataset[dataset["id"] == qid_int].iloc[0]
            correct_ans = str(row["answer"]).strip().lower()
            user_ans_clean = str(user_ans).strip().lower()
            is_correct = correct_ans == user_ans_clean
            if is_correct:
                correct_count += 1

            q_time = float(time_logs.get(str(qid), 0))
            total_time += q_time
            if q_time > max_time_val:
                max_time_val = q_time
                max_time_q = row["question_text"]

            solutions.append({
                "question": row["question_text"],
                "user_answer": user_ans,
                "correct_answer": row["answer"],
                "is_correct": is_correct,
                "time_taken": round(q_time, 2),
                "topic": row.get("topic", "General"),
                "subtopic": row.get("subtopic", "General")
            })
        except Exception:
            continue

    avg_time = round(total_time / len(answers), 2) if answers else 0

    # -------------------- Determine Next Level or Retry --------------------
    if correct_count == 10:
        next_level_map = {"very easy": "Easy", "easy": "Moderate", "moderate": "Difficult"}
        current_difficulty = next_level_map.get(current_difficulty.lower(), None)
        if not current_difficulty:
            return jsonify({
                "result": "completed",
                "message": "🎉 Congratulations! You mastered all levels!",
                "score": correct_count,
                "solutions": solutions,
                "average_time": avg_time,
                "max_time_question": max_time_q,
                "max_time_value": round(max_time_val, 2),
                "elapsed_time": round(elapsed_time, 2)
            })

        if current_difficulty not in used_questions:
            used_questions[current_difficulty] = set()

        available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]
        remaining = available[~available["id"].isin(used_questions[current_difficulty])]
        if len(remaining) < 10:
            used_questions[current_difficulty] = set()
            remaining = available
        selected = remaining.sample(10)
        used_questions[current_difficulty].update(selected["id"].tolist())

        return jsonify({
            "result": "success",
            "message": f"✅ You completed {current_difficulty} level!",
            "score": correct_count,
            "solutions": solutions,
            "average_time": avg_time,
            "max_time_question": max_time_q,
            "max_time_value": round(max_time_val, 2),
            "elapsed_time": round(elapsed_time, 2),
            "next_level": current_difficulty,
            "questions": selected.to_dict(orient="records")
        })

    # Retry same level
    available = dataset[
        (dataset["difficulty"].str.lower() == current_difficulty.lower()) &
        (~dataset["id"].isin(used_questions[current_difficulty]))
    ]
    if len(available) < 10:
        used_questions[current_difficulty] = set()
        available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]
    selected = available.sample(10)
    used_questions[current_difficulty].update(selected["id"].tolist())

    return jsonify({
        "result": "fail",
        "message": f"❌ You got {correct_count}/10 correct. Try again!",
        "score": correct_count,
        "solutions": solutions,
        "average_time": avg_time,
        "max_time_question": max_time_q,
        "max_time_value": round(max_time_val, 2),
        "elapsed_time": round(elapsed_time, 2),
        "questions": selected.to_dict(orient="records")
    })

# -------------------- Generate Report --------------------
@app.route("/generate_report", methods=["POST"])
def generate_report_endpoint():
    data = request.json
    solutions = data.get("solutions")
    student_name = data.get("student_name", "Student")

    if not solutions or len(solutions) == 0:
        return jsonify({"error": "No solutions provided for report"}), 400

    try:
        reports_dir = "backend/reports"
        os.makedirs(reports_dir, exist_ok=True)
        report_path = report_generator.generate_report(
            solutions=solutions,
            output_dir=reports_dir,
            student_name=student_name
        )
        return send_file(report_path, as_attachment=True)
    except Exception as e:
        print("Report generation error:", e)
        return jsonify({"error": f"Failed to generate report: {str(e)}"}), 500

# -------------------- Main --------------------
if __name__ == "__main__":
    app.run(debug=True)
