"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { subscribeToRun, subscribeToGlobal } from "@/lib/stream";
import type { StreamEvent, SSEConnection } from "@/lib/stream";

/**
 * Hook for run-scoped SSE streaming.
 * Returns live events and connection status.
 */
export function useRunStream(runId: string | null) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const connRef = useRef<SSEConnection | null>(null);
  const seenRef = useRef(new Set<string>());

  const handleEvent = useCallback((event: StreamEvent) => {
    // Deduplicate by event_type + JSON data key
    const key = `${event.event_type}:${JSON.stringify(event.data)}`;
    if (seenRef.current.has(key)) return;
    seenRef.current.add(key);
    // Cap seen set to prevent memory growth
    if (seenRef.current.size > 500) {
      const arr = [...seenRef.current];
      seenRef.current = new Set(arr.slice(-250));
    }
    setEvents((prev) => [...prev, event]);
  }, []);

  useEffect(() => {
    if (!runId) return;

    seenRef.current.clear();
    setEvents([]);

    const conn = subscribeToRun(runId, handleEvent, undefined, setConnected);
    connRef.current = conn;

    return () => {
      conn.close();
      connRef.current = null;
    };
  }, [runId, handleEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    seenRef.current.clear();
  }, []);

  return { events, connected, clearEvents };
}

/**
 * Hook for global SSE streaming.
 * Returns live events and connection status.
 */
export function useGlobalStream() {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const connRef = useRef<SSEConnection | null>(null);
  const seenRef = useRef(new Set<string>());

  const handleEvent = useCallback((event: StreamEvent) => {
    const key = `${event.event_type}:${JSON.stringify(event.data)}`;
    if (seenRef.current.has(key)) return;
    seenRef.current.add(key);
    if (seenRef.current.size > 500) {
      const arr = [...seenRef.current];
      seenRef.current = new Set(arr.slice(-250));
    }
    setEvents((prev) => [...prev, event]);
  }, []);

  useEffect(() => {
    const conn = subscribeToGlobal(handleEvent, undefined, setConnected);
    connRef.current = conn;

    return () => {
      conn.close();
      connRef.current = null;
    };
  }, [handleEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    seenRef.current.clear();
  }, []);

  return { events, connected, clearEvents };
}
