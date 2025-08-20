import React, { useState } from "react";
import UploadResumeForm from "./components/UploadResumeForm";
import SectionCard from "./components/SectionCard";

function App() {
  const [analysisData, setAnalysisData] = useState(null);

  const handleUploadSuccess = (data) => {
    setAnalysisData(data.analysis);
  };

  if (!analysisData) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: "#f2f2f2",
        }}
      >
        <UploadResumeForm onUploadSuccess={handleUploadSuccess} />
      </div>
    );
  }

  // Map sections dynamically
  const sections = [
    { title: "Basic Info", data: analysisData.basic_info, isObject: true },
    {
      title: "Professional Summary",
      data: analysisData.professional_summary,
      isObject: true,
    },
    { title: "Education", data: analysisData.education, isArray: true },
    {
      title: "Work Experience",
      data: analysisData.work_experience,
      isArray: true,
    },
    { title: "Projects", data: analysisData.projects, isArray: true },
    { title: "Skills", data: analysisData.skills, isObject: true },
    {
      title: "Certifications",
      data: analysisData.certifications,
      isArray: true,
    },
    {
      title: "Extracurriculars",
      data: analysisData.extracurriculars,
      isArray: true,
    },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "24px",
        backgroundColor: "#f2f2f2",
      }}
    >
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>
        <div
          style={{
            marginBottom: "24px",
            padding: "16px",
            backgroundColor: "#fff",
            borderRadius: "8px",
            border: "1px solid #ccc",
          }}
        >
          <h1 style={{ fontSize: "24px", fontWeight: "bold" }}>
            Resume Analysis
          </h1>
          <p>
            <strong>Overall Score:</strong> {analysisData.overall_score} / 10
          </p>
          {analysisData.overall_suggestions && (
            <p style={{ color: "#856404" }}>
              <strong>Suggestions:</strong> {analysisData.overall_suggestions}
            </p>
          )}
        </div>

        {sections.map((section) => {
          if (
            !section.data ||
            (Array.isArray(section.data) && section.data.length === 0)
          )
            return null;

          if (section.isArray) {
            return section.data.map((item, i) => (
              <SectionCard
                key={`${section.title}-${i}`}
                title={`${section.title} #${i + 1}`}
                contentObj={item}
                completeness={item.completeness}
                qualityScore={item.quality_score}
                suggestions={item.suggestions}
              />
            ));
          }

          if (section.isObject) {
            return (
              <SectionCard
                key={section.title}
                title={section.title}
                contentObj={section.data}
                completeness={section.data.completeness}
                qualityScore={section.data.quality_score}
                suggestions={section.data.suggestions}
              />
            );
          }

          return null;
        })}
      </div>
    </div>
  );
}

export default App;
