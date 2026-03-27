import React, { useEffect, useState } from "react";

function CircularProgress({ progress, isComplete }) {
  const [displayProgress, setDisplayProgress] = useState(0);

  // Animate progress value
  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayProgress((prev) => {
        if (prev < progress) {
          return Math.min(prev + 1, progress);
        }
        return prev;
      });
    }, 30);

    return () => clearInterval(interval);
  }, [progress]);

  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (displayProgress / 100) * circumference;

  return (
    <div style={containerStyle}>
      <div style={progressContainerStyle}>
        <svg width="120" height="120" style={svgStyle}>
          {/* Background circle */}
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke="#e2e8f0"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="60"
            cy="60"
            r="45"
            fill="none"
            stroke="url(#progressGradient)"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={circleStyle}
          />
          {/* Gradient definition */}
          <defs>
            <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#0d9488" />
              <stop offset="100%" stopColor="#0f766e" />
            </linearGradient>
          </defs>
        </svg>
        <div style={percentageStyle}>{displayProgress}%</div>
      </div>
      <p style={messageStyle}>
        {isComplete
          ? "Analysis complete!"
          : "Analyzing meeting data..."}
      </p>
    </div>
  );
}

const containerStyle = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  padding: "40px 20px",
  minHeight: "300px",
};

const progressContainerStyle = {
  position: "relative",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  marginBottom: "24px",
};

const svgStyle = {
  filter: "drop-shadow(0 4px 12px rgba(13, 148, 136, 0.15))",
};

const circleStyle = {
  transition: "stroke-dashoffset 0.3s ease",
  transform: "rotate(-90deg)",
  transformOrigin: "60px 60px",
};

const percentageStyle = {
  position: "absolute",
  fontSize: "28px",
  fontWeight: "700",
  color: "#0d9488",
  textAlign: "center",
};

const messageStyle = {
  margin: "0",
  fontSize: "16px",
  color: "#64748b",
  fontWeight: "500",
  textAlign: "center",
};

export default CircularProgress;
