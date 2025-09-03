// renderContent.js
import React from "react";
import "./renderContent.css";

export function renderContent(content, depth = 0, maxDepth = 5) {
  if (!content) return <i>No content available.</i>;

  // Prevent infinite recursion
  if (depth > maxDepth) return <span>Content too nested</span>;

  // Array → bullet list
  if (Array.isArray(content)) {
    return (
      <ul className="rc-list">
        {content.map((item, idx) => (
          <li key={idx}>{renderContent(item, depth + 1, maxDepth)}</li>
        ))}
      </ul>
    );
  }

  // Object → definition-style block
  if (typeof content === "object") {
    const filteredEntries = Object.entries(content).filter(
      ([key]) => !["quality_score", "suggestions"].includes(key)
    );

    if (filteredEntries.length === 0) {
      return <i>No content details available.</i>;
    }

    return (
      <dl className="rc-definition">
        {filteredEntries.map(([key, value]) => (
          <div key={key} className="rc-definition-item">
            <strong className="rc-key">{key.replace(/_/g, " ")}:</strong>
            {renderContent(value, depth + 1, maxDepth)}
          </div>
        ))}
      </dl>
    );
  }

  // Boolean → Yes/No
  if (typeof content === "boolean") {
    return <span>{content ? "Yes" : "No"}</span>;
  }

  // String / Number → plain text
  return <span className="rc-text">{String(content)}</span>;
}
