"""Embedding service — vector-based semantic search infrastructure.

FM-162: Semantic Search with Embeddings
- Generate embeddings for indexed content via configurable provider (litellm)
- Store embedding vectors in SearchEmbedding table
- Cosine similarity for vector-based semantic search
- Hybrid ranking: alpha * text_score + (1-alpha) * semantic_score
"""

import math
import uuid
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_knowledge import SearchIndex, SearchEmbedding, SearchEntityType

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_DIMENSIONS = 256

# Pluggable embedding function signature: (text, model, dimensions) -> list[float]
EmbeddingFn = Callable[[str, str, int], Awaitable[list[float]]]


# ── Vector Math ──────────────────────────────────────────────────


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two embedding vectors.

    Returns a value in [-1, 1] where 1 means identical direction,
    0 means orthogonal, -1 means opposite direction.
    """
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


# ── Embedding Generation ────────────────────────────────────────


async def generate_embedding(
    text: str,
    *,
    model: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    embedding_fn: EmbeddingFn | None = None,
) -> list[float]:
    """Generate an embedding vector for text.

    Uses litellm.aembedding() by default for provider-agnostic embedding
    generation (OpenAI, Cohere, HuggingFace, etc.).
    Pass embedding_fn for testing or custom providers.

    Returns a list of floats (the embedding vector).
    """
    if not text or not text.strip():
        return [0.0] * dimensions

    if embedding_fn is not None:
        return await embedding_fn(text, model, dimensions)

    # Production path: use litellm for real embeddings
    import litellm

    response = await litellm.aembedding(
        model=model,
        input=[text[:8000]],  # Truncate to typical model token limit
        dimensions=dimensions,
    )
    return response.data[0]["embedding"]


# ── Storage ──────────────────────────────────────────────────────


async def store_embedding(
    db: AsyncSession,
    *,
    search_index_id: uuid.UUID,
    embedding: list[float],
    model_name: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
) -> SearchEmbedding:
    """Store or update an embedding vector for a search index entry."""
    result = await db.execute(
        select(SearchEmbedding).where(
            SearchEmbedding.search_index_id == search_index_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.embedding = embedding
        existing.model_name = model_name
        existing.dimensions = dimensions
        await db.flush()
        return existing

    entry = SearchEmbedding(
        search_index_id=search_index_id,
        embedding=embedding,
        model_name=model_name,
        dimensions=dimensions,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_embedding(
    db: AsyncSession,
    search_index_id: uuid.UUID,
) -> SearchEmbedding | None:
    """Get the embedding for a search index entry."""
    result = await db.execute(
        select(SearchEmbedding).where(
            SearchEmbedding.search_index_id == search_index_id,
        )
    )
    return result.scalar_one_or_none()


async def generate_and_store(
    db: AsyncSession,
    *,
    search_index_id: uuid.UUID,
    title: str,
    body: str,
    model: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    embedding_fn: EmbeddingFn | None = None,
) -> SearchEmbedding | None:
    """Generate an embedding for text content and store it.

    Combines title and body for embedding generation.
    Returns the stored embedding, or None if generation fails.
    """
    text = f"{title} {body}".strip()
    if not text:
        return None

    try:
        vector = await generate_embedding(
            text,
            model=model,
            dimensions=dimensions,
            embedding_fn=embedding_fn,
        )
        return await store_embedding(
            db,
            search_index_id=search_index_id,
            embedding=vector,
            model_name=model,
            dimensions=dimensions,
        )
    except Exception as exc:
        logger.warning(
            "Embedding generation failed for index %s: %s",
            search_index_id,
            exc,
        )
        return None


async def batch_generate_embeddings(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    model: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    embedding_fn: EmbeddingFn | None = None,
) -> dict:
    """Generate embeddings for all search index entries that don't have one.

    Optionally scoped to a project. Returns stats dict.
    """
    # Find entries without embeddings
    query = (
        select(SearchIndex)
        .outerjoin(
            SearchEmbedding,
            SearchEmbedding.search_index_id == SearchIndex.id,
        )
        .where(SearchEmbedding.id.is_(None))
    )
    if project_id:
        query = query.where(SearchIndex.project_id == project_id)

    result = await db.execute(query)
    entries = list(result.scalars().all())

    generated = 0
    failed = 0
    for entry in entries:
        emb = await generate_and_store(
            db,
            search_index_id=entry.id,
            title=entry.title or "",
            body=entry.body or "",
            model=model,
            dimensions=dimensions,
            embedding_fn=embedding_fn,
        )
        if emb:
            generated += 1
        else:
            failed += 1

    return {"total": len(entries), "generated": generated, "failed": failed}


# ── Semantic Search ──────────────────────────────────────────────


async def semantic_search(
    db: AsyncSession,
    *,
    query: str,
    project_id: uuid.UUID | None = None,
    entity_types: list[SearchEntityType] | None = None,
    limit: int = 20,
    model: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    embedding_fn: EmbeddingFn | None = None,
) -> list[dict]:
    """Pure vector-based semantic search.

    Generates an embedding for the query, then ranks all indexed entries
    by cosine similarity to the query embedding.

    Returns results sorted by semantic_score descending.
    """
    query_vector = await generate_embedding(
        query,
        model=model,
        dimensions=dimensions,
        embedding_fn=embedding_fn,
    )

    # Fetch embeddings (optionally scoped)
    emb_query = select(SearchEmbedding, SearchIndex).join(
        SearchIndex, SearchIndex.id == SearchEmbedding.search_index_id
    )
    if project_id:
        emb_query = emb_query.where(SearchIndex.project_id == project_id)
    if entity_types:
        emb_query = emb_query.where(SearchIndex.entity_type.in_(entity_types))

    result = await db.execute(emb_query)
    rows = result.all()

    # Score by cosine similarity
    scored = []
    for emb, idx in rows:
        sim = cosine_similarity(query_vector, emb.embedding)
        if sim > 0.0:
            scored.append((idx, sim))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "entity_type": idx.entity_type.value,
            "entity_id": str(idx.entity_id),
            "project_id": str(idx.project_id) if idx.project_id else None,
            "title": idx.title,
            "snippet": (idx.body or "")[:200],
            "semantic_score": round(sim, 4),
        }
        for idx, sim in scored[:limit]
    ]


# ── Hybrid Search ────────────────────────────────────────────────


async def hybrid_search(
    db: AsyncSession,
    *,
    query: str,
    project_id: uuid.UUID | None = None,
    entity_types: list[SearchEntityType] | None = None,
    alpha: float = 0.5,
    limit: int = 20,
    model: str = DEFAULT_MODEL,
    dimensions: int = DEFAULT_DIMENSIONS,
    embedding_fn: EmbeddingFn | None = None,
) -> list[dict]:
    """Hybrid search combining keyword text scores and semantic similarity.

    hybrid_score = alpha * normalized_text_score + (1 - alpha) * semantic_score

    alpha=1.0 → pure keyword search
    alpha=0.0 → pure semantic search
    alpha=0.5 → equal blend (default)

    Gracefully degrades to keyword-only when no embeddings are available.
    """
    from app.services import search_service

    # 1. Get keyword search results with text scores
    text_items, _total, _ = await search_service.search(
        db,
        query=query,
        project_id=project_id,
        entity_types=entity_types,
        limit=limit * 3,  # Over-fetch for score fusion
    )

    # Build text score lookup, normalized to [0, 1]
    text_scores: dict[str, float] = {}
    text_data: dict[str, dict] = {}
    max_text_score = 0.0
    for item in text_items:
        eid = item["entity_id"]
        text_scores[eid] = item.get("score", 0.0)
        text_data[eid] = item
        max_text_score = max(max_text_score, item.get("score", 0.0))

    if max_text_score > 0:
        for eid in text_scores:
            text_scores[eid] /= max_text_score

    # 2. Get semantic search results
    semantic_scores: dict[str, float] = {}
    semantic_data: dict[str, dict] = {}
    try:
        semantic_items = await semantic_search(
            db,
            query=query,
            project_id=project_id,
            entity_types=entity_types,
            limit=limit * 3,
            model=model,
            dimensions=dimensions,
            embedding_fn=embedding_fn,
        )
        for item in semantic_items:
            eid = item["entity_id"]
            semantic_scores[eid] = item.get("semantic_score", 0.0)
            semantic_data[eid] = item
    except Exception as exc:
        logger.warning("Semantic search failed, falling back to keyword-only: %s", exc)

    # 3. Fuse scores
    all_entity_ids = set(text_scores.keys()) | set(semantic_scores.keys())

    fused: list[dict] = []
    for eid in all_entity_ids:
        ts = text_scores.get(eid, 0.0)
        ss = semantic_scores.get(eid, 0.0)
        hybrid_score = alpha * ts + (1 - alpha) * ss

        # Get entity data from whichever source has it
        data = text_data.get(eid) or semantic_data.get(eid, {})
        fused.append(
            {
                "entity_type": data.get("entity_type", ""),
                "entity_id": eid,
                "project_id": data.get("project_id"),
                "title": data.get("title", ""),
                "snippet": data.get("snippet", ""),
                "text_score": round(ts, 4),
                "semantic_score": round(ss, 4),
                "hybrid_score": round(hybrid_score, 4),
            }
        )

    fused.sort(key=lambda x: x["hybrid_score"], reverse=True)
    return fused[:limit]


# ── Vector-Enhanced Find Similar ─────────────────────────────────


async def find_similar_by_embedding(
    db: AsyncSession,
    *,
    entity_type: SearchEntityType,
    entity_id: uuid.UUID,
    limit: int = 10,
) -> list[dict]:
    """Find similar entities using embedding cosine similarity.

    Falls back to empty list if source entity has no embedding.
    """
    # Get source entity's search index entry
    source_result = await db.execute(
        select(SearchIndex).where(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id,
        )
    )
    source = source_result.scalar_one_or_none()
    if not source:
        return []

    # Get source embedding
    source_emb = await get_embedding(db, source.id)
    if not source_emb:
        return []

    # Fetch all embeddings (exclude self)
    result = await db.execute(
        select(SearchEmbedding, SearchIndex)
        .join(SearchIndex, SearchIndex.id == SearchEmbedding.search_index_id)
        .where(SearchIndex.entity_id != entity_id)
    )
    rows = result.all()

    # Score by cosine similarity
    scored = []
    for emb, idx in rows:
        sim = cosine_similarity(source_emb.embedding, emb.embedding)
        if sim > 0.0:
            scored.append((idx, sim))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "entity_type": idx.entity_type.value,
            "entity_id": str(idx.entity_id),
            "project_id": str(idx.project_id) if idx.project_id else None,
            "title": idx.title,
            "snippet": (idx.body or "")[:200],
            "similarity_score": round(sim, 4),
        }
        for idx, sim in scored[:limit]
    ]
