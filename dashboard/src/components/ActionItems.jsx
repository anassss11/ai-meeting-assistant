import React from "react";

function ActionItems({ items }) {
  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Action Items</h2>
      {items.length > 0 ? (
        <ol style={listStyle}>
          {items.map((item, index) => (
            <li key={`${item.task}-${index}`} style={itemStyle}>
              <p style={taskStyle}><strong>Task:</strong> {item.task}</p>
              <p style={metaStyle}><strong>Owner:</strong> {item.owner}</p>
              <p style={metaStyle}><strong>Deadline:</strong> {item.deadline}</p>
            </li>
          ))}
        </ol>
      ) : (
        <p style={emptyStyle}>No action items available yet.</p>
      )}
    </section>
  );
}

const cardStyle = {
  padding: "24px",
  borderRadius: "16px",
  background: "#ffffff",
  boxShadow: "0 10px 30px rgba(0, 0, 0, 0.08)",
  border: "1px solid #f0f9ff",
  transition: "all 0.3s ease",
};

const titleStyle = {
  margin: "0 0 16px",
  fontSize: "20px",
  fontWeight: "700",
  color: "#0d9488",
  textTransform: "uppercase",
  letterSpacing: "0.5px",
};

const listStyle = {
  margin: 0,
  paddingLeft: 0,
  listStyle: "none",
};

const itemStyle = {
  marginBottom: "16px",
  lineHeight: 1.6,
  padding: "14px",
  background: "#f8fafc",
  borderRadius: "12px",
  border: "1px solid #e2e8f0",
  borderLeft: "4px solid #0d9488",
};

const taskStyle = {
  margin: "0 0 8px",
  fontSize: "15px",
  fontWeight: "600",
  color: "#0f172a",
};

const metaStyle = {
  margin: "0 0 4px",
  color: "#64748b",
  fontSize: "14px",
};

const emptyStyle = {
  margin: 0,
  color: "#94a3b8",
  fontStyle: "italic",
};

export default ActionItems;
