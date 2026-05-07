"""FM-222: Agent long-term memory service.

Provides store / recall operations for project-scoped agent memory.
Similarity search uses cosine similarity over embedded float vectors
stored as JSON arrays (no pgvector dependency — works in SQLite tests).
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_intelligence import AgentMemoryEntry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vector utilities (pure Python — no pgvector required)
# ---------------------------------------------------------------------------


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _text_to_embedding(text: str) -> list[float]:
    """Deterministic pseudo-embedding for testing (not for production use).

    In production, replace this with a real embedding call via LiteLLM
    (e.g. litellm.embedding("text-embedding-3-small", input=text)).
    """
    try:
        import litellm

        response = litellm.embedding("text-embedding-3-small", input=[text])
        return response.data[0]["embedding"]
    except Exception:
        pass
    # Fallback: deterministic bag-of-bytes hash → 64-dim vector
    import hashlib

    digest = hashlib.sha256(text.encode()).digest()
    vec = [(b / 255.0) * 2 - 1 for b in digest]
    # Normalise
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def store_memory(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    agent_type: str,
    key: str,
    value: Any,
    run_id: uuid.UUID | None = None,
    embed_text: str | None = None,
) -> AgentMemoryEntry:
    """Upsert a memory entry for a project + agent + key triple."""
    result = await db.execute(
        select(AgentMemoryEntry).where(
            AgentMemoryEntry.project_id == project_id,
            AgentMemoryEntry.agent_type == agent_type,
            AgentMemoryEntry.key == key,
        )
    )
    entry = result.scalar_one_or_none()

    embedding = None
    if embed_text:
        embedding = _text_to_embedding(embed_text)
    elif isinstance(value, str):
        embedding = _text_to_embedding(value)
    elif isinstance(value, dict):
        embedding = _text_to_embedding(json.dumps(value))

    if entry:
        entry.value_json = value if isinstance(value, dict) else {"v": value}
        entry.embedding_vector = embedding
        if run_id:
            entry.run_id = run_id
    else:
        entry = AgentMemoryEntry(
            project_id=project_id,
            agent_type=agent_type,
            key=key,
            value_json=value if isinstance(value, dict) else {"v": value},
            embedding_vector=embedding,
            run_id=run_id,
        )
        db.add(entry)

    await db.flush()
    await db.refresh(entry)
    logger.debug("agent_memory: stored key=%s project=%s agent=%s", key, project_id, agent_type)
    return entry


async def recall_memory(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    agent_type: str,
    query: str,
    top_k: int = 5,
) -> list[AgentMemoryEntry]:
    """Return top-k memory entries most similar to the query string."""
    result = await db.execute(
        select(AgentMemoryEntry).where(
            AgentMemoryEntry.project_id == project_id,
            AgentMemoryEntry.agent_type == agent_type,
        )
    )
    entries = list(result.scalars().all())
    if not entries:
        return []

    query_vec = _text_to_embedding(query)

    # Score each entry
    scored: list[tuple[float, AgentMemoryEntry]] = []
    for e in entries:
        vec = e.embedding_vector
        if vec:
            sim = _cosine_similarity(query_vec, vec)
        else:
            sim = 0.0
        scored.append((sim, e))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in scored[:top_k]]


async def list_memories(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    agent_type: str | None = None,
    limit: int = 50,
) -> list[AgentMemoryEntry]:
    """List all memory entries for a project, optionally filtered by agent type."""
    query = select(AgentMemoryEntry).where(
        AgentMemoryEntry.project_id == project_id
    )
    if agent_type:
        query = query.where(AgentMemoryEntry.agent_type == agent_type)
    query = query.order_by(AgentMemoryEntry.updated_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def delete_memory(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    agent_type: str,
    key: str,
) -> bool:
    result = await db.execute(
        select(AgentMemoryEntry).where(
            AgentMemoryEntry.project_id == project_id,
            AgentMemoryEntry.agent_type == agent_type,
            AgentMemoryEntry.key == key,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        return False
    await db.delete(entry)
    await db.flush()
    return True
