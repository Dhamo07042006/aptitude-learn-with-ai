import React, { useState } from "react";

export default function UploadDataset({ onUploadSuccess }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState("");
  const [isLoading, setIsLoading] = useState(false);

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
        if (data.questions) onUploadSuccess(data.questions);

        setSelectedFile(null);
        const fileInput = document.getElementById("fileInput");
        if (fileInput) fileInput.value = "";
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
    <div style={{ padding: 20, border: "1px solid #ccc", borderRadius: 12, marginBottom: 20 }}>
      <h2>Upload Quiz Dataset</h2>
      <input id="fileInput" type="file" accept=".csv,.xlsx" onChange={handleFileSelect} />
      <button
        onClick={handleUpload}
        disabled={isLoading}
        style={{
          marginLeft: 10,
          padding: "8px 16px",
          backgroundColor: isLoading ? "#a0aec0" : "green",
          color: "#fff",
          border: "none",
          borderRadius: 6,
          cursor: isLoading ? "not-allowed" : "pointer",
        }}
      >
        {isLoading ? "Uploading..." : "Upload"}
      </button>
      {message && (
        <p style={{ marginTop: 10, color: messageType === "success" ? "green" : "red" }}>
          {message}
        </p>
      )}
    </div>
  );
}
