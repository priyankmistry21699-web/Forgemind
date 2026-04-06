# FM-104 — Slash Command Parsing

## Summary

Implemented chat slash commands (`/fm.specify`, `/fm.plan`, `/fm.tasks`, `/fm.implement`) with regex-based parsing in `slash_command_service.py`. Commands are routed to their respective services and integrated into the chat endpoint.

## Deliverables

- `slash_command_service.py` — `parse_command(text)` regex parser, `execute_command(db, run_id, command)` dispatcher
- Command routing: `/fm.specify` → spec_service, `/fm.plan` → plan_artifact_service, `/fm.tasks` → task listing, `/fm.implement` → run start
- Frontend slash command suggestions in chat input
- Integration with chat endpoint — commands return structured `command_result` alongside reply text

## Known Gaps

- None

## Test Results

- Covered by `TestFM104_SlashCommands` (9 tests)
