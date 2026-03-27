// Guard against duplicate widget injection
if (!window.__aiAssistantWidgetInjected) {
  window.__aiAssistantWidgetInjected = true;

  const BACKEND_URL = "http://localhost:8000";
  let isRecording = false;
  let isAnalyzing = false;
  let updateInterval = null;

  // Create widget container
  function createWidget() {
    const widget = document.createElement("div");
    widget.id = "ai-assistant-widget";
    widget.className = "ai-widget";
    widget.innerHTML = `
      <div class="ai-widget-header">
        <span class="ai-widget-title">AI Assistant</span>
        <div class="ai-widget-header-buttons">
          <button class="ai-widget-toggle" aria-label="Toggle widget">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 8L10 13L15 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <button class="ai-widget-close" aria-label="Close widget">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M5 5L15 15M15 5L5 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
      <div class="ai-widget-content">
        <div class="ai-widget-status" style="display: none;">
          <span class="ai-widget-status-text">Recording...</span>
        </div>
        <div class="ai-widget-controls">
          <button class="ai-widget-btn ai-widget-start" aria-label="Start recording">Start</button>
          <button class="ai-widget-btn ai-widget-stop" aria-label="Stop recording" disabled>Stop</button>
        </div>
        <div class="ai-widget-progress-container" style="display: none;">
          <svg class="ai-widget-progress-svg" width="100" height="100" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#333333" stroke-width="6"/>
            <circle class="ai-widget-progress-circle" cx="50" cy="50" r="40" fill="none" stroke="url(#progressGradient)" stroke-width="6" stroke-dasharray="251.2" stroke-dashoffset="251.2" stroke-linecap="round"/>
            <defs>
              <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#0d9488"/>
                <stop offset="100%" stop-color="#0f766e"/>
              </linearGradient>
            </defs>
          </svg>
          <div class="ai-widget-progress-text">
            <span class="ai-widget-progress-percentage">0%</span>
            <p class="ai-widget-progress-label">Analyzing...</p>
          </div>
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
    const closeBtn = widget.querySelector(".ai-widget-close");
    const startBtn = widget.querySelector(".ai-widget-start");
    const stopBtn = widget.querySelector(".ai-widget-stop");
    const content = widget.querySelector(".ai-widget-content");
    const statusDiv = widget.querySelector(".ai-widget-status");
    const progressContainer = widget.querySelector(".ai-widget-progress-container");
    const progressCircle = widget.querySelector(".ai-widget-progress-circle");
    const progressPercentage = widget.querySelector(".ai-widget-progress-percentage");
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;
    let currentProgress = 0;

    // Close widget
    closeBtn.addEventListener("click", () => {
      widget.remove();
    });

    // Toggle collapse/expand
    toggleBtn.addEventListener("click", () => {
      content.classList.toggle("ai-widget-collapsed");
      toggleBtn.classList.toggle("ai-widget-toggle-rotated");
    });

    // Drag functionality
    const header = widget.querySelector(".ai-widget-header");
    header.addEventListener("mousedown", (e) => {
      if (e.target.closest(".ai-widget-close") || e.target.closest(".ai-widget-toggle")) {
        return;
      }
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

    // Update progress bar
    function updateProgressBar(progress) {
      currentProgress = progress;
      const circumference = 2 * Math.PI * 40;
      const strokeDashoffset = circumference - (progress / 100) * circumference;
      progressCircle.style.strokeDashoffset = strokeDashoffset;
      progressPercentage.textContent = progress + "%";
    }

    // Update button states
    function updateButtonStates() {
      startBtn.disabled = isRecording || isAnalyzing;
      stopBtn.disabled = !isRecording || isAnalyzing;
      statusDiv.style.display = isRecording ? "block" : "none";
    }

    // Start recording
    startBtn.addEventListener("click", () => {
      isRecording = true;
      updateButtonStates();
    });

    // Stop recording and trigger analysis
    stopBtn.addEventListener("click", async () => {
      isRecording = false;
      isAnalyzing = true;
      updateButtonStates();
      progressContainer.style.display = "flex";
      updateProgressBar(0);

      // Show loading state
      showLoadingState();

      try {
        // Simulate progress updates
        let progress = 0;
        const progressInterval = setInterval(() => {
          if (progress < 90) {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            updateProgressBar(Math.round(progress));
          }
        }, 500);

        // Fetch analysis data
        const response = await fetch(`${BACKEND_URL}/analysis-status`);
        clearInterval(progressInterval);

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Complete progress
        updateProgressBar(100);

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

        // Hide progress and show results after a short delay
        setTimeout(() => {
          progressContainer.style.display = "none";
          highlightUpdatedContent();
          isAnalyzing = false;
          updateButtonStates();
        }, 500);
      } catch (error) {
        console.error("Error fetching analysis:", error);
        showErrorState(error.message);
        progressContainer.style.display = "none";
        isAnalyzing = false;
        updateButtonStates();
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
