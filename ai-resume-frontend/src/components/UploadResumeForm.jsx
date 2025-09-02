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
    // Only set dragging to false if leaving the drop zone entirely
    if (e.currentTarget.contains(e.relatedTarget)) return;
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileChange(droppedFile);
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
