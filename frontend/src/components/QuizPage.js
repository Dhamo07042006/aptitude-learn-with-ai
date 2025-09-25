import React, { useState } from "react";
import UploadDataset from "./UploadDataset";

export default function QuizPage() {
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [message, setMessage] = useState("");

  // Called by UploadDataset after upload success
  const handleUploadSuccess = (firstQuestions) => {
    setQuestions(firstQuestions);
    setMessage(""); // clear previous messages
  };

  const handleAnswer = (id, option) => {
    setAnswers({ ...answers, [id]: option });
  };

  const handleSubmit = async () => {
    try {
      const res = await fetch("http://localhost:5000/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answers }),
      });

      const data = await res.json();
      setMessage(data.message || data.result);

      if (data.result === "success" || data.result === "fail") {
        // fetch next questions after success or reload same level
        const qRes = await fetch("http://localhost:5000/get-questions");
        const qData = await qRes.json();
        setQuestions(qData);
        setAnswers({});
      }
    } catch (err) {
      console.error(err);
      setMessage("Submission failed. Check console.");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1 style={{ fontSize: 24, fontWeight: "bold", marginBottom: 20 }}>Aptitude Quiz</h1>

      {/* Upload Dataset */}
      <UploadDataset onUploadSuccess={handleUploadSuccess} />

      {/* Show Questions */}
      {questions.length > 0 && (
        <div>
          {questions.map((q, i) => (
            <div key={q.id} style={{ marginBottom: 20, padding: 12, border: "1px solid #ccc", borderRadius: 8 }}>
              <p style={{ fontWeight: "bold" }}>{i + 1}. {q.question_text}</p>
              <ul style={{ listStyleType: "none", paddingLeft: 0 }}>
                {["a", "b", "c", "d"].map(opt => q[`option_${opt}`] && (
                  <li key={opt} style={{ marginBottom: 6 }}>
                    <label>
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        value={opt}
                        onChange={() => handleAnswer(q.id, opt)}
                        checked={answers[q.id] === opt}
                        style={{ marginRight: 8 }}
                      />
                      {q[`option_${opt}`]}
                    </label>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <button
            onClick={handleSubmit}
            style={{
              padding: "12px 24px",
              backgroundColor: "#667eea",
              color: "white",
              border: "none",
              borderRadius: 8,
              cursor: "pointer",
            }}
          >
            Submit
          </button>

          {message && (
            <p style={{ marginTop: 20, color: "green", fontWeight: "bold" }}>{message}</p>
          )}
        </div>
      )}
    </div>
  );
}
