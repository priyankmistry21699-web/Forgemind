"""FM-097 — IDE / editor workflow integration.

Generates editor configuration files (VS Code tasks, settings) so developers
can trigger ForgeMind commands directly from their editor.
"""

from __future__ import annotations

import json
import os
from typing import Any

# ── VS Code tasks ──────────────────────────────────────────────────

_VSCODE_TASKS: dict[str, Any] = {
    "version": "2.0.0",
    "tasks": [
        {
            "label": "ForgeMind: Status",
            "type": "shell",
            "command": "forgemind status",
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Index Repo",
            "type": "shell",
            "command": "forgemind attach",
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Ask Question",
            "type": "shell",
            "command": 'forgemind ask "${input:question}"',
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Explain Current File",
            "type": "shell",
            "command": 'forgemind ask --file ${relativeFile} "Explain this file"',
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Generate Patch",
            "type": "shell",
            "command": 'forgemind patch generate "${input:patchDescription}"',
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: List Patches",
            "type": "shell",
            "command": "forgemind patch list",
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Prepare PR",
            "type": "shell",
            "command": "forgemind pr prepare",
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Run Tests (safe)",
            "type": "shell",
            "command": 'forgemind exec "pytest --tb=short -q"',
            "problemMatcher": [],
            "group": "test",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Run Lint (safe)",
            "type": "shell",
            "command": 'forgemind exec "ruff check ."',
            "problemMatcher": [],
            "group": "test",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "ForgeMind: Export Snapshot",
            "type": "shell",
            "command": "forgemind snapshot export",
            "problemMatcher": [],
            "group": "none",
            "presentation": {"reveal": "always", "panel": "shared"},
        },
    ],
    "inputs": [
        {
            "id": "question",
            "description": "What would you like to ask about the codebase?",
            "type": "promptString",
        },
        {
            "id": "patchDescription",
            "description": "Describe the patch you want to generate",
            "type": "promptString",
        },
    ],
}


def setup_editor(repo_root: str, editor: str = "vscode") -> list[str]:
    """Generate editor configuration files. Returns list of created files."""
    if editor != "vscode":
        return []

    created: list[str] = []

    vscode_dir = os.path.join(repo_root, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)

    # Tasks
    tasks_path = os.path.join(vscode_dir, "tasks.json")
    if os.path.isfile(tasks_path):
        # Merge — load existing, add ForgeMind tasks if not present
        with open(tasks_path, encoding="utf-8") as fh:
            existing = json.load(fh)
        existing_labels = {t.get("label") for t in existing.get("tasks", [])}
        for task in _VSCODE_TASKS["tasks"]:
            if task["label"] not in existing_labels:
                existing.setdefault("tasks", []).append(task)
        # Add inputs if missing
        existing_inputs = {i.get("id") for i in existing.get("inputs", [])}
        for inp in _VSCODE_TASKS.get("inputs", []):
            if inp["id"] not in existing_inputs:
                existing.setdefault("inputs", []).append(inp)
        with open(tasks_path, "w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2)
    else:
        with open(tasks_path, "w", encoding="utf-8") as fh:
            json.dump(_VSCODE_TASKS, fh, indent=2)
    created.append(tasks_path)

    # Settings recommendation
    settings_path = os.path.join(vscode_dir, "settings.json")
    fm_settings = {
        "forgemind.local.enabled": True,
        "files.exclude": {
            "**/.forgemind/cache": True,
            "**/.forgemind/state/runs": True,
        },
    }
    if os.path.isfile(settings_path):
        with open(settings_path, encoding="utf-8") as fh:
            existing_settings = json.load(fh)
        for k, v in fm_settings.items():
            if k not in existing_settings:
                existing_settings[k] = v
        with open(settings_path, "w", encoding="utf-8") as fh:
            json.dump(existing_settings, fh, indent=2)
    else:
        with open(settings_path, "w", encoding="utf-8") as fh:
            json.dump(fm_settings, fh, indent=2)
    created.append(settings_path)

    return created
