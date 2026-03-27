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
          <p style={loadingTextStyle}>NVIDIA Qwen 3.5 AI is generating summary... (no timeout - will wait until complete)</p>
        </div>
      ) : (
        <p style={bodyStyle}>{text || "No summary available yet."}</p>
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

const bodyStyle = {
  margin: 0,
  lineHeight: 1.7,
  color: "#334155",
  fontSize: "15px",
};

const loadingStyle = {
  display: "flex",
  alignItems: "center",
  gap: "12px",
  margin: 0,
  padding: "16px",
  background: "#ecfdf5",
  borderRadius: "12px",
};

const spinnerStyle = {
  width: "24px",
  height: "24px",
  border: "3px solid #d1fae5",
  borderTop: "3px solid #0d9488",
  borderRadius: "50%",
  animation: "spin 1s linear infinite",
  flexShrink: 0,
};

const loadingTextStyle = {
  margin: 0,
  color: "#0d9488",
  fontStyle: "italic",
  fontSize: "14px",
  fontWeight: "500",
};

export default Summary;