const STATUS = {
  IDLE: "Idle",
  RECORDING: "Recording",
  ANALYZING: "Analyzing",
  COMPLETE: "Complete",
};

const CAPTURE_SOURCE = {
  TAB: "tab",
  DESKTOP: "desktop",
};

const BACKEND_BASE_URL = "http://127.0.0.1:8000";
const ANALYSIS_STATUS_URL = `${BACKEND_BASE_URL}/analysis-status`;
const SESSION_START_URL = `${BACKEND_BASE_URL}/session/start`;
const ANALYSIS_POLL_INTERVAL_MS = 2000;
const ANALYSIS_POLL_TIMEOUT_MS = 30000;

const statusText = document.getElementById("statusText");
const messageText = document.getElementById("message");
const captureSourceSelect = document.getElementById("captureSourceSelect");
const sourceHint = document.getElementById("sourceHint");
const tabField = document.getElementById("tabField");
const tabSelect = document.getElementById("tabSelect");
const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const dashboardButton = document.getElementById("dashboardButton");

let analysisCheckPromise = null;

function getCaptureSource() {
  return captureSourceSelect.value === CAPTURE_SOURCE.DESKTOP ? CAPTURE_SOURCE.DESKTOP : CAPTURE_SOURCE.TAB;
}

function requiresTabSelection() {
  return getCaptureSource() === CAPTURE_SOURCE.TAB;
}

function canStartWithCurrentSelection() {
  return !requiresTabSelection() || Boolean(tabSelect.value);
}

function setControls(status) {
  const isRecording = status === STATUS.RECORDING;
  const isAnalyzing = status === STATUS.ANALYZING;
  const isComplete = status === STATUS.COMPLETE;

  statusText.textContent = status;
  captureSourceSelect.disabled = isRecording || isAnalyzing;
  startButton.disabled = isRecording || isAnalyzing || !canStartWithCurrentSelection();
  stopButton.disabled = !isRecording;
  tabSelect.disabled = isRecording || isAnalyzing || !requiresTabSelection();
  dashboardButton.disabled = !isComplete;
}

function updateSourceField() {
  const isTabCapture = requiresTabSelection();
  tabField.hidden = !isTabCapture;
  sourceHint.textContent = isTabCapture
    ? "Captures a browser tab. Tab audio stays audible while recording."
    : "Opens the system picker so you can choose a Brave tab, Zoom window, app window, or screen. If the picker shows a Share audio option, enable it.";
  setControls(statusText.textContent || STATUS.IDLE);
}

function formatTabLabel(tab) {
  const title = tab.title?.trim() || "Untitled tab";
  const hostname = tab.url ? new URL(tab.url).hostname : "";
  const windowLabel = tab.windowId ? `Window ${tab.windowId}` : "Current window";
  const tabLabel = hostname ? `${title} (${hostname})` : title;
  return `${windowLabel}: ${tabLabel}`;
}

async function loadTabs() {
  const tabs = await chrome.tabs.query({});
  const recordableTabs = tabs.filter(
    (tab) => tab.id && tab.url && !tab.url.startsWith("chrome://") && !tab.url.startsWith("edge://")
  );

  tabSelect.innerHTML = "";

  if (recordableTabs.length === 0) {
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "No recordable tabs found";
    tabSelect.appendChild(option);
    return;
  }

  for (const tab of recordableTabs) {
    const option = document.createElement("option");
    option.value = String(tab.id);
    option.textContent = formatTabLabel(tab);
    option.selected = Boolean(tab.active);
    tabSelect.appendChild(option);
  }
}

async function updateStatus(status) {
  const response = await chrome.runtime.sendMessage({ type: "SET_STATUS", status });
  if (!response?.ok) {
    throw new Error(response?.error || "Unable to update status.");
  }
  setControls(status);
}

async function startBackendSession() {
  const response = await fetch(SESSION_START_URL, { method: "POST" });
  if (!response.ok) {
    throw new Error(`Failed to initialize backend session (${response.status}).`);
  }
}

async function requestTabStream() {
  const tabId = Number(tabSelect.value);
  if (!tabId) {
    throw new Error("Select a browser tab to record first.");
  }

  const streamId = await chrome.tabCapture.getMediaStreamId({ targetTabId: tabId });
  return {
    streamId,
    captureType: CAPTURE_SOURCE.TAB,
    shouldMonitorAudio: true,
  };
}

async function requestDesktopStream() {
  return new Promise((resolve, reject) => {
    chrome.desktopCapture.chooseDesktopMedia(["window", "screen", "tab", "audio"], (streamId, options) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
        return;
      }

      if (!streamId) {
        reject(new Error("Source selection was canceled."));
        return;
      }

      if (!options?.canRequestAudioTrack) {
        reject(new Error("The selected source is not sharing audio. Choose a source with audio enabled."));
        return;
      }

      resolve({
        streamId,
        captureType: CAPTURE_SOURCE.DESKTOP,
        shouldMonitorAudio: false,
      });
    });
  });
}

async function requestCaptureConfig() {
  if (getCaptureSource() === CAPTURE_SOURCE.DESKTOP) {
    return requestDesktopStream();
  }

  return requestTabStream();
}

