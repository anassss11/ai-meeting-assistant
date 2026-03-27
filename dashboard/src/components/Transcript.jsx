import React from "react";

function Transcript({ text }) {
  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Transcript</h2>
      <p style={bodyStyle}>{text || "No transcript available yet."}</p>
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

const bodyStyle = {
  margin: 0,
  lineHeight: 1.7,
  whiteSpace: "pre-wrap",
  color: "#334155",
  fontSize: "15px",
  maxHeight: "400px",
  overflowY: "auto",
};

export default Transcript;