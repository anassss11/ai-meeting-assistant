const STATUS = {
  IDLE: "Idle",
};

const DASHBOARD_URL = "http://localhost:5173";
const OFFSCREEN_DOCUMENT_PATH = "offscreen.html";

async function setStatus(status) {
  await chrome.storage.local.set({ recordingStatus: status });
}

async function getStatus() {
  const result = await chrome.storage.local.get("recordingStatus");
  return result.recordingStatus || STATUS.IDLE;
}

async function ensureOffscreenDocument() {
  const offscreenUrl = chrome.runtime.getURL(OFFSCREEN_DOCUMENT_PATH);
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ["OFFSCREEN_DOCUMENT"],
    documentUrls: [offscreenUrl],
  });

  if (contexts.length === 0) {
    await chrome.offscreen.createDocument({
      url: OFFSCREEN_DOCUMENT_PATH,
      reasons: ["USER_MEDIA"],
      justification: "Record meeting audio while the popup is closed.",
    });
  }
}

async function startRecording(captureConfig) {
  await ensureOffscreenDocument();

  const response = await chrome.runtime.sendMessage({
    type: "OFFSCREEN_START_RECORDING",
    ...captureConfig,
  });

  if (!response?.ok) {
    throw new Error(response?.error || "Offscreen recorder failed to start.");
  }
}

async function stopRecording() {
  await ensureOffscreenDocument();
  const response = await chrome.runtime.sendMessage({ type: "OFFSCREEN_STOP_RECORDING" });

  if (!response?.ok) {
    throw new Error(response?.error || "Offscreen recorder failed to stop.");
  }
}

async function openDashboard() {
  await chrome.tabs.create({ url: DASHBOARD_URL });
}

chrome.runtime.onInstalled.addListener(() => {
  setStatus(STATUS.IDLE);
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "GET_STATUS") {
    getStatus()
      .then((status) => sendResponse({ status }))
      .catch((error) => sendResponse({ error: error.message }));
    return true;
  }

  if (message.type === "SET_STATUS") {
    setStatus(message.status)
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "START_RECORDING") {
    startRecording({
      streamId: message.streamId,
      captureType: message.captureType,
      shouldMonitorAudio: Boolean(message.shouldMonitorAudio),
    })
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "STOP_RECORDING") {
    stopRecording()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "OPEN_DASHBOARD") {
    openDashboard()
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  return false;
});