async function startRecordingInBackground(captureConfig) {
  return chrome.runtime.sendMessage({
    type: "START_RECORDING",
    ...captureConfig,
  });
}

async function fetchAnalysisStatus() {
  const response = await fetch(ANALYSIS_STATUS_URL);

  if (!response.ok) {
    throw new Error(`Failed to read analysis status (${response.status}).`);
  }

  return response.json();
}

async function waitForAnalysisCompletion() {
  const startedAt = Date.now();

  while (Date.now() - startedAt < ANALYSIS_POLL_TIMEOUT_MS) {
    try {
      const status = await fetchAnalysisStatus();
      if (status.analysis_ready) {
        return status;
      }
    } catch (_error) {
      // Keep polling until timeout so the button enables only when transcript data exists.
    }

    await new Promise((resolve) => window.setTimeout(resolve, ANALYSIS_POLL_INTERVAL_MS));
  }

  return null;
}

async function ensureAnalysisCompletionStatus() {
  if (analysisCheckPromise) {
    return analysisCheckPromise;
  }

  analysisCheckPromise = (async () => {
    const analysisStatus = await waitForAnalysisCompletion();

    if (analysisStatus?.analysis_ready) {
      await updateStatus(STATUS.COMPLETE);
      messageText.textContent = "Recording and analysis are complete. You can open the dashboard now.";
      return true;
    }

    await updateStatus(STATUS.IDLE);
    messageText.textContent = "No transcript was produced within 30 seconds after recording stopped. Verify that audio sharing is enabled and the backend is reachable.";
    return false;
  })();

  try {
    return await analysisCheckPromise;
  } finally {
    analysisCheckPromise = null;
  }
}

async function startMeeting() {
  messageText.textContent = "Preparing recording session...";

  try {
    await startBackendSession();

    const captureConfig = await requestCaptureConfig();
    messageText.textContent =
      captureConfig.captureType === CAPTURE_SOURCE.DESKTOP
        ? "Starting recording from the selected window or screen..."
        : "Starting tab recording...";

    const response = await startRecordingInBackground(captureConfig);

    if (!response?.ok) {
      throw new Error(response?.error || "Failed to start recording.");
    }

    await updateStatus(STATUS.RECORDING);
    messageText.textContent =
      captureConfig.captureType === CAPTURE_SOURCE.DESKTOP
        ? "Recording started from the selected window or screen."
        : "Recording started. Browser tab audio should remain audible while it continues.";
  } catch (error) {
    await updateStatus(STATUS.IDLE);
    messageText.textContent = error.message || "Failed to start recording.";
  }
}

async function stopMeeting() {
  await updateStatus(STATUS.ANALYZING);
  messageText.textContent = "Stopping recording and waiting for transcript data...";

  const response = await chrome.runtime.sendMessage({ type: "STOP_RECORDING" });

  if (!response?.ok) {
    await updateStatus(STATUS.IDLE);
    messageText.textContent = response?.error || "Failed to stop recording.";
    return;
  }

  await ensureAnalysisCompletionStatus();
}

async function openDashboard() {
  if (statusText.textContent !== STATUS.COMPLETE) {
    messageText.textContent = "Dashboard is available only after recording and analysis are complete.";
    return;
  }

  const response = await chrome.runtime.sendMessage({ type: "OPEN_DASHBOARD" });

  if (!response?.ok) {
    messageText.textContent = response?.error || "Failed to open dashboard.";
    return;
  }

  messageText.textContent = "Dashboard opened in a new tab.";
}

startButton.addEventListener("click", startMeeting);
stopButton.addEventListener("click", stopMeeting);
dashboardButton.addEventListener("click", openDashboard);
tabSelect.addEventListener("change", () => setControls(statusText.textContent));
captureSourceSelect.addEventListener("change", updateSourceField);

async function initializePopup() {
  await loadTabs();
  updateSourceField();

  const response = await chrome.runtime.sendMessage({ type: "GET_STATUS" });
  const status = response?.status || STATUS.IDLE;

  setControls(status);

  if (!tabSelect.value && requiresTabSelection()) {
    startButton.disabled = true;
    messageText.textContent = "Open a normal browser tab or switch to Window or screen capture.";
    return;
  }

  if (status === STATUS.RECORDING) {
    messageText.textContent = "Recording is active. Stop it before changing the capture source.";
    return;
  }

  if (status === STATUS.ANALYZING) {
    messageText.textContent = "Waiting for transcript data...";
    await ensureAnalysisCompletionStatus();
    return;
  }

  if (status === STATUS.COMPLETE) {
    const analysisStatus = await fetchAnalysisStatus().catch(() => null);
    if (!analysisStatus?.analysis_ready) {
      await updateStatus(STATUS.IDLE);
      messageText.textContent = "The last session has no transcript yet. Start a new recording after confirming audio is being shared.";
      return;
    }

    messageText.textContent = "Recording and analysis are complete. You can open the dashboard now.";
    return;
  }

  messageText.textContent = "Choose a source and start recording. The dashboard opens after recording and analysis finish.";
}

initializePopup().catch((error) => {
  messageText.textContent = error.message || "Failed to initialize popup.";
  setControls(STATUS.IDLE);
});
