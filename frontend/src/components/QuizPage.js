// QuizPage.js
import React, { useState, useEffect } from "react";
import UploadDataset from "./UploadDataset";
import "./QuizPage.css";

export default function QuizPage() {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [message, setMessage] = useState("");
  const [timeLogs, setTimeLogs] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [finished, setFinished] = useState(false);
  const [showNextButton, setShowNextButton] = useState(false);
  const [timer, setTimer] = useState(3600);
  const [testStarted, setTestStarted] = useState(false);
  const [nextQuestions, setNextQuestions] = useState(null);
  const [solutions, setSolutions] = useState([]);
  const [showSolutionIds, setShowSolutionIds] = useState(new Set());
  const [studentName, setStudentName] = useState(""); // <-- Added student name state

  // Timer effect
  useEffect(() => {
    if (questions.length > 0 && !finished && testStarted) {
      const interval = setInterval(() => {
        setTimer((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            handleSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [questions, finished, testStarted]);

  const formatTime = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const handleUploadSuccess = (firstQuestions) => {
    if (!studentName) {
      alert("Please enter your name before starting the test.");
      return;
    }

    setQuestions(firstQuestions);
    setMessage("");
    setCurrentIndex(0);
    setAnswers({});
    setTimeLogs({});
    setFinished(false);
    setShowNextButton(false);
    setStartTime(Date.now());
    setTimer(3600);
    setTestStarted(true);
    setSolutions([]);
    setShowSolutionIds(new Set());
  };

  const handleAnswer = (id, option) => {
    setAnswers({ ...answers, [id]: option });
  };

  const moveQuestion = (direction) => {
    const currentQ = questions[currentIndex];
    if (currentQ) {
      const timeTaken = (Date.now() - startTime) / 1000;
      setTimeLogs((prev) => ({
        ...prev,
        [currentQ.id]: (prev[currentQ.id] || 0) + timeTaken,
      }));
    }
    if (direction === "next" && currentIndex < questions.length - 1)
      setCurrentIndex(currentIndex + 1);
    else if (direction === "prev" && currentIndex > 0)
      setCurrentIndex(currentIndex - 1);
    setStartTime(Date.now());
  };

  const handleSubmit = async () => {
    if (finished) return;

    const currentQ = questions[currentIndex];
    if (currentQ) {
      const timeTaken = (Date.now() - startTime) / 1000;
      setTimeLogs((prev) => ({
        ...prev,
        [currentQ.id]: (prev[currentQ.id] || 0) + timeTaken,
      }));
    }

    try {
      const res = await fetch("http://localhost:5000/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers, time_logs: timeLogs }),
      });

      const data = await res.json();
      if (data.questions) setNextQuestions(data.questions);
      if (data.solutions) setSolutions(data.solutions);

      setMessage(
        `${data.message}\n\n⏱ Avg time/question: ${data.average_time}s\n🐢 Longest: ${data.max_time_value}s (Q: ${data.max_time_question})`
      );
      setFinished(true);
      setShowNextButton(true);
      setTestStarted(false);
    } catch (err) {
      console.error(err);
      setMessage("Submission failed. Check console.");
    }
  };

  const startNextTest = () => {
    if (nextQuestions && nextQuestions.length > 0) {
      setQuestions(nextQuestions);
      setCurrentIndex(0);
      setAnswers({});
      setTimeLogs({});
      setStartTime(Date.now());
      setFinished(false);
      setShowNextButton(false);
      setMessage("");
      setTimer(3600);
      setTestStarted(true);
      setNextQuestions(null);
      setSolutions([]);
      setShowSolutionIds(new Set());
    }
  };

  const toggleSolution = (qid) => {
    const newSet = new Set(showSolutionIds);
    if (newSet.has(qid)) newSet.delete(qid);
    else newSet.add(qid);
    setShowSolutionIds(newSet);
  };

  // ✅ Generate report
  const handleGenerateReport = async () => {
    if (!solutions || solutions.length === 0) {
      alert("No solutions to generate report.");
      return;
    }
    try {
      const res = await fetch("http://localhost:5000/generate_report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ solutions, student_name: studentName || "Student" }),
      });

      if (!res.ok) throw new Error("Backend error");

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${studentName || "Student"}_report.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      console.error(err);
      alert("Failed to generate report. Check backend.");
    }
  };

  return (
    <div className="quiz-container">
      <h1 className="quiz-title">Aptitude Quiz</h1>

      {!testStarted && !finished && (
        <div>
          <input
            type="text"
            placeholder="Enter your name"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            className="student-name-input"
          />
          <UploadDataset onUploadSuccess={handleUploadSuccess} />
        </div>
      )}

      {questions.length > 0 && !finished && testStarted && (
        <div>
          <div className="question-card">
            <p className="question-text">
              {currentIndex + 1}. {questions[currentIndex].question_text}
            </p>
            <p className="question-topic">
              Topic: {questions[currentIndex].topic || "N/A"} | Subtopic:{" "}
              {questions[currentIndex].subtopic || "N/A"}
            </p>

            <ul className="options-list">
              {["a", "b", "c", "d"].map(
                (opt) =>
                  questions[currentIndex][`option_${opt}`] && (
                    <li key={opt}>
                      <label className="option-label">
                        <input
                          type="radio"
                          name={`q-${questions[currentIndex].id}`}
                          value={opt}
                          onChange={() =>
                            handleAnswer(questions[currentIndex].id, opt)
                          }
                          checked={answers[questions[currentIndex].id] === opt}
                        />
                        {questions[currentIndex][`option_${opt}`]}
                      </label>
                    </li>
                  )
              )}
            </ul>
          </div>

          <div className="nav-buttons">
            <button
              onClick={() => moveQuestion("prev")}
              disabled={currentIndex === 0}
            >
              Previous
            </button>
            {currentIndex < questions.length - 1 ? (
              <button onClick={() => moveQuestion("next")}>Next</button>
            ) : (
              <button onClick={handleSubmit} className="submit-btn">
                Submit Test
              </button>
            )}
          </div>

          <p className="question-counter">
            ⏳ Question {currentIndex + 1} of {questions.length}
          </p>
          <p className="timer">🕒 Time Left: {formatTime(timer)}</p>
        </div>
      )}

      {finished && (
        <div className="results-container">
          <pre className="results-message">{message}</pre>

          {solutions.length > 0 &&
            solutions.map((s) => (
              <div key={s.question} className="solution-card">
                <p className="question-text">{s.question}</p>
                <p className="question-topic">
                  Topic: {s.topic || "N/A"} | Subtopic: {s.subtopic || "N/A"}
                </p>

                <button
                  className="show-solution-btn"
                  onClick={() => toggleSolution(s.question)}
                >
                  {showSolutionIds.has(s.question)
                    ? "Hide Solution"
                    : "Show Solution"}
                </button>
                {showSolutionIds.has(s.question) && (
                  <div className="solution-text">
                    ✅ Correct Answer: {s.correct_answer} <br />
                    📝 Your Answer: {s.user_answer} <br />
                    ⏱ Time Taken: {s.time_taken}s <br />
                    {s.is_correct ? "🎉 Correct!" : "❌ Incorrect"}
                  </div>
                )}
              </div>
            ))}

          {showNextButton && (
            <button className="next-test-btn" onClick={startNextTest}>
              Start Next Test
            </button>
          )}

          {solutions.length > 0 && (
            <button
              className="generate-report-btn"
              onClick={handleGenerateReport}
            >
              📄 Generate Report
            </button>
          )}
        </div>
      )}
    </div>
  );
}
