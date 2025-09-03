// App.js
import React, { useState } from "react";
import UploadResumeForm from "./components/UploadResumeForm";
import ResumeAnalysisResults from "./components/ResumeAnalysisResults";
import "./App.css";

function App() {
  const [analysisData, setAnalysisData] = useState(null);

  const handleUploadSuccess = (data) => setAnalysisData(data);
  const handleReset = () => setAnalysisData(null);

  return (
    <div className="app-container">
      {!analysisData ? (
        <div className="upload-section">
          <UploadResumeForm onUploadSuccess={handleUploadSuccess} />
        </div>
      ) : (
        <div className="results-section">
          <button className="floating-back-button" onClick={handleReset}>
            <span>←</span> <span>Upload New Resume</span>
          </button>

          <div className="results-content">
            <ResumeAnalysisResults analysisData={analysisData} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
