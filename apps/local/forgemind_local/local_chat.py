"""FM-093 — Local chat over codebase.

Answers developer questions using the local repo index, file contents,
and optional LLM integration.  Works offline with rule-based fallback.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from forgemind_local.repo_index import load_manifest


# ── Keyword / heuristic search ─────────────────────────────────────


def _search_files(
    repo_root: str, manifest: dict[str, Any], query: str
) -> list[dict[str, Any]]:
    """Find files whose path or content matches the query keywords."""
    keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) > 2]
    if not keywords:
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    for f in manifest.get("files", []):
        fpath = f["path"].lower()
        score = sum(1 for kw in keywords if kw in fpath) * 3.0

        # Optionally peek at file content for deeper matches
        full = os.path.join(repo_root, f["path"])
        if os.path.isfile(full) and f.get("lines", 0) < 2000:
            try:
                content = (
                    Path(full).read_text(encoding="utf-8", errors="ignore").lower()
                )
                score += sum(1 for kw in keywords if kw in content)
            except Exception:
                pass

        if score > 0:
            scored.append((score, f))

    scored.sort(key=lambda t: -t[0])
    return [item for _, item in scored[:10]]


def _read_file_snippet(repo_root: str, rel_path: str, max_lines: int = 60) -> str:
    full = os.path.join(repo_root, rel_path)
    if not os.path.isfile(full):
        return ""
    try:
        lines = Path(full).read_text(encoding="utf-8", errors="ignore").splitlines()
        return "\n".join(lines[:max_lines])
    except Exception:
        return ""


# ── Answer generation ──────────────────────────────────────────────

_WHERE_IS = re.compile(r"where\s+is|find|locate|which\s+file", re.I)
_EXPLAIN = re.compile(r"explain|what\s+does|how\s+does|describe", re.I)
_RISK = re.compile(r"risk|danger|concern|problem|issue", re.I)
_CHANGED = re.compile(r"changed|modified|recent|diff", re.I)


def _build_rule_answer(
    repo_root: str,
    manifest: dict[str, Any],
    question: str,
    hits: list[dict[str, Any]],
    target_file: str | None,
) -> str:
    """Rule-based answering without LLM."""
    if target_file:
        snippet = _read_file_snippet(repo_root, target_file, max_lines=80)
        if snippet:
            return (
                f"**{target_file}** ({_count_detail(manifest, target_file)})\n\n"
                f"```\n{snippet}\n```\n\n"
                "Use an LLM-enabled mode for deeper explanation."
            )
        return f"File `{target_file}` not found or empty."

    if _WHERE_IS.search(question) and hits:
        lines = [
            f"- `{h['path']}` ({h['language']}, {h['lines']} lines)" for h in hits[:8]
        ]
        return "Matching files:\n" + "\n".join(lines)

    if hits:
        top = hits[0]
        snippet = _read_file_snippet(repo_root, top["path"], max_lines=40)
        parts = [
            f"Top match: **{top['path']}** ({top['language']}, {top['lines']} lines)"
        ]
        if snippet:
            parts.append(f"```\n{snippet}\n```")
        if len(hits) > 1:
            parts.append("\nOther relevant files:")
            parts.extend(f"- `{h['path']}`" for h in hits[1:6])
        return "\n".join(parts)

    return "No relevant files found for your question. Try refining your query or indexing the repo first."


def _count_detail(manifest: dict[str, Any], rel_path: str) -> str:
    for f in manifest.get("files", []):
        if f["path"] == rel_path:
            return f"{f['language']}, {f['lines']} lines"
    return "unknown"


# ── LLM integration (optional) ─────────────────────────────────────


def _try_llm_answer(
    question: str,
    context: str,
    target_file: str | None,
) -> str | None:
    """Attempt LLM-based answer. Returns None if LLM unavailable."""
    try:
        from litellm import completion  # type: ignore[import-untyped]

        model = os.environ.get("FORGEMIND_LLM_MODEL", "gpt-4o-mini")
        system = (
            "You are ForgeMind Local, a developer workstation assistant. "
            "Answer the user's question about their codebase using the provided context. "
            "Be concise and reference specific files/lines."
        )
        user_msg = f"Question: {question}\n"
        if target_file:
            user_msg += f"Focus file: {target_file}\n"
        user_msg += f"\nCodebase context:\n{context[:8000]}"

        resp = completion(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
            temperature=0.2,
        )
        return resp.choices[0].message.content  # type: ignore[union-attr]
    except Exception:
        return None


# ── Public API ─────────────────────────────────────────────────────


def answer_question(
    repo_root: str,
    question: str,
    *,
    target_file: str | None = None,
) -> dict[str, Any]:
    """Answer a codebase question. Returns dict with 'answer' and 'citations'."""
    manifest = load_manifest(repo_root)
    if manifest is None:
        return {
            "answer": "Repo not indexed. Run `forgemind attach` first.",
            "citations": [],
        }

    hits = _search_files(repo_root, manifest, question)
    citations = [h["path"] for h in hits[:8]]

    # Build context for LLM
    context_parts: list[str] = []
    for h in hits[:5]:
        snippet = _read_file_snippet(repo_root, h["path"], max_lines=40)
        if snippet:
            context_parts.append(f"=== {h['path']} ===\n{snippet}")

    context_text = "\n\n".join(context_parts)

    # Try LLM first, fall back to rule-based
    llm_answer = _try_llm_answer(question, context_text, target_file)
    if llm_answer:
        return {"answer": llm_answer, "citations": citations}

    rule_answer = _build_rule_answer(repo_root, manifest, question, hits, target_file)
    return {"answer": rule_answer, "citations": citations}
