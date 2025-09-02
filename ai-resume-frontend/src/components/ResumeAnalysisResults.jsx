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

  // Check if there's an error in the analysis
  if (analysisData.error) {
    return (
      <div style={{ textAlign: "center", padding: "40px", color: "#dc3545" }}>
        <div style={{ fontSize: "48px", marginBottom: "16px" }}>⚠️</div>
        <h3>Analysis Error</h3>
        <p>{analysisData.error}</p>
      </div>
    );
  }

  // Extract sections from the analysis data
  const sections = [
    {
      title: "Basic Information",
      contentObj: analysisData.basic_info_content || {},
      qualityScore: analysisData.basic_info?.quality_score,
      suggestions: analysisData.basic_info?.suggestions,
    },
    {
      title: "Professional Summary",
      contentObj: analysisData.summary_content || {},
      qualityScore: analysisData.professional_summary?.quality_score,
      suggestions: analysisData.professional_summary?.suggestions,
    },
    {
      title: "Education",
      contentObj: analysisData.education_content || {},
      qualityScore: analysisData.education?.quality_score,
      suggestions: analysisData.education?.suggestions,
    },
    {
      title: "Work Experience",
      contentObj: analysisData.experience_content || {},
      qualityScore: analysisData.work_experience?.quality_score,
      suggestions: analysisData.work_experience?.suggestions,
    },
    {
      title: "Skills",
      contentObj: analysisData.skills_content || {},
      qualityScore: analysisData.skills?.quality_score,
      suggestions: analysisData.skills?.suggestions,
    },
    {
      title: "Projects",
      contentObj: analysisData.projects_content || {},
      qualityScore: analysisData.projects?.quality_score,
      suggestions: analysisData.projects?.suggestions,
    },
    {
      title: "Certifications",
      contentObj: analysisData.certifications_content || {},
      qualityScore: analysisData.certifications?.quality_score,
      suggestions: analysisData.certifications?.suggestions,
    },
    {
      title: "Extracurricular Activities",
      contentObj: analysisData.extracurriculars_content || {},
      qualityScore: analysisData.extracurriculars?.quality_score,
      suggestions: analysisData.extracurriculars?.suggestions,
    },
    {
      title: "Links Found",
      contentObj: analysisData.links_found || {},
      suggestions: analysisData.links_found?.link_suggestions,
    },
    {
      title: "Formatting Issues",
      contentObj: analysisData.formatting_issues || {},
      suggestions: analysisData.formatting_issues?.other_formatting_issues,
    },
  ];

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
          Overall Score: {analysisData.overall_score || 0}%
        </div>
        {analysisData.overall_suggestions && (
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
              {analysisData.overall_suggestions}
            </p>
          </div>
        )}
      </div>

      {/* Sections */}
      <div>
        {sections.map((section, index) => (
          <SectionCard
            key={index}
            title={section.title}
            contentObj={section.contentObj}
            qualityScore={section.qualityScore}
            suggestions={section.suggestions}
            isLast={index === sections.length - 1}
          />
        ))}
      </div>
    </div>
  );
};

export default ResumeAnalysisResults;
