const CHUNK_INTERVAL_MS = 4000;
const BACKEND_AUDIO_URL = "http://127.0.0.1:8000/audio";

let mediaRecorder = null;
let mediaStream = null;
let pendingUploads = new Set();
let stopPromise = null;
let monitorContext = null;
let monitorSourceNode = null;
let completedUploadCount = 0;
let stopError = null;
let recordedChunks = [];

async function uploadChunk(blob) {
  const extension = blob.type.includes("ogg") ? "ogg" : "webm";
  const formData = new FormData();

  formData.append("file", blob, `meeting-chunk-${Date.now()}.${extension}`);

  const response = await fetch(BACKEND_AUDIO_URL, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let backendMessage = "";

    try {
      const payload = await response.json();
      backendMessage = payload?.detail || payload?.error || "";
    } catch {
      backendMessage = await response.text();
    }

    const message = backendMessage
      ? `Backend upload failed with status ${response.status}: ${backendMessage}`
      : `Backend upload failed with status ${response.status}`;

    throw new Error(message);
  }
}

function resetRecordingState() {
  completedUploadCount = 0;
  stopError = null;
  recordedChunks = [];
}

function trackUpload(promise) {
  pendingUploads.add(promise);
  promise.finally(() => pendingUploads.delete(promise));
  return promise;
}

async function finalizePendingUploads() {
  const results = await Promise.allSettled(Array.from(pendingUploads));
  const rejected = results.find((result) => result.status === "rejected");

  if (rejected) {
    throw rejected.reason instanceof Error ? rejected.reason : new Error(String(rejected.reason));
  }

  if (completedUploadCount === 0) {
    throw new Error("No audio chunks were captured or uploaded.");
  }
}

function stopAudioMonitor() {
  if (monitorSourceNode) {
    try {
      monitorSourceNode.disconnect();
    } catch (_error) {
      // Ignore disconnect errors during teardown.
    }
    monitorSourceNode = null;
  }

  if (monitorContext) {
    const activeContext = monitorContext;
    monitorContext = null;
    activeContext.close().catch(() => undefined);
  }
}

async function startAudioMonitor(stream) {
  const audioTracks = stream.getAudioTracks();
  if (audioTracks.length === 0) {
    return;
  }

  stopAudioMonitor();
  monitorContext = new AudioContext();
  const playbackStream = new MediaStream(audioTracks);
  monitorSourceNode = monitorContext.createMediaStreamSource(playbackStream);
  monitorSourceNode.connect(monitorContext.destination);

  if (monitorContext.state === "suspended") {
    await monitorContext.resume();
  }
}

function stopActiveStream() {
  stopAudioMonitor();

  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
}

async function createAudioStream(captureConfig) {
  const mandatory = {
    chromeMediaSource: captureConfig.captureType === "desktop" ? "desktop" : "tab",
    chromeMediaSourceId: captureConfig.streamId,
  };

  return navigator.mediaDevices.getUserMedia({
    audio: { mandatory },
    video: false,
  });
}

async function startRecording(captureConfig) {
  if (mediaRecorder?.state === "recording") {
    throw new Error("Recording is already active.");
  }

  resetRecordingState();
  mediaStream = await createAudioStream(captureConfig);
  stopPromise = null;

  if (!mediaStream.getAudioTracks().length) {
    stopActiveStream();
    throw new Error("The selected source did not provide an audio track.");
  }

  if (captureConfig.shouldMonitorAudio) {
    await startAudioMonitor(mediaStream);
  }

  try {
    mediaRecorder = new MediaRecorder(mediaStream, {
      mimeType: "audio/webm;codecs=opus",
    });
  } catch (_error) {
    mediaRecorder = new MediaRecorder(mediaStream);
  }

  mediaRecorder.ondataavailable = (event) => {
    if (!event.data || event.data.size === 0) {
      return;
    }

    recordedChunks.push(event.data);
  };

  mediaRecorder.onstop = async () => {
    try {
      if (recordedChunks.length === 0) {
        throw new Error("No audio chunks were captured or uploaded.");
      }

      const mimeType = recordedChunks[0]?.type || mediaRecorder?.mimeType || "audio/webm";
      const recordingBlob = new Blob(recordedChunks, { type: mimeType });
      const uploadPromise = uploadChunk(recordingBlob).then(() => {
        completedUploadCount = 1;
      });

      trackUpload(uploadPromise);
      await finalizePendingUploads();
    } catch (error) {
      stopError = error instanceof Error ? error : new Error(String(error));
    } finally {
      recordedChunks = [];
      stopActiveStream();
      mediaRecorder = null;
      stopPromise = null;
    }
  };

  mediaRecorder.onerror = (event) => {
    console.error("MediaRecorder error", event.error);
    stopError = event.error || new Error("MediaRecorder error");
    if (mediaRecorder?.state !== "inactive") {
      mediaRecorder.stop();
    }
  };

  mediaRecorder.start(CHUNK_INTERVAL_MS);
}

async function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    if (!stopPromise) {
      stopPromise = new Promise((resolve, reject) => {
        const originalOnStop = mediaRecorder.onstop;
        mediaRecorder.onstop = async () => {
          try {
            if (originalOnStop) {
              await originalOnStop();
            }

            if (stopError) {
              reject(stopError);
              return;
            }

            resolve();
          } catch (error) {
            reject(error);
          }
        };
      });
    }

    mediaRecorder.requestData();
    mediaRecorder.stop();
    await stopPromise;
    return;
  }

  stopActiveStream();
  mediaRecorder = null;
  stopPromise = null;
  recordedChunks = [];
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "OFFSCREEN_START_RECORDING") {
    startRecording({
      streamId: message.streamId,
      captureType: message.captureType,
      shouldMonitorAudio: Boolean(message.shouldMonitorAudio),
    })
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }

  if (message.type === "OFFSCREEN_STOP_RECORDING") {
    stopRecording()
      .then(() => sendResponse({ ok: true, uploadedChunks: completedUploadCount }))
      .catch((error) => sendResponse({ ok: false, error: error.message, uploadedChunks: completedUploadCount }));
    return true;
  }

  return false;
});
