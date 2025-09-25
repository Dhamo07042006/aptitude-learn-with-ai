import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

dataset = None
used_questions = {}  # Track used question IDs per difficulty
current_difficulty = "Very easy"
user_sessions = {}  # Track per-user sessions


# Upload dataset
@app.route("/upload", methods=["POST"])
def upload_dataset():
    global dataset, used_questions, current_difficulty
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    try:
        if file.filename.endswith(".xlsx"):
            dataset = pd.read_excel(file)
        else:
            dataset = pd.read_csv(file)
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Standardize column names
    dataset.rename(columns={
        "questiontext": "question_text",
        "optiona": "option_a",
        "optionb": "option_b",
        "optionc": "option_c",
        "optiond": "option_d"
    }, inplace=True)

    used_questions.clear()
    current_difficulty = "Very easy"
    used_questions[current_difficulty] = set()

    # First 10 questions
    available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]
    selected = available.sample(10)
    used_questions[current_difficulty].update(selected["id"].tolist())

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
    if elapsed_time > 3600:  # 1 hour limit
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
                "time_taken": round(q_time, 2)
            })
        except Exception:
            continue

    avg_time = round(total_time / len(answers), 2) if answers else 0

    # All correct → move to next level
    if correct_count == 10:
        if current_difficulty.lower() == "very easy":
            current_difficulty = "Easy"
        elif current_difficulty.lower() == "easy":
            current_difficulty = "Moderate"
        elif current_difficulty.lower() == "moderate":
            current_difficulty = "Difficult"
        else:
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

    # Failed case → retry with new questions
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


if __name__ == "__main__":
    app.run(debug=True)
