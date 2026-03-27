const API_BASE_URL = "http://127.0.0.1:8000";

// Fetch function with configurable timeout to handle BART AI processing times
async function fetchJson(path, timeoutMs = 5000) {
  // If timeoutMs is 0, don't set any timeout
  if (timeoutMs === 0) {
    try {
      const response = await fetch(`${API_BASE_URL}${path}`);
      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      return response.json();
    } catch (error) {
      throw error;
    }
  }

  // Original timeout logic for other endpoints
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { signal: controller.signal });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    return response.json();
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

export function fetchTranscript() {
  return fetchJson("/transcript", 10000);
}

export function fetchSummary() {
  return fetchJson("/summary", 0); // No timeout - let NVIDIA take as long as needed
}

export function fetchActionItems() {
  return fetchJson("/action-items", 0); // No timeout - same as summary
}

export function fetchDecisions() {
  return fetchJson("/decisions", 0); // No timeout - same as summary
}
