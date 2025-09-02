// ResumeAnalysisResults.jsx
import React from "react";
import SectionCard from "./SectionCard";

const ResumeAnalysisResults = ({ analysisData }) => {
  if (!analysisData) {
    return (
      <div style={{ textAlign: "center", padding: "40px", color: "#6c757d" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>📄</div>
        <h3>No analysis data available</h3>
        <p>Upload a resume to see the analysis results.</p>
      </div>
    );
  }

  // Check if there's an error in the analysis response
  if (analysisData.status === "error" || analysisData.analysis?.error) {
    return (
      <div style={{ textAlign: "center", padding: "40px", color: "#dc3545", backgroundColor: "white", borderRadius: "12px", border: "1px solid #f5c2c7" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
        <h3>Analysis Error</h3>
        <p>{analysisData.analysis?.error || "An error occurred during analysis"}</p>
        {analysisData.analysis?.raw_output && (
          <details style={{ marginTop: "16px", textAlign: "left" }}>
            <summary style={{ cursor: "pointer", color: "#6c757d" }}>Show raw output</summary>
            <pre style={{ fontSize: "12px", backgroundColor: "#f8f9fa", padding: "10px", borderRadius: "4px", overflow: "auto" }}>
              {analysisData.analysis.raw_output}
            </pre>
          </details>
        )}
      </div>
    );
  }

  // Get the analysis object from the response
  const analysis = analysisData.analysis;

  // Extract sections from the analysis data
  const sections = [
    {
      title: "Basic Information",
      contentObj: {},
      qualityScore: analysis.basic_info?.quality_score,
      suggestions: analysis.basic_info?.suggestions,
    },
    {
      title: "Professional Summary",
      contentObj: {},
      qualityScore: analysis.professional_summary?.quality_score,
      suggestions: analysis.professional_summary?.suggestions,
    },
    {
      title: "Education",
      contentObj: {},
      qualityScore: analysis.education?.quality_score,
      suggestions: analysis.education?.suggestions,
    },
    {
      title: "Work Experience",
      contentObj: {},
      qualityScore: analysis.work_experience?.quality_score,
      suggestions: analysis.work_experience?.suggestions,
    },
    {
      title: "Skills",
      contentObj: {},
      qualityScore: analysis.skills?.quality_score,
      suggestions: analysis.skills?.suggestions,
    },
    {
      title: "Projects",
      contentObj: {},
      qualityScore: analysis.projects?.quality_score,
      suggestions: analysis.projects?.suggestions,
    },
    {
      title: "Certifications",
      contentObj: {},
      qualityScore: analysis.certifications?.quality_score,
      suggestions: analysis.certifications?.suggestions,
    },
    {
      title: "Extracurricular Activities",
      contentObj: {},
      qualityScore: analysis.extracurriculars?.quality_score,
      suggestions: analysis.extracurriculars?.suggestions,
    },
    {
      title: "Links Found",
      contentObj: analysis.links_found || {},
      suggestions: analysis.links_found?.link_suggestions,
    },
    {
      title: "Formatting Issues",
      contentObj: analysis.formatting_issues || {},
      suggestions: analysis.formatting_issues?.other_formatting_issues,
    },
  ];

  // Filter out sections that don't have meaningful data
  const validSections = sections.filter(section => 
    section.qualityScore !== undefined || 
    section.suggestions || 
    (section.contentObj && Object.keys(section.contentObj).length > 0)
  );

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "20px" }}>
      {/* Overall Score Header */}
      <div
        style={{
          textAlign: "center",
          marginBottom: "32px",
          padding: "24px",
          backgroundColor: "#f8f9fa",
          borderRadius: "12px",
          border: "1px solid #e9ecef",
        }}
      >
        <h2 style={{ margin: "0 0 12px 0", color: "#2d3748" }}>
          Resume Analysis Results
        </h2>
        <div
          style={{
            display: "inline-block",
            backgroundColor: "#004aad",
            color: "white",
            padding: "8px 20px",
            borderRadius: "24px",
            fontSize: "18px",
            fontWeight: "600",
            marginBottom: "12px",
          }}
        >
          Overall Score: {analysis.overall_score || 0}%
        </div>
        {analysis.overall_suggestions && (
          <div
            style={{
              marginTop: "16px",
              padding: "16px",
              backgroundColor: "#e8f4f8",
              border: "1px solid #bee5eb",
              borderRadius: "8px",
              textAlign: "left",
            }}
          >
            <h3 style={{ margin: "0 0 8px 0", color: "#0c5460" }}>
              Overall Suggestions
            </h3>
            <p style={{ margin: 0, lineHeight: "1.5" }}>
              {analysis.overall_suggestions}
            </p>
          </div>
        )}
        
        {/* Display extracted text preview if available */}
        {analysisData.extracted_text_preview && (
          <div
            style={{
              marginTop: "16px",
              padding: "16px",
              backgroundColor: "#f8f9fa",
              border: "1px solid #dee2e6",
              borderRadius: "8px",
              textAlign: "left",
            }}
          >
            <h3 style={{ margin: "0 0 8px 0", color: "#495057" }}>
              Extracted Text Preview
            </h3>
            <pre style={{ 
              margin: 0, 
              lineHeight: "1.4", 
              fontSize: "12px", 
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              maxHeight: "150px",
              overflow: "auto",
              fontFamily: "Monaco, 'Courier New', monospace"
            }}>
              {analysisData.extracted_text_preview}
            </pre>
          </div>
        )}
      </div>

      {/* Sections */}
      <div>
        {validSections.map((section, index) => (
          <SectionCard
            key={index}
            title={section.title}
            contentObj={section.contentObj}
            qualityScore={section.qualityScore}
            suggestions={section.suggestions}
            isLast={index === validSections.length - 1}
          />
        ))}
      </div>
    </div>
  );
};

export default ResumeAnalysisResults;
