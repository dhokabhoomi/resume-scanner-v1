// SectionCard.jsx
import React, { useState } from "react";

const SectionCard = ({
  title,
  contentObj,
  qualityScore,
  suggestions,
  isLast = false,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  // Calculate score color based on value
  const getScoreColor = (score) => {
    if (score >= 90) return "#4caf50";
    if (score >= 70) return "#8bc34a";
    if (score >= 50) return "#ffc107";
    if (score >= 30) return "#ff9800";
    return "#f44336";
  };

  // Render content based on type
  const renderContent = (content) => {
    if (!content) return <i>No content available.</i>;

    // Array → render as bullet list
    if (Array.isArray(content)) {
      return (
        <ul style={{ paddingLeft: "20px", margin: "6px 0" }}>
          {content.map((item, idx) => (
            <li key={idx} style={{ marginBottom: "4px" }}>
              {renderContent(item)}
            </li>
          ))}
        </ul>
      );
    }

    // Object → render as definition list
    if (typeof content === "object") {
      return (
        <dl style={{ margin: "8px 0" }}>
          {Object.entries(content).map(([key, value]) => (
            <div key={key} style={{ marginBottom: "6px" }}>
              <strong style={{ textTransform: "capitalize" }}>
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

  return (
    <div
      style={{
        border: "1px solid #e0e0e0",
        borderRadius: "12px",
        marginBottom: isLast ? "0" : "16px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
        overflow: "hidden",
        transition: "all 0.3s ease",
      }}
    >
      {/* Title Bar */}
      <div
        style={{
          padding: "16px 20px",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "#f9f9f9",
          borderBottom: isOpen ? "1px solid #eee" : "none",
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <h2
            style={{
              fontSize: "17px",
              fontWeight: "600",
              margin: 0,
              color: "#2d3748",
            }}
          >
            {title}
          </h2>
          {qualityScore !== undefined && (
            <div
              style={{
                backgroundColor: getScoreColor(qualityScore),
                color: "white",
                padding: "4px 10px",
                borderRadius: "20px",
                fontSize: "13px",
                fontWeight: "600",
              }}
            >
              {qualityScore}%
            </div>
          )}
        </div>
        <span style={{ fontSize: "14px", color: "#666" }}>
          {isOpen ? "▲" : "▼"}
        </span>
      </div>

      {isOpen && (
        <div style={{ padding: "20px" }}>
          {/* Main extracted content */}
          {contentObj && Object.keys(contentObj).length > 0 && (
            <div style={{ marginBottom: "16px" }}>
              <h3
                style={{
                  fontSize: "15px",
                  margin: "0 0 10px 0",
                  color: "#4a5568",
                }}
              >
                Analysis Details:
              </h3>
              <div
                style={{
                  backgroundColor: "#f8f9fa",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  border: "1px solid #e9ecef",
                }}
              >
                {renderContent(contentObj)}
              </div>
            </div>
          )}

          {/* Show message if no content and no suggestions */}
          {(!contentObj || Object.keys(contentObj).length === 0) && !suggestions && (
            <div style={{ 
              textAlign: "center", 
              color: "#6c757d", 
              fontStyle: "italic",
              padding: "20px 0"
            }}>
              No analysis data available for this section
            </div>
          )}

          {/* Suggestions */}
          {suggestions && (
            <div
              style={{
                marginTop: "16px",
                padding: "16px",
                backgroundColor: "#e8f4f8",
                border: "1px solid #bee5eb",
                borderRadius: "8px",
                fontSize: "14px",
              }}
            >
              <h3
                style={{
                  fontSize: "15px",
                  margin: "0 0 10px 0",
                  color: "#0c5460",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span style={{ fontSize: "18px" }}>💡</span> Suggestions
              </h3>
              {Array.isArray(suggestions) ? (
                <ul style={{ margin: "6px 0 0 0", paddingLeft: "20px" }}>
                  {suggestions.map((suggestion, idx) => (
                    <li key={idx} style={{ marginBottom: "6px" }}>
                      {suggestion}
                    </li>
                  ))}
                </ul>
              ) : (
                <div style={{ lineHeight: "1.5" }}>
                  {suggestions.split(/(?<=[.!?])\s+/).map(
                    (sentence, idx) =>
                      sentence.trim() && (
                        <div key={idx} style={{ marginBottom: "8px" }}>
                          • {sentence.trim()}
                        </div>
                      )
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SectionCard;
