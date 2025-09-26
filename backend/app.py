import pandas as pd
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import time
import os

# Import your report generator
from ml_model import report_generator  # Make sure ml_model/__init__.py exists

app = Flask(__name__)
CORS(app)

dataset = None
used_questions = {}  # Track used question IDs per difficulty
current_difficulty = "Very easy"
user_sessions = {}  # Track per-user sessions


def standardize_dataset(df):
    # Normalize column names: lowercase, strip spaces
    df.columns = [c.strip().lower() for c in df.columns]

    # Rename common columns
    rename_map = {
        "questiontext": "question_text",
        "question_text": "question_text",
        "optiona": "option_a",
        "optionb": "option_b",
        "optionc": "option_c",
        "optiond": "option_d",
        "answer": "answer",
        "topic": "topic",
        "subtopic": "subtopic",
        "difficulty": "difficulty"
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # Ensure required columns exist
    if "question_text" not in df.columns:
        df["question_text"] = "No question text"
    if "answer" not in df.columns:
        df["answer"] = "a"
    if "difficulty" not in df.columns:
        df["difficulty"] = "Very easy"
    if "topic" not in df.columns:
        df["topic"] = "General"
    if "subtopic" not in df.columns:
        df["subtopic"] = "General"

    return df


# Upload dataset
@app.route("/upload", methods=["POST"])
def upload_dataset():
    global dataset, used_questions, current_difficulty
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        if file.filename.endswith(".xlsx"):
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Standardize dataframe
    dataset = standardize_dataset(df)

    # Reset tracking
    used_questions.clear()
    current_difficulty = "Very easy"
    used_questions[current_difficulty] = set()

    # Filter questions by difficulty
    available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]

    # Group by topic & subtopic safely
    grouped = available.groupby(["topic", "subtopic"], sort=False) if "topic" in available.columns and "subtopic" in available.columns else [(("General","General"), available)]

    selected = pd.DataFrame()
    for _, group in grouped:
        take = min(1, len(group))  # Take at least 1 per subtopic
        selected = pd.concat([selected, group.sample(take)])

    # Fill remaining to make 10 questions
    if len(selected) < 10:
        remaining = available.drop(selected.index, errors="ignore")
        extra_needed = 10 - len(selected)
        if len(remaining) >= extra_needed:
            selected = pd.concat([selected, remaining.sample(extra_needed)])
        else:
            selected = pd.concat([selected, remaining])

    selected = selected.head(10)
    used_questions[current_difficulty].update(selected["id"].tolist() if "id" in selected.columns else [])

    # Track session start
    user_sessions["test_user"] = {
        "start_time": time.time(),
        "time_logs": {}
    }

    return jsonify({
        "message": "Dataset uploaded successfully!",
        "questions": selected.to_dict(orient="records"),
        "time_limit": 3600
    })


# Submit answers
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

    # Determine next level / retry
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
        remaining = available[~available["id"].isin(used_questions[current_difficulty])] if "id" in available.columns else available
        if len(remaining) < 10:
            used_questions[current_difficulty] = set()
            remaining = available
        selected = remaining.sample(10)
        used_questions[current_difficulty].update(selected["id"].tolist() if "id" in selected.columns else [])

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
    

    # Retry with new questions
    available = dataset[
        (dataset["difficulty"].str.lower() == current_difficulty.lower()) & 
        (~dataset["id"].isin(used_questions[current_difficulty])) if "id" in dataset.columns else dataset
    ]
    if len(available) < 10:
        used_questions[current_difficulty] = set()
        available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]

    selected = available.sample(10)
    used_questions[current_difficulty].update(selected["id"].tolist() if "id" in selected.columns else [])

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


# -------------------- ADD: Generate Report Route --------------------
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


if __name__ == "__main__":
    app.run(debug=True)
