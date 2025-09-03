// ResumeAnalysisResults.jsx
import React from "react";
import SectionCard from "./SectionCard";
import "./ResumeAnalysisResults.css";

const ResumeAnalysisResults = ({ analysisData }) => {
  if (!analysisData) {
    return (
      <div className="analysis-results-empty">
        <div className="empty-icon">📄</div>
        <h3>No analysis data available</h3>
        <p>Upload a resume to see the analysis results.</p>
      </div>
    );
  }

  if (analysisData.status === "error" || analysisData.analysis?.error) {
    return (
      <div className="analysis-results-error">
        <div className="error-icon">⚠️</div>
        <h3>Analysis Error</h3>
        <p>
          {analysisData.analysis?.error || "An error occurred during analysis"}
        </p>
        {analysisData.analysis?.raw_output && (
          <details className="raw-output-details">
            <summary>Show raw output</summary>
            <pre className="raw-output-pre">
              {analysisData.analysis.raw_output}
            </pre>
          </details>
        )}
      </div>
    );
  }

  const analysis = analysisData.analysis;

  const keyFindingsSections = [
    {
      title: "Formatting Issues",
      contentObj: analysis.formatting_issues || {},
      suggestions: analysis.formatting_issues?.other_formatting_issues,
      icon: "⚠️",
      priority: "high",
    },
    {
      title: "Links Found",
      contentObj: analysis.links_found || {},
      suggestions: analysis.links_found?.link_suggestions,
      icon: "🔗",
      priority: "medium",
    },
  ];

  const otherSections = [
    { title: "Basic Information", section: analysis.basic_info, icon: "👤" },
    {
      title: "Professional Summary",
      section: analysis.professional_summary,
      icon: "📝",
    },
    { title: "Education", section: analysis.education, icon: "🎓" },
    { title: "Work Experience", section: analysis.work_experience, icon: "💼" },
    { title: "Skills", section: analysis.skills, icon: "⚡" },
    { title: "Projects", section: analysis.projects, icon: "🚀" },
    { title: "Certifications", section: analysis.certifications, icon: "📜" },
    {
      title: "Extracurricular Activities",
      section: analysis.extracurriculars,
      icon: "🌟",
    },
  ].map((s) => ({
    ...s,
    contentObj: s.section?.content || {},
    qualityScore: s.section?.quality_score,
    suggestions: s.section?.suggestions,
  }));

  const validKeyFindings = keyFindingsSections.filter(
    (s) => s.suggestions || Object.keys(s.contentObj).length > 0
  );
  const validOtherSections = otherSections.filter(
    (s) =>
      s.qualityScore !== undefined ||
      s.suggestions ||
      Object.keys(s.contentObj).length > 0
  );

  return (
    <div className="resume-analysis-results">
      {/* Overall Score */}
      <div className="overall-score-header">
        <h2>Resume Analysis Results</h2>
        <div className="overall-score">
          Overall Score: {analysis.overall_score || 0}%
        </div>
        {analysis.overall_suggestions && (
          <div className="overall-suggestions">
            <h3>Overall Suggestions</h3>
            <p>{analysis.overall_suggestions}</p>
          </div>
        )}
      </div>

      {/* Key Findings */}
      {validKeyFindings.length > 0 && (
        <section className="key-findings-section">
          <div className="section-header">
            <h2 className="section-title">
              <span className="section-icon">🔍</span>
              Key Findings
            </h2>
            <p className="section-subtitle">
              Critical issues that need your attention
            </p>
          </div>

          <div className="key-findings-grid">
            {validKeyFindings.map((section, idx) => (
              <div
                key={idx}
                className={`key-finding-card priority-${section.priority}`}
              >
                <div className="key-finding-header">
                  <span className="key-finding-icon">{section.icon}</span>
                  <h3 className="key-finding-title">{section.title}</h3>
                </div>

                <div className="key-finding-content">
                  {Object.keys(section.contentObj).length > 0 && (
                    <div className="key-finding-details">
                      {Object.entries(section.contentObj).map(
                        ([key, value]) => (
                          <div key={key} className="key-finding-item">
                            <span className="key-finding-label">
                              {key.replace(/_/g, " ")}:
                            </span>
                            <span className="key-finding-value">
                              {Array.isArray(value)
                                ? value.join(", ")
                                : String(value)}
                            </span>
                          </div>
                        )
                      )}
                    </div>
                  )}

                  {section.suggestions && (
                    <div className="key-finding-suggestions">
                      <h4 className="suggestions-title">
                        <span className="suggestion-icon">💡</span>
                        Recommendations
                      </h4>
                      {Array.isArray(section.suggestions) ? (
                        <ul className="key-suggestions-list">
                          {section.suggestions.map((s, i) => (
                            <li key={i} className="key-suggestion-item">
                              {s}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="key-suggestion-text">
                          {section.suggestions}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Other Sections */}
      {validOtherSections.length > 0 && (
        <section className="other-sections">
          <div className="section-header">
            <h2 className="section-title">
              <span className="section-icon">📊</span>
              Detailed Analysis
            </h2>
            <p className="section-subtitle">
              Comprehensive breakdown of your resume sections
            </p>
          </div>

          <div className="sections-grid">
            {validOtherSections.map((section, idx) => (
              <SectionCard key={idx} {...section} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
};

export default ResumeAnalysisResults;
