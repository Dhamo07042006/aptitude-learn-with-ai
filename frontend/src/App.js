// App.js
import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./components/Login";
import Signup from "./components/Signup";
import UploadDataset from "./components/UploadDataset";
import QuizPage from "./components/QuizPage";

function App() {
  return (
    <Router>
      <Routes>
        {/* Base URL "/" redirects to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Login page */}
        <Route path="/login" element={<Login />} />

        {/* Signup page */}
        <Route path="/signup" element={<Signup />} />

        {/* Upload dataset (requires login) */}
        <Route
          path="/upload"
          element={
            localStorage.getItem("user") ? <UploadDataset /> : <Navigate to="/login" />
          }
        />

        {/* Quiz page */}
        <Route
          path="/quiz"
          element={localStorage.getItem("user") ? <QuizPage /> : <Navigate to="/login" />}
        />
      </Routes>
    </Router>
  );
}

export default App;
