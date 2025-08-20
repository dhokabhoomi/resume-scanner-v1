import React, { useState } from "react";
import { renderContent } from "../utils/renderContent";

const SectionCard = ({
  title,
  contentObj,
  completeness,
  qualityScore,
  suggestions,
}) => {
  const [isOpen, setIsOpen] = useState(true);

  const badgeColor =
    completeness?.toLowerCase() === "complete"
      ? "#d4edda"
      : completeness?.toLowerCase() === "partial" ||
        completeness?.toLowerCase() === "medium"
      ? "#fff3cd"
      : "#f8d7da";

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: "8px",
        marginBottom: "16px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 6px rgba(0,0,0,0.05)",
      }}
    >
      {/* Title Bar */}
      <div
        style={{
          padding: "12px 16px",
          cursor: "pointer",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid #eee",
          background: "#f9f9f9",
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <h2 style={{ fontSize: "16px", fontWeight: "600", margin: 0 }}>
          {title}
        </h2>
        <span style={{ fontSize: "14px", color: "#666" }}>
          {isOpen ? "▲" : "▼"}
        </span>
      </div>

      {isOpen && (
        <div style={{ padding: "12px 16px" }}>
          {/* Main extracted content */}
          <div>{renderContent(contentObj)}</div>

          {/* Completeness + Quality Row */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginTop: "12px",
              fontSize: "14px",
              alignItems: "center",
            }}
          >
            <span
              style={{
                backgroundColor: badgeColor,
                padding: "4px 10px",
                borderRadius: "12px",
                fontWeight: "500",
                textTransform: "capitalize",
              }}
            >
              {completeness}
            </span>
            <span style={{ color: "#333" }}>
              Quality: <strong>{qualityScore}/10</strong>
            </span>
          </div>

          {/* Suggestions */}
          {suggestions && (
            <div
              style={{
                marginTop: "12px",
                padding: "10px",
                backgroundColor: "#fff8e1",
                border: "1px solid #ffe58f",
                borderRadius: "6px",
                fontSize: "14px",
              }}
            >
              <strong>Suggestions:</strong>
              <ul style={{ marginTop: "6px", paddingLeft: "20px" }}>
                {suggestions
                  .split(".")
                  .map((s, idx) => s.trim() && <li key={idx}>{s.trim()}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SectionCard;
