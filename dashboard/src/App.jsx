import React, { useEffect, useState } from "react";

import { fetchActionItems, fetchDecisions, fetchSummary, fetchTranscript } from "./api";
import ActionItems from "./components/ActionItems";
import Decisions from "./components/Decisions";
import Summary from "./components/Summary";
import Transcript from "./components/Transcript";

const initialData = {
  transcript: "",
  summary: "",
  actionItems: [],
  decisions: [],
};

function App() {
  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  // Load dashboard data function
  const loadDashboard = async (showLoading) => {
    if (showLoading) {
      setLoading(true);
    }

    const errors = [];
    const recordError = (label, requestError) => {
      const message = `${label}: ${requestError instanceof Error ? requestError.message : "request failed"}`;
      errors.push(message);
      setError([...errors].join(" | "));
    };
    
    const markUpdated = () => {
      setLastUpdated(new Date().toLocaleTimeString());
    };

    const tasks = [
      fetchTranscript()
        .then((transcriptResponse) => {
          setData((current) => ({ ...current, transcript: transcriptResponse.transcript || "" }));
          markUpdated();
        })
        .catch((requestError) => recordError("transcript", requestError)),
      
      fetchActionItems()
        .then((actionItemsResponse) => {
          setData((current) => ({ 
            ...current, 
            actionItems: Array.isArray(actionItemsResponse.action_items) ? actionItemsResponse.action_items : [] 
          }));
          markUpdated();
        })
        .catch((requestError) => recordError("action-items", requestError)),
      
      fetchDecisions()
        .then((decisionsResponse) => {
          setData((current) => ({ 
            ...current, 
            decisions: Array.isArray(decisionsResponse.decisions) ? decisionsResponse.decisions : [] 
          }));
          markUpdated();
        })
        .catch((requestError) => recordError("decisions", requestError)),
      
      fetchSummary()
        .then((summaryResponse) => {
          let summaryText = summaryResponse.summary || "";
          
          // Clean summary by removing decisions and action items sections
          // (they're already handled by separate API calls)
          let cleanedSummary = summaryText.split(/Decisions:/i)[0];
          cleanedSummary = cleanedSummary.split(/Action Items:/i)[0];
          cleanedSummary = cleanedSummary.trim();
          
          setData((current) => ({ ...current, summary: cleanedSummary }));
          markUpdated();
          setSummaryLoading(false);
        })
        .catch((requestError) => {
          recordError("summary", requestError);
          setSummaryLoading(false);
        }),
    ];

    try {
      await Promise.allSettled(tasks);
      if (errors.length === 0) {
        setError("");
      }
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  // Manual refresh function for the button
  const handleRefresh = () => {
    setError(""); // Clear any previous errors
    setSummaryLoading(true); // Show summary loading state
    loadDashboard(true);
  };

  // Load data on component mount
  useEffect(() => {
    setSummaryLoading(true); // Show summary loading on initial load
    loadDashboard(true);
  }, []);

  function downloadFile(content, fileName, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  function exportTranscriptAsTxt() {
    downloadFile(data.transcript || "", "meeting-transcript.txt", "text/plain;charset=utf-8");
  }

  function escapeCsvValue(value) {
    return `"${String(value).replace(/"/g, '""')}"`;
  }

  function exportTranscriptAsCsv() {
    const exportTimestamp = new Date().toISOString();
    const transcriptLines = (data.transcript || "")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    const rows = transcriptLines.length > 0 ? transcriptLines : [""];
    const csvContent = [
      "timestamp,text",
      ...rows.map((line) => `${escapeCsvValue(exportTimestamp)},${escapeCsvValue(line)}`),
    ].join("\n");

    downloadFile(csvContent, "meeting-transcript.csv", "text/csv;charset=utf-8");
  }

  return (
    <main style={pageStyle}>
      <header style={headerStyle}>
        <div>
          <p style={eyebrowStyle}>AI Meeting Assistant</p>
          <h1 style={titleStyle}>Meeting Dashboard</h1>
          <p style={metaStyle}>Connected to `http://127.0.0.1:8000` - Using NVIDIA Qwen 3.5 AI for summaries - No timeout, will wait until complete.</p>
          <p style={metaStyle}>Last updated: {lastUpdated || "waiting for first response"}</p>
        </div>
        <div style={actionsStyle}>
          <button style={buttonStyle} type="button" onClick={handleRefresh}>
            🔄 Refresh Data
          </button>
          <button style={buttonStyle} type="button" onClick={exportTranscriptAsCsv}>
            Download transcript as CSV
          </button>
          <button style={buttonStyle} type="button" onClick={exportTranscriptAsTxt}>
            Download transcript as TXT
          </button>
        </div>
      </header>

      {loading ? <div style={infoStyle}>Loading meeting data... (NVIDIA Qwen 3.5 AI has no timeout - will wait until summary is complete)</div> : null}
      {error ? <div style={errorStyle}>Backend error: {error}</div> : null}

      <section style={gridStyle}>
        <Transcript text={data.transcript} />
        <Summary text={data.summary} loading={summaryLoading} />
        <ActionItems items={data.actionItems} />
        <Decisions items={data.decisions} />
      </section>
    </main>
  );
}

const pageStyle = {
  minHeight: "100vh",
  padding: "32px",
  background: "linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0fdfa 100%)",
  color: "#0f172a",
  fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  boxSizing: "border-box",
};

const headerStyle = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "flex-start",
  gap: "24px",
  flexWrap: "wrap",
  marginBottom: "32px",
  background: "#ffffff",
  padding: "28px",
  borderRadius: "16px",
  boxShadow: "0 10px 30px rgba(0, 0, 0, 0.08)",
};

const eyebrowStyle = {
  margin: 0,
  fontSize: "12px",
  letterSpacing: "0.12em",
  textTransform: "uppercase",
  color: "#0d9488",
  fontWeight: "700",
};

const titleStyle = {
  margin: "8px 0",
  fontSize: "36px",
  fontWeight: "700",
  background: "linear-gradient(135deg, #0d9488 0%, #0f766e 100%)",
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
};

const metaStyle = {
  margin: "6px 0",
  color: "#64748b",
  fontSize: "14px",
};

const actionsStyle = {
  display: "flex",
  gap: "12px",
  flexWrap: "wrap",
};

const buttonStyle = {
  border: 0,
  borderRadius: "12px",
  padding: "12px 18px",
  background: "linear-gradient(135deg, #0d9488 0%, #0f766e 100%)",
  color: "#ffffff",
  cursor: "pointer",
  fontSize: "14px",
  fontWeight: "600",
  transition: "all 0.3s ease",
  boxShadow: "0 4px 12px rgba(13, 148, 136, 0.2)",
};

const infoStyle = {
  marginBottom: "16px",
  padding: "16px",
  borderRadius: "12px",
  background: "#ecfdf5",
  color: "#065f46",
  border: "1px solid #a7f3d0",
  fontWeight: "500",
};

const errorStyle = {
  marginBottom: "16px",
  padding: "16px",
  borderRadius: "12px",
  background: "#fef2f2",
  color: "#991b1b",
  border: "1px solid #fecaca",
  fontWeight: "500",
};

const gridStyle = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
  gap: "20px",
};

export default App;