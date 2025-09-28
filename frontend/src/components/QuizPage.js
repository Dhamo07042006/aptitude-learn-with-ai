// QuizPage.js
import React, { useState, useEffect, useRef } from "react";
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
  const [studentName, setStudentName] = useState("");

  // Chatbot state
  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatOpen, setChatOpen] = useState(false);
  const chatWindowRef = useRef(null);

  // Load studentName from localStorage (or any DB/session logic)
  useEffect(() => {
    const user = JSON.parse(localStorage.getItem("user")); // replace with your login info
    if (user && user.username) setStudentName(user.username);
  }, []);

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

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [chatHistory]);

  const formatTime = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const handleUploadSuccess = (firstQuestions) => {
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

    // Reset chatbot for new test
    setChatHistory([]);
    setChatInput("");
    setChatOpen(false); // Keep chat closed
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

    // Keep chat open for same question
    setChatInput("");
    setChatHistory([]); // reset messages per question
    setChatOpen(false);
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

      // Reset chatbot for new test
      setChatHistory([]);
      setChatInput("");
      setChatOpen(true); // Keep chat open
    }
  };

  const toggleSolution = (qid) => {
    const newSet = new Set(showSolutionIds);
    if (newSet.has(qid)) newSet.delete(qid);
    else newSet.add(qid);
    setShowSolutionIds(newSet);
  };

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

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const newMsg = { sender: "user", text: chatInput };
    setChatHistory((prev) => [...prev, newMsg]);
    setChatInput("");

    try {
      const res = await fetch("http://localhost:5000/chatbot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: newMsg.text }),
      });
      const data = await res.json();
      setChatHistory((prev) => [...prev, { sender: "bot", text: data.reply }]);
    } catch (err) {
      setChatHistory((prev) => [...prev, { sender: "bot", text: "⚠️ Chatbot error" }]);
    }
  };

  return (
    <div className="quiz-container">
      <h1 className="quiz-title">Aptitude Quiz</h1>

      {!testStarted && !finished && (
        <div>
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

          {/* Chatbot Panel per question */}
          <div className={`chatbot-container ${chatOpen ? "open" : "closed"}`}>
            <button
              className="chat-toggle-btn"
              onClick={() => setChatOpen(!chatOpen)}
            >
              💬 {chatOpen ? "Close" : "Chat"}
            </button>

            {chatOpen && (
              <div className="chat-panel">
                <h2>💬 Chatbot Assistant</h2>
                <div
                  className="chat-window"
                  ref={chatWindowRef}
                  style={{
                    maxHeight: "300px",
                    overflowY: "auto",
                    padding: "8px",
                    border: "1px solid #ccc",
                    marginBottom: "8px",
                  }}
                >
                  {chatHistory.map((msg, i) => (
                    <p
                      key={i}
                      className={msg.sender === "user" ? "chat-user" : "chat-bot"}
                    >
                      <b>{msg.sender === "user" ? "You" : "Bot"}:</b> {msg.text}
                    </p>
                  ))}
                </div>
                <div
                  className="chat-input"
                  style={{ display: "flex", gap: "8px" }}
                >
                  <input
                    type="text"
                    value={chatInput}
                    placeholder="Ask the bot..."
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleChatSend()}
                    style={{ flex: 1 }}
                  />
                  <button onClick={handleChatSend}>Send</button>
                </div>
              </div>
            )}
          </div>
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
