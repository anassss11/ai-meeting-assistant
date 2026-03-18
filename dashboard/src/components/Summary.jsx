import React, { useEffect } from "react";

function Summary({ text, loading }) {
  // Inject CSS animation for spinner
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  return (
    <section style={cardStyle}>
      <h2 style={titleStyle}>Summary</h2>
      {loading ? (
        <div style={loadingStyle}>
          <div style={spinnerStyle}></div>
          <p style={loadingTextStyle}>LLaMA 3 AI is generating summary... (no timeout - will wait until complete)</p>
        </div>
      ) : (
        <p style={bodyStyle}>{text || "No summary available yet."}</p>
      )}
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
};

const loadingStyle = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  margin: 0,
};

const spinnerStyle = {
  width: "20px",
  height: "20px",
  border: "2px solid #e2e8f0",
  borderTop: "2px solid #0f766e",
  borderRadius: "50%",
  animation: "spin 1s linear infinite",
};

const loadingTextStyle = {
  margin: 0,
  color: "#0f766e",
  fontStyle: "italic",
};

export default Summary;