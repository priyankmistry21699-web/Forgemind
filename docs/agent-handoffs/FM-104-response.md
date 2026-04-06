# FM-104 — Slash Command Parsing

## Goal

Parse `/fm.*` commands in chat messages and route them to the appropriate lifecycle services.

## What Was Implemented

- `slash_command_service.py` with `ParsedCommand` and `CommandResult` dataclasses
- 4 commands: `/fm.specify`, `/fm.plan`, `/fm.tasks`, `/fm.implement` (case-insensitive regex parsing)
- `parse_command(message)` → `ParsedCommand | None`
- `is_slash_command(message)` → `bool`
- `list_commands()` → autocomplete data
- `execute_command(db, run_id, parsed)` → `CommandResult` with routing to `_handle_specify`, `_handle_plan`, `_handle_tasks`, `_handle_implement`
- Chat route integration: `POST /runs/{run_id}/chat` detects and routes slash commands
- Autocomplete endpoint: `GET /chat/commands`
- Frontend `chat.ts` updated to return `command_result` alongside `reply`

## Files Changed/Added

- `apps/api/app/services/slash_command_service.py` — parser + router
- `apps/api/app/api/routes/chat.py` — slash command integration in chat endpoint
- `apps/web/lib/chat.ts` — ChatResponse includes command_result
- `apps/web/components/chat/run-chat-panel.tsx` — destructures new return type

## Test Coverage

- `TestFM104_SlashCommands` — 9 tests (parse specify/plan/tasks/implement, unknown returns none, case insensitivity, is_slash_command, list_commands)

## Result

✅ Complete — 9 tests passing
