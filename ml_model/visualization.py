import os
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend
import matplotlib.pyplot as plt

def plot_accuracy(accuracy, student_id="student", save_dir="backend/reports"):
    """
    Create a pie chart showing correct vs incorrect answers.
    """
    os.makedirs(save_dir, exist_ok=True)
    labels = ["Correct", "Incorrect"]
    correct = accuracy
    incorrect = 100 - correct
    plt.figure(figsize=(5, 5))
    plt.pie([correct, incorrect], labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title(f"Accuracy of {student_id}")
    chart_path = os.path.join(save_dir, f"{student_id}_accuracy.png")
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def plot_topic_performance(topic_perf, student_id="student", save_dir="backend/reports"):
    """
    Create a bar chart for topic-wise performance.
    topic_perf = {"Algebra": 80, "Geometry": 60}
    """
    os.makedirs(save_dir, exist_ok=True)
    topics = list(topic_perf.keys())
    scores = list(topic_perf.values())
    plt.figure(figsize=(7, 5))
    plt.bar(topics, scores, color="skyblue")
    plt.ylabel("Accuracy (%)")
    plt.title(f"Topic Performance - {student_id}")
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    chart_path = os.path.join(save_dir, f"{student_id}_topic_perf.png")
    plt.savefig(chart_path)
    plt.close()
    return chart_path


def plot_subtopic_performance(subtopic_perf, student_id="student", save_dir="backend/reports"):
    """
    Create a bar chart for subtopic-wise performance.
    subtopic_perf = {"Trigonometry - Basics": 70, "Mensuration - Volume": 50}
    """
    os.makedirs(save_dir, exist_ok=True)
    subtopics = list(subtopic_perf.keys())
    scores = list(subtopic_perf.values())
    plt.figure(figsize=(7, 5))
    plt.bar(subtopics, scores, color="orange")
    plt.ylabel("Accuracy (%)")
    plt.title(f"Subtopic Performance - {student_id}")
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    chart_path = os.path.join(save_dir, f"{student_id}_subtopic_perf.png")
    plt.savefig(chart_path)
    plt.close()
    return chart_path