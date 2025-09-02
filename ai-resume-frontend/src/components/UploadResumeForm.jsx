// UploadResumeForm.jsx
import React, { useState, useCallback } from "react";
import "./UploadResumeForm.css";
import logo from "../assets/vishwakarma_logo.png";

function UploadResumeForm({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (selectedFile) => {
    setError("");
    if (selectedFile && selectedFile.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      setFile(null);
      return;
    }

    // Check file size (5MB max)
    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      setError("File size exceeds 5MB limit.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleInputChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileChange(selectedFile);
    }
  };

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileChange(droppedFiles[0]);
    }
  }, []);

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
        const errorText = await response.text();
        throw new Error(errorText || "Upload failed");
      }

      const result = await response.json();

      // Check if the response contains an error
      if (result.error) {
        throw new Error(result.error);
      }

      onUploadSuccess(result);
    } catch (err) {
      setError(err.message || "An error occurred during analysis");
    } finally {
      setUploading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form-container">
      {/* Logo Header */}
      <div className="upload-form-header">
        <img src={logo} alt="VU Logo" className="vu-logo" />
        <h2 className="upload-form-title">VU Resume Analyzer</h2>
      </div>

      <p className="upload-form-instruction">
        Upload your resume as a <strong>PDF</strong>. Our AI will analyze it and
        provide structured feedback to improve your chances!
      </p>

      {/* Drag and Drop Area */}
      <div
        className={`drag-drop-area ${isDragging ? "drag-over" : ""} ${
          file ? "has-file" : ""
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="drag-drop-content">
          <div className="upload-icon">
            {file ? "📄" : isDragging ? "⬆️" : "📁"}
          </div>
          <p className="drag-drop-text">
            {isDragging
              ? "Drop your resume here"
              : file
              ? file.name
              : "Drag & drop your PDF resume here"}
          </p>
          <p className="drag-drop-subtext">
            {file ? "File selected successfully!" : "or"}
          </p>
          {!file && (
            <label htmlFor="file-input" className="browse-file-button">
              Browse files
            </label>
          )}
          <input
            id="file-input"
            type="file"
            onChange={handleInputChange}
            accept="application/pdf"
            className="upload-file-input"
          />
        </div>
      </div>

      {file && (
        <div className="file-details">
          <p className="upload-selected-file">
            📄 {file.name} ({(file.size / 1024).toFixed(2)} KB)
          </p>
          <button
            type="button"
            className="remove-file-button"
            onClick={() => setFile(null)}
          >
            Remove
          </button>
        </div>
      )}

      {error && <p className="upload-error-message">⚠ {error}</p>}

      <button
        type="submit"
        disabled={!file || uploading}
        className="upload-submit-button"
      >
        {uploading ? "⏳ Analyzing..." : "🚀 Analyze Resume"}
      </button>

      <p className="upload-form-footer">
        Supported format: <strong>PDF only</strong>. Max size:{" "}
        <strong>5MB</strong>.
      </p>
    </form>
  );
}

export default UploadResumeForm;
