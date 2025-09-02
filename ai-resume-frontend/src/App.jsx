import React, { useState } from "react";
import UploadResumeForm from "./components/UploadResumeForm";
import ResumeAnalysisResults from "./components/ResumeAnalysisResults";

function App() {
  const [analysisData, setAnalysisData] = useState(null);

  const handleUploadSuccess = (data) => {
    setAnalysisData(data);
  };

  const handleReset = () => {
    setAnalysisData(null);
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "#f8f9fa" }}>
      {!analysisData ? (
        <div style={{ padding: "20px", maxWidth: "900px", margin: "0 auto" }}>
          <UploadResumeForm onUploadSuccess={handleUploadSuccess} />
        </div>
      ) : (
        <div style={{ padding: "20px" }}>
          <div style={{ maxWidth: "900px", margin: "0 auto", marginBottom: "20px" }}>
            <button
              onClick={handleReset}
              style={{
                backgroundColor: "#6c757d",
                color: "white",
                border: "none",
                padding: "10px 20px",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "500",
                transition: "background-color 0.2s",
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = "#5a6268"}
              onMouseOut={(e) => e.target.style.backgroundColor = "#6c757d"}
            >
              ← Upload New Resume
            </button>
          </div>
          <ResumeAnalysisResults analysisData={analysisData} />
        </div>
      )}
    </div>
  );
}

export default App;
