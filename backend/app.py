import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

dataset = None
used_questions = {}  # Track used question IDs per difficulty
current_difficulty = "Very easy"


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

    # Rename columns for frontend
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

    return jsonify({
        "message": "Dataset uploaded successfully!",
        "questions": selected.to_dict(orient="records")
    })


# Get 10 random questions
@app.route("/get-questions", methods=["GET"])
def get_questions():
    global dataset, used_questions, current_difficulty
    if dataset is None:
        return jsonify({"error": "Upload dataset first"}), 400

    if current_difficulty not in used_questions:
        used_questions[current_difficulty] = set()

    available = dataset[
        (dataset["difficulty"].str.lower() == current_difficulty.lower()) &
        (~dataset["id"].isin(used_questions[current_difficulty]))
    ]

    # If fewer than 10 remaining, reset used_questions for this difficulty
    if len(available) < 10:
        used_questions[current_difficulty] = set()
        available = dataset[dataset["difficulty"].str.lower() == current_difficulty.lower()]

    selected = available.sample(10)
    used_questions[current_difficulty].update(selected["id"].tolist())
    return jsonify(selected.to_dict(orient="records"))


# Submit answers
@app.route("/submit", methods=["POST"])
def submit_answers():
    global dataset, current_difficulty, used_questions
    data = request.json
    answers = data.get("answers", {})

    correct_count = 0
    for qid, user_ans in answers.items():
        try:
            qid_int = int(float(qid))  # Handle numeric IDs properly
            row = dataset[dataset["id"] == qid_int].iloc[0]
            correct_ans = str(row["answer"]).strip().lower()
            user_ans_clean = str(user_ans).strip().lower()
            if correct_ans == user_ans_clean:
                correct_count += 1
        except IndexError:
            continue  # ID not found in dataset

    # If all 10 correct → move to next difficulty
    if correct_count == 10:
        if current_difficulty.lower() == "very easy":
            current_difficulty = "Easy"
        elif current_difficulty.lower() == "easy":
            current_difficulty = "Moderate"
        elif current_difficulty.lower() == "moderate":
            current_difficulty = "Difficult"
        else:
            return jsonify({"result": "completed", "message": "🎉 Congratulations! You mastered all levels!"})

        # Initialize used questions for new difficulty
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
            "message": f"🎉 You completed the {current_difficulty} level!",
            "next_level": current_difficulty,
            "questions": selected.to_dict(orient="records")
        })

    else:
        # Not all correct → send 10 other random questions in same level
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
            "message": f"❌ You got {correct_count}/10 correct. Try these new questions.",
            "questions": selected.to_dict(orient="records")
        })


if __name__ == "__main__":
    app.run(debug=True)
