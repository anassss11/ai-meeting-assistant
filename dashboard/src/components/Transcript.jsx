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
  padding: "20px",
  borderRadius: "18px",
  background: "rgba(255, 255, 255, 0.88)",
  boxShadow: "0 18px 45px rgba(15, 23, 42, 0.08)",
};

const titleStyle = {
  margin: "0 0 12px",
  fontSize: "22px",
};

const bodyStyle = {
  margin: 0,
  lineHeight: 1.6,
  whiteSpace: "pre-wrap",
};

export default Transcript;