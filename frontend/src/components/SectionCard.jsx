// SectionCard.jsx
import React from "react";

const SectionCard = ({
  title,
  contentObj,
  qualityScore,
  suggestions,
  icon,
}) => {
  // Calculate score color based on value
  const getScoreColor = (score) => {
    if (score >= 90) return "#059669"; // green - excellent
    if (score >= 70) return "#2563eb"; // blue - good
    if (score >= 50) return "#d97706"; // amber - average
    if (score >= 30) return "#ea580c"; // orange - below average
    return "#dc2626"; // red - poor
  };

  // Render content based on type
  const renderContent = (content) => {
    if (!content) return <i>No content available.</i>;

    // Array → render as bullet list
    if (Array.isArray(content)) {
      return (
        <ul className="content-list">
          {content.map((item, idx) => (
            <li key={idx} className="content-list-item">
              {renderContent(item)}
            </li>
          ))}
        </ul>
      );
    }

    // Object → render as definition list
    if (typeof content === "object") {
      return (
        <dl className="content-dl">
          {Object.entries(content).map(([key, value]) => (
            <div key={key} className="content-dl-item">
              <strong className="content-dl-key">
                {key.replace(/_/g, " ")}:{" "}
              </strong>
              {renderContent(value)}
            </div>
          ))}
        </dl>
      );
    }

    // Boolean → render as Yes/No
    if (typeof content === "boolean") {
      return <span>{content ? "Yes" : "No"}</span>;
    }

    // String / number → plain span
    return <span>{String(content)}</span>;
  };

  // Process suggestions to avoid duplicates
  const processSuggestions = (suggestions) => {
    if (!suggestions) return null;

    // If it's an array, remove duplicates
    if (Array.isArray(suggestions)) {
      const uniqueSuggestions = [...new Set(suggestions)];
      return uniqueSuggestions;
    }

    // If it's a string, split into sentences and remove duplicates
    if (typeof suggestions === "string") {
      const sentences = suggestions
        .split(/(?<=[.!?])\s+/)
        .map((s) => s.trim())
        .filter((s) => s);
      const uniqueSentences = [...new Set(sentences)];
      return uniqueSentences;
    }

    return suggestions;
  };

  const processedSuggestions = processSuggestions(suggestions);

  return (
    <div className="section-card">
      {/* Title Bar */}
      <div className="section-card-header">
        <div className="section-card-title-container">
          <div className="section-card-title-wrapper">
            {icon && <span className="section-card-icon">{icon}</span>}
            <h2 className="section-card-title">{title}</h2>
          </div>
          {qualityScore !== undefined && (
            <div
              className="section-card-score"
              style={{ backgroundColor: getScoreColor(qualityScore) }}
            >
              {qualityScore}%
            </div>
          )}
        </div>
      </div>

      <div className="section-card-content">
        {/* Main extracted content */}
        {contentObj && Object.keys(contentObj).length > 0 && (
          <div className="section-card-details">
            <h3 className="section-card-subtitle">Analysis Details:</h3>
            <div className="section-card-content-box">
              {renderContent(contentObj)}
            </div>
          </div>
        )}

        {/* Show message if no content and no suggestions */}
        {(!contentObj || Object.keys(contentObj).length === 0) &&
          !processedSuggestions && (
            <div className="section-card-empty">
              No analysis data available for this section
            </div>
          )}

        {/* Suggestions */}
        {processedSuggestions && (
          <div className="section-card-suggestions">
            <h3 className="section-card-suggestions-title">
              <span className="section-card-suggestions-icon">
                <i className="bi bi-lightbulb"></i>
              </span>{" "}
              Suggestions
            </h3>
            {Array.isArray(processedSuggestions) ? (
              <ul className="suggestions-list">
                {processedSuggestions.map((suggestion, idx) => (
                  <li key={idx} className="suggestions-list-item">
                    {suggestion}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="suggestions-text">{processedSuggestions}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(SectionCard);
