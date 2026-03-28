/**
 * SSE stream client for real-time event updates.
 *
 * Provides helpers to connect to run-scoped and global SSE endpoints.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StreamEvent {
  event_type: string;
  run_id?: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/**
 * Subscribe to a run-scoped SSE stream.
 * Returns an EventSource that emits "message" events with StreamEvent payloads.
 */
export function subscribeToRun(
  runId: string,
  onEvent: (event: StreamEvent) => void,
  onError?: (error: Event) => void,
): EventSource {
  const url = `${API_BASE_URL}/runs/${runId}/stream`;
  const source = new EventSource(url);

  source.onmessage = (e) => {
    if (e.data === ":heartbeat") return;
    try {
      const parsed: StreamEvent = JSON.parse(e.data);
      onEvent(parsed);
    } catch {
      // skip malformed events
    }
  };

  if (onError) {
    source.onerror = onError;
  }

  return source;
}

/**
 * Subscribe to the global SSE stream for all events.
 */
export function subscribeToGlobal(
  onEvent: (event: StreamEvent) => void,
  onError?: (error: Event) => void,
): EventSource {
  const url = `${API_BASE_URL}/stream/events`;
  const source = new EventSource(url);

  source.onmessage = (e) => {
    if (e.data === ":heartbeat") return;
    try {
      const parsed: StreamEvent = JSON.parse(e.data);
      onEvent(parsed);
    } catch {
      // skip malformed events
    }
  };

  if (onError) {
    source.onerror = onError;
  }

  return source;
}
