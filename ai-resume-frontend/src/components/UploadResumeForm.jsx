import React, { useState } from "react";
import "./UploadResumeForm.css";
import logo from "../assets/vishwakarma_logo.png";

function UploadResumeForm({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e) => {
    setError("");
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a PDF file first.");
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/analyze_resume", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      const result = await response.json();
      onUploadSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form-container">
      {/* Logo Header */}
      <div className="upload-form-header">
        <img src={logo} alt="VIT Logo" className="vit-logo" />
        <h2 className="upload-form-title">VIT Resume Analyzer</h2>
      </div>

      <p className="upload-form-instruction">
        Upload your resume as a <strong>PDF</strong>. Our AI will analyze it and
        provide structured feedback to improve your chances!
      </p>

      {file && (
        <p className="upload-selected-file">
          📄 {file.name} ({(file.size / 1024).toFixed(2)} KB)
        </p>
      )}

      <input
        type="file"
        onChange={handleFileChange}
        accept="application/pdf"
        className="upload-file-input"
      />

      {error && <p className="upload-error-message">⚠ {error}</p>}

      <button
        type="submit"
        disabled={!file || uploading}
        className="upload-submit-button"
      >
        {uploading ? "⏳ Uploading..." : "🚀 Upload Resume"}
      </button>

      <p className="upload-form-footer">
        Supported format: <strong>PDF only</strong>. Max size:{" "}
        <strong>5MB</strong>.
      </p>
    </form>
  );
}

export default UploadResumeForm;
