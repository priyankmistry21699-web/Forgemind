# FM-033 — Execution Chatbot Foundation

## Status: DONE

## What was implemented

### Backend

1. **`apps/api/app/services/chat_service.py`** — New chat service with:
   - `_build_run_context(db, run_id)`: Assembles text context from run, tasks (status/agent/errors), artifacts (type/content preview), approvals (status/comments), events (latest 30)
   - `chat_about_run(db, run_id, user_message)`: Builds context, calls LLM with temperature=0.3, max_tokens=1024. Falls back to rule-based stub when LLM unavailable
   - `_build_stub_response(context, question)`: Keyword matching for "block/stuck", "fail/error", "approv/pending", "artifact/output" questions
2. **`apps/api/app/api/routes/chat.py`** — `POST /runs/{run_id}/chat` endpoint with ChatRequest/ChatResponse models
3. **`apps/api/app/api/router.py`** — Mounted chat router with "chat" tag

### Frontend

4. **`apps/web/lib/chat.ts`** — `ChatMessage` interface and `sendRunChat(runId, message)` helper
5. **`apps/web/components/chat/run-chat-panel.tsx`** — Collapsible chat panel with:
   - Collapsed state: dashed-border button prompt
   - Expanded state: message history, suggestion chips, Enter-to-send, auto-scroll, "Thinking…" indicator
6. **`apps/web/app/dashboard/runs/[runId]/page.tsx`** — Integrated chat panel as "Execution Assistant" section

## Technical debt

- TD-017: Chat has no conversation memory (each message is standalone, no multi-turn context)
