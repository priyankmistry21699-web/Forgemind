# FM-096 — PR Preparation

## Summary

Implemented automated PR material generation from git diff — produces structured markdown with title, risk analysis, test checklist, and subsystem classification.

## Deliverables

### Service (`apps/local/forgemind_local/local_pr.py` — 172 lines)

- **`prepare_pr(repo_root, base_branch="main")`** — returns dict with:
  - `markdown` — complete PR description in markdown
  - `title` — auto-generated title from branch name
  - `branch` — current branch name
  - `base` — target base branch
  - `files` — list of changed files
  - `risks` — detected risk patterns
  - `checklist` — dynamic test/review checklist
  - `subsystems` — classified file categories

- **11 subsystem categories**: api, frontend, tests, config, docs, ci, docker, models, schemas, services, other
- **Risk detection patterns**: security (auth, token, secret), db migration (alembic, migration), env vars (.env), dependency changes (requirements, package.json)
- **Dynamic checklist**: items generated based on detected subsystems and risks

### CLI

- **`forgemind pr prepare`** — generates and prints PR materials; saves markdown to `.forgemind/state/pr_summary.md`

## Tests

1 test in `TestLocalPR`:
- prepare_pr (verifies dict structure, markdown content, subsystem classification)

## Test Results

- **Total**: 535 passing
