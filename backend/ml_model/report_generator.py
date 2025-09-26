import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for server-side plotting
import matplotlib.pyplot as plt
import seaborn as sns
from docx import Document
from docx.shared import Inches

def generate_report(solutions, output_dir="reports", student_name="Student"):
    """
    Generate a Word report with charts and question-wise analysis.
    
    solutions: list of dicts, each dict has keys:
        - question, user_answer, correct_answer, is_correct, time_taken, topic, subtopic
    output_dir: folder to save reports
    student_name: name of the student for report title
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df = pd.DataFrame(solutions)
    df["is_correct"] = df["is_correct"].astype(bool)
    df["time_taken"] = df["time_taken"].astype(float)
    
    # ----- Topic Accuracy -----
    topic_acc = df.groupby("topic")["is_correct"].mean() * 100
    plt.figure(figsize=(8,5))
    sns.barplot(x=topic_acc.index, y=topic_acc.values, palette="Blues_d")
    plt.ylim(0,100)
    plt.ylabel("Accuracy (%)")
    plt.title("Topic Accuracy")
    topic_chart_path = os.path.join(output_dir, "topic_accuracy.png")
    plt.savefig(topic_chart_path)
    plt.close()

    # ----- Subtopic Accuracy -----
    subtopic_acc = df.groupby("subtopic")["is_correct"].mean() * 100
    plt.figure(figsize=(10,5))
    sns.barplot(x=subtopic_acc.index, y=subtopic_acc.values, palette="Greens_d")
    plt.ylim(0,100)
    plt.ylabel("Accuracy (%)")
    plt.title("Subtopic Accuracy")
    subtopic_chart_path = os.path.join(output_dir, "subtopic_accuracy.png")
    plt.savefig(subtopic_chart_path)
    plt.close()

    # ----- Learning Fundamentals -----
    # Use get with default to avoid KeyError if 'difficulty' missing
    fundamentals = {
        "Listening": max(0, 100 - df["time_taken"].mean()),
        "Grasping": df["is_correct"].mean() * 100,
        "Retention": 100 - df[~df["is_correct"]].shape[0]/df.shape[0]*100,
        "Application": df[df.get("difficulty", pd.Series(["Very easy"]*len(df))).isin(["Moderate","Difficult"])]["is_correct"].mean() * 100
    }

    plt.figure(figsize=(6,4))
    sns.barplot(x=list(fundamentals.keys()), y=list(fundamentals.values()), palette="Oranges_d")
    plt.ylim(0,100)
    plt.ylabel("Score (%)")
    plt.title("Learning Fundamentals")
    fundamentals_chart_path = os.path.join(output_dir, "fundamentals.png")
    plt.savefig(fundamentals_chart_path)
    plt.close()

    # ----- Generate Word Report -----
    report_path = os.path.join(output_dir, f"{student_name}_report.docx")
    doc = Document()
    doc.add_heading(f"{student_name} - Performance Report", 0)
    doc.add_paragraph("This report provides detailed insights into student's performance by topic, subtopic, and learning fundamentals.\n")

    # Learning Fundamentals
    doc.add_heading("Learning Fundamentals", level=1)
    for k, v in fundamentals.items():
        doc.add_paragraph(f"{k}: {v:.2f}%")
    doc.add_picture(fundamentals_chart_path, width=Inches(5))

    # Topic Accuracy
    doc.add_heading("Topic Accuracy", level=1)
    doc.add_picture(topic_chart_path, width=Inches(5))

    # Subtopic Accuracy
    doc.add_heading("Subtopic Accuracy", level=1)
    doc.add_picture(subtopic_chart_path, width=Inches(5))

    # Question-wise Performance
    doc.add_heading("Question-wise Performance", level=1)
    for i, row in df.iterrows():
        doc.add_paragraph(
            f"Q: {row['question']}\n"
            f"Topic/Subtopic: {row['topic']} / {row['subtopic']}\n"
            f"Your Answer: {row['user_answer']} | Correct Answer: {row['correct_answer']} | "
            f"{'✅ Correct' if row['is_correct'] else '❌ Incorrect'} | Time Taken: {row['time_taken']}s"
        )

    doc.save(report_path)
    print(f"Report generated: {report_path}")
    return report_path
