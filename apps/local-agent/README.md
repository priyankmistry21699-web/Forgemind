# ForgeMind Local Agent

> Lightweight local OS companion for ForgeMind.

## Overview

A Python CLI that runs on the developer's machine and provides:

- Scoped folder access (read/write with approval gates)
- Local command execution (build, test, lint)
- Repository inspection and file import
- Environment analysis (dependencies, runtime versions)
- WebSocket sync with ForgeMind cloud
- File watching for local changes
- Hybrid local-cloud workflows

## Tech Stack

- **Python 3.12** with **Typer** (CLI framework)
- **WebSocket client** for cloud communication
- **watchdog** for file watching
- **Docker SDK** for sandboxed local tasks

## Development

```bash
cd apps/local-agent
pip install -r requirements.txt
python -m local_agent --help
```

## Security

- All file operations are scoped to explicitly allowed directories
- Destructive commands require user approval
- No secrets are stored locally in plaintext
