import React, { useState } from "react";
import UploadResumeForm from "./components/UploadResumeForm";
import SectionCard from "./components/SectionCard";

function App() {
  const [analysisData, setAnalysisData] = useState(null);

  const handleUploadSuccess = (data) => {
    setAnalysisData(data);
  };

  return (
    <div style={{ padding: "20px", maxWidth: "900px", margin: "0 auto" }}>
      {!analysisData ? (
        <UploadResumeForm onUploadSuccess={handleUploadSuccess} />
      ) : (
        analysisData.sections.map((section, index) => (
          <SectionCard
            key={index}
            title={section.title}
            contentObj={section.content}
            qualityScore={section.qualityScore}
            suggestions={section.suggestions}
            isLast={index === analysisData.sections.length - 1}
          />
        ))
      )}
    </div>
  );
}

export default App;
