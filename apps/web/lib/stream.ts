/**
 * SSE stream client with reconnection and auth support.
 *
 * Uses fetch + ReadableStream so we can attach Authorization headers
 * (native EventSource doesn't support custom headers).
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface StreamEvent {
  event_type: string;
  run_id?: string;
  data: Record<string, unknown>;
  timestamp: string;
}

export interface SSEConnection {
  /** Call to permanently close the connection (no more reconnects). */
  close: () => void;
}

// ── Internal fetch-based SSE reader ─────────────────────────────

const MAX_BACKOFF_MS = 16_000;

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("forgemind_token");
}

async function connectSSE(
  url: string,
  onEvent: (event: StreamEvent) => void,
  onStatus?: (connected: boolean) => void,
): Promise<SSEConnection> {
  let cancelled = false;
  let attempt = 0;

  async function open() {
    while (!cancelled) {
      try {
        const headers: Record<string, string> = {
          Accept: "text/event-stream",
        };
        const token = getAuthToken();
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(url, { headers, signal: undefined });
        if (!res.ok || !res.body) throw new Error(`SSE ${res.status}`);

        attempt = 0;
        onStatus?.(true);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!cancelled) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          let currentEventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              if (currentEventType === "heartbeat") {
                currentEventType = "";
                continue;
              }
              try {
                const parsed: StreamEvent = JSON.parse(line.slice(6));
                if (currentEventType) {
                  parsed.event_type = parsed.event_type || currentEventType;
                }
                onEvent(parsed);
              } catch {
                // skip malformed
              }
              currentEventType = "";
            }
          }
        }
      } catch {
        onStatus?.(false);
      }

      if (cancelled) break;
      // Exponential backoff
      const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS);
      attempt++;
      await new Promise((r) => setTimeout(r, delay));
    }
  }

  open();

  return {
    close() {
      cancelled = true;
      onStatus?.(false);
    },
  };
}

// ── Public API ──────────────────────────────────────────────────

/**
 * Subscribe to a run-scoped SSE stream with auto-reconnect.
 */
export function subscribeToRun(
  runId: string,
  onEvent: (event: StreamEvent) => void,
  onError?: (error: Event) => void,
  onStatus?: (connected: boolean) => void,
): SSEConnection {
  const url = `${API_BASE_URL}/runs/${runId}/stream`;
  // connectSSE returns a promise but we start it eagerly
  let conn: SSEConnection | null = null;
  connectSSE(url, onEvent, onStatus).then((c) => (conn = c));
  return {
    close() {
      conn?.close();
    },
  };
}

/**
 * Subscribe to the global SSE stream with auto-reconnect.
 */
export function subscribeToGlobal(
  onEvent: (event: StreamEvent) => void,
  onError?: (error: Event) => void,
  onStatus?: (connected: boolean) => void,
): SSEConnection {
  const url = `${API_BASE_URL}/stream/events`;
  let conn: SSEConnection | null = null;
  connectSSE(url, onEvent, onStatus).then((c) => (conn = c));
  return {
    close() {
      conn?.close();
    },
  };
}
