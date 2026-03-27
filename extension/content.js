// Guard against duplicate widget injection
if (!window.__aiAssistantWidgetInjected) {
  window.__aiAssistantWidgetInjected = true;

  const BACKEND_URL = "http://localhost:8000";
  let isRecording = false;
  let updateInterval = null;

  // Create widget container
  function createWidget() {
    const widget = document.createElement("div");
    widget.id = "ai-assistant-widget";
    widget.className = "ai-widget";
    widget.innerHTML = `
      <div class="ai-widget-header">
        <span class="ai-widget-title">AI Assistant</span>
        <button class="ai-widget-toggle" aria-label="Toggle widget">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M5 8L10 13L15 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <div class="ai-widget-content">
        <div class="ai-widget-controls">
          <button class="ai-widget-btn ai-widget-start" aria-label="Start analysis">Start</button>
          <button class="ai-widget-btn ai-widget-stop" aria-label="Stop analysis" disabled>Stop</button>
        </div>
        <div class="ai-widget-sections">
          <div class="ai-widget-section">
            <h3 class="ai-widget-section-title">Summary</h3>
            <div class="ai-widget-section-content ai-summary-content">
              <p class="ai-widget-placeholder">Click Start to analyze the meeting</p>
            </div>
          </div>
          <div class="ai-widget-section">
            <h3 class="ai-widget-section-title">Decisions</h3>
            <div class="ai-widget-section-content ai-decisions-content">
              <p class="ai-widget-placeholder">No decisions yet</p>
            </div>
          </div>
          <div class="ai-widget-section">
            <h3 class="ai-widget-section-title">Action Items</h3>
            <div class="ai-widget-section-content ai-actions-content">
              <p class="ai-widget-placeholder">No action items yet</p>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(widget);
    return widget;
  }

  // Initialize widget
  function initWidget() {
    const widget = createWidget();
    const toggleBtn = widget.querySelector(".ai-widget-toggle");
    const startBtn = widget.querySelector(".ai-widget-start");
    const stopBtn = widget.querySelector(".ai-widget-stop");
    const content = widget.querySelector(".ai-widget-content");
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    // Toggle collapse/expand
    toggleBtn.addEventListener("click", () => {
      content.classList.toggle("ai-widget-collapsed");
      toggleBtn.classList.toggle("ai-widget-toggle-rotated");
    });

    // Drag functionality
    const header = widget.querySelector(".ai-widget-header");
    header.addEventListener("mousedown", (e) => {
      isDragging = true;
      const rect = widget.getBoundingClientRect();
      offsetX = e.clientX - rect.left;
      offsetY = e.clientY - rect.top;
      widget.style.cursor = "grabbing";
    });

    document.addEventListener("mousemove", (e) => {
      if (isDragging) {
        widget.style.left = e.clientX - offsetX + "px";
        widget.style.top = e.clientY - offsetY + "px";
        widget.style.right = "auto";
        widget.style.bottom = "auto";
      }
    });

    document.addEventListener("mouseup", () => {
      isDragging = false;
      widget.style.cursor = "grab";
    });

    // Start analysis
    startBtn.addEventListener("click", async () => {
      isRecording = true;
      startBtn.disabled = true;
      stopBtn.disabled = false;

      // Show loading state
      showLoadingState();

      try {
        // Fetch analysis data
        const response = await fetch(`${BACKEND_URL}/analysis-status`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Populate widget with data
        if (data.summary) {
          populateSummary(data.summary);
        }
        if (data.decisions) {
          populateDecisions(data.decisions);
        }
        if (data.action_items) {
          populateActionItems(data.action_items);
        }

        // Highlight newly updated content
        highlightUpdatedContent();
      } catch (error) {
        console.error("Error fetching analysis:", error);
        showErrorState(error.message);
      }
    });

    // Stop analysis
    stopBtn.addEventListener("click", () => {
      isRecording = false;
      startBtn.disabled = false;
      stopBtn.disabled = true;

      if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
      }
    });
  }

  // Show loading state
  function showLoadingState() {
    const summaryContent = document.querySelector(".ai-summary-content");
    const decisionsContent = document.querySelector(".ai-decisions-content");
    const actionsContent = document.querySelector(".ai-actions-content");

    summaryContent.innerHTML = '<div class="ai-widget-loading">Analyzing...</div>';
    decisionsContent.innerHTML = '<div class="ai-widget-loading">Analyzing...</div>';
    actionsContent.innerHTML = '<div class="ai-widget-loading">Analyzing...</div>';
  }

  // Show error state
  function showErrorState(message) {
    const summaryContent = document.querySelector(".ai-summary-content");
    summaryContent.innerHTML = `<p class="ai-widget-error">Error: ${message}</p>`;
  }

  // Populate summary
  function populateSummary(summary) {
    const summaryContent = document.querySelector(".ai-summary-content");
    if (summary) {
      summaryContent.innerHTML = `<p class="ai-widget-text">${escapeHtml(summary)}</p>`;
    } else {
      summaryContent.innerHTML = '<p class="ai-widget-placeholder">No summary available</p>';
    }
  }

  // Populate decisions
  function populateDecisions(decisions) {
    const decisionsContent = document.querySelector(".ai-decisions-content");
    if (Array.isArray(decisions) && decisions.length > 0) {
      const listHtml = decisions
        .map((decision) => `<li class="ai-widget-item">${escapeHtml(decision)}</li>`)
        .join("");
      decisionsContent.innerHTML = `<ul class="ai-widget-list">${listHtml}</ul>`;
    } else {
      decisionsContent.innerHTML = '<p class="ai-widget-placeholder">No decisions yet</p>';
    }
  }

  // Populate action items
  function populateActionItems(actionItems) {
    const actionsContent = document.querySelector(".ai-actions-content");
    if (Array.isArray(actionItems) && actionItems.length > 0) {
      const listHtml = actionItems
        .map((item) => `<li class="ai-widget-item">${escapeHtml(item)}</li>`)
        .join("");
      actionsContent.innerHTML = `<ul class="ai-widget-list">${listHtml}</ul>`;
    } else {
      actionsContent.innerHTML = '<p class="ai-widget-placeholder">No action items yet</p>';
    }
  }

  // Highlight updated content
  function highlightUpdatedContent() {
    const sections = document.querySelectorAll(".ai-widget-section-content");
    sections.forEach((section) => {
      section.classList.add("ai-widget-highlight");
      setTimeout(() => {
        section.classList.remove("ai-widget-highlight");
      }, 2000);
    });
  }

  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Initialize widget when DOM is ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWidget);
  } else {
    initWidget();
  }
}
