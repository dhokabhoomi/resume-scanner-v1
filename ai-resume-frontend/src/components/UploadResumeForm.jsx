import React, { useState, useCallback } from "react";
import "./UploadResumeForm.css";
import logo from "../assets/vishwakarma_logo.png";
import { API_ENDPOINTS } from "../config/api";

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

    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      setError("File size exceeds 5MB limit.");
      setFile(null);
      return;
    }

    setFile(selectedFile);
  };

  const handleInputChange = (e) => {
    if (e.target.files[0]) handleFileChange(e.target.files[0]);
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
    if (e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
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
      console.log('Uploading to:', API_ENDPOINTS.ANALYZE_RESUME);
      
      const response = await fetch(API_ENDPOINTS.ANALYZE_RESUME, {
        method: "POST",
        body: formData,
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log('Error response:', errorText);
        throw new Error(`Upload failed: ${response.status} - ${errorText || 'Unknown error'}`);
      }

      const result = await response.json();
      console.log('Success response:', result);
      
      if (result.error) throw new Error(result.error);

      onUploadSuccess(result);
    } catch (err) {
      console.error('Upload error:', err);
      
      // More detailed error messages
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        setError("Cannot connect to server. Please check if the backend is running.");
      } else if (err.message.includes('CORS')) {
        setError("CORS error: Server configuration issue.");
      } else {
        setError(err.message || "An error occurred during analysis");
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="form-container">
      <form onSubmit={handleSubmit} className="upload-form-container">
        {/* Logo Header */}
        <div className="upload-form-header">
          <img src={logo} alt="VU Logo" className="vu-logo" />
          <h2 className="upload-form-title">VU Resume Analyzer</h2>
        </div>

        <p className="upload-form-instruction">
          Upload your resume as a <strong>PDF</strong>. Our AI will analyze it
          and provide structured feedback to improve your chances!
        </p>

        {/* Drag & Drop Area */}
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

        {/* File Details */}
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

        {/* Error */}
        {error && <p className="upload-error-message">⚠ {error}</p>}

        {/* Submit */}
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
    </div>
  );
}

export default UploadResumeForm;
