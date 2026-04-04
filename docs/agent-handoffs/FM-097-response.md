# FM-097 — IDE Integration

## Summary

Implemented VS Code integration via `tasks.json` generation. Creates 10 ForgeMind CLI tasks with input prompts, and merges idempotently with existing editor configuration.

## Deliverables

### Service (`apps/local/forgemind_local/ide_integration.py` — 114 lines)

- **`setup_editor(repo_root)`** — generates `.vscode/tasks.json` with:
  - 10 shell tasks: init, attach, status, ask, exec, patch-generate, patch-apply, pr-prepare, snapshot-export, snapshot-import
  - 2 input prompts: question (for ask), command (for exec)
  - Tasks use `forgemind` CLI as the command
- **Idempotent merge** — removes old ForgeMind tasks (by label prefix), appends new ones; preserves non-ForgeMind tasks
- **Creates `.vscode/` directory** if it doesn't exist

### CLI

- **`forgemind ide setup`** — generates editor config, prints confirmation

## Design Notes

- VS Code only — no JetBrains, Neovim, or other editor support
- `.vscode/tasks.json` is generated on demand, not pre-seeded in repo
- Task labels prefixed with "ForgeMind:" for idempotent identification

## Tests

2 tests in `TestIDEIntegration`:

- setup_editor_creates_tasks, setup_editor_idempotent

## Test Results

- **Total**: 535 passing
