# FM-044 — Execution Chatbot v2

## What was done

Enhanced the run chatbot with topic detection, context-aware assembly, and rich stub responses. The chatbot now detects user intent (blockers, failures, retries, connectors) and builds targeted context accordingly, keeping LLM prompts focused.

## Files modified

- `apps/api/app/services/chat_service.py` — Major v2 rewrite:
  - `ChatTopic` class: Constants for `BLOCKER`, `FAILURE`, `APPROVAL`, `ARTIFACT`, `RETRY`, `CONNECTOR`, `NEXT_STEP`, `STATUS`, `GENERAL`
  - `TOPIC_KEYWORDS` mapping: Keyword lists for each topic (e.g., `RETRY → ["retry", "rerun", "again", "attempt", "revision", "redo"]`)
  - `detect_topics(message)`: Scans message for keywords, returns list of detected topics
  - `CHAT_SYSTEM_PROMPT`: Enhanced v2 prompt declaring capabilities (root cause analysis, retry guidance, artifact comparison, connector readiness)
  - `_build_run_context(db, run_id)`: Assembles text context from `run_memory_service`
  - `_build_connector_context(db, run_id)`: Fetches connector readiness states for the run's project
  - `_build_stub_response(context, question)`: Rule-based fallback with keyword detection for blocker/failure/approval/artifact/retry/connector topics
  - `chat_about_run(db, run_id, user_message)`: Detects topics, builds targeted context, calls LLM, falls back to stub

## Design decisions

- Topic detection is keyword-based (no ML) for deterministic, fast classification
- Context assembly is topic-aware: only fetches connector/retry context when the detected topic warrants it
- Enhanced system prompt explicitly lists capabilities to guide LLM responses
- Backward compatible: same `POST /runs/{run_id}/chat` endpoint, same request/response schema
