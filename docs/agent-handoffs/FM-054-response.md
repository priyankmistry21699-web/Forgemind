# FM-054 — SSE Streaming (Real-Time Event Pub/Sub)

## What was done

Built an in-memory asyncio.Queue-based pub/sub system for real-time Server-Sent Events (SSE). Supports both run-scoped and global event subscriptions with automatic heartbeats and graceful overflow handling.

## Files created

- `apps/api/app/services/stream_service.py` — Stream service:
  - In-memory registry: `_subscribers[run_id]` → list of asyncio.Queues, `_global_subscribers` → list
  - `subscribe_run(run_id)` / `unsubscribe_run(run_id, queue)`: Per-run subscription management
  - `subscribe_global()` / `unsubscribe_global(queue)`: Global subscription management
  - `publish_run_event(run_id, event_type, data)`: Publishes to run subscribers + global subscribers, returns subscriber count
  - `run_event_generator(run_id)`: Async generator yielding SSE frames for a specific run
  - `global_event_generator()`: Async generator yielding SSE frames for all events
- `apps/api/app/api/routes/streaming.py` — Routes:
  - `GET /runs/{run_id}/stream`: Run-scoped SSE endpoint (StreamingResponse)
  - `GET /stream/events`: Global SSE endpoint (StreamingResponse)

## Files modified

- `apps/api/app/api/router.py` — Registered `streaming_router`

## Design decisions

- In-memory asyncio.Queue (no persistence) — fire-and-forget delivery model
- Run-scoped + global subscriptions for flexible consumption patterns
- Heartbeat every 15 seconds keeps connections alive through proxies/load balancers
- QueueFull (queue size 100) is logged but non-fatal — events are dropped gracefully
- Payload format: `{run_id, event_type, data}` for consistent SSE parsing
