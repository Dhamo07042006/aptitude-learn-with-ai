import React, { useState } from "react";
import "./UploadDataset.css";

export default function UploadDataset({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [uploaded, setUploaded] = useState(false);

  const handleFileSelect = (e) => {
    setSelectedFile(e.target.files[0] || null);
    setMessage("");
    setMessageType("");
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setMessage("Please select a file first!");
      setMessageType("error");
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(data.message);
        setMessageType("success");
        setUploaded(true);
        if (data.questions) onUploadSuccess(data.questions);
      } else {
        setMessage(data.error || "Upload failed.");
        setMessageType("error");
      }
    } catch (err) {
      console.error(err);
      setMessage("Upload failed. Check console.");
      setMessageType("error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <h2 className="upload-title">Upload Quiz Dataset</h2>

      {!uploaded && (
        <>
          <input
            id="fileInput"
            type="file"
            accept=".csv,.xlsx"
            onChange={handleFileSelect}
            className="file-input"
          />
          <button
            onClick={handleUpload}
            disabled={isLoading}
            className={`upload-btn ${isLoading ? "loading" : ""}`}
          >
            {isLoading ? "Uploading..." : "Upload"}
          </button>
        </>
      )}

      {uploaded && (
        <p className="success-message">✅ Dataset uploaded successfully! You can now start the test.</p>
      )}

      {message && !uploaded && (
        <p className={`upload-message ${messageType === "success" ? "success" : "error"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
