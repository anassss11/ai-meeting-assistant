import React from "react";

function Decisions({ items }) {
  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Decisions</h2>
      {items.length > 0 ? (
        <ul style={listStyle}>
          {items.map((item) => (
            <li key={item} style={itemStyle}>
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p style={emptyStyle}>No decisions available yet.</p>
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
  marginBottom: "12px",
  lineHeight: 1.6,
  padding: "12px",
  background: "#f8fafc",
  borderRadius: "12px",
  border: "1px solid #e2e8f0",
  borderLeft: "4px solid #0d9488",
  color: "#334155",
  fontSize: "15px",
};

const emptyStyle = {
  margin: 0,
  color: "#94a3b8",
  fontStyle: "italic",
};

export default Decisions;