export function renderContent(content) {
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

  // Object → render as definition list (cleaner than divs)
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

  // String / number → plain span
  return <span>{String(content)}</span>;
}
