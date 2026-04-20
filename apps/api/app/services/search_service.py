"""Search service — full-text search across all ForgeMind entities.

FM-161: Full-text search index with keyword matching, ranking, and filtering.
FM-165: Cross-project search with RBAC enforcement.

Uses a SearchIndex table for pre-computed searchable text.
Supports project-scoped and global search with entity type filtering.
"""

import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_knowledge import SearchIndex, SearchEntityType
from app.models.task import Task
from app.models.artifact import Artifact
from app.models.comment import Comment
from app.models.run import Run
from app.models.project import Project
from app.models.project_knowledge import ProjectKnowledge
from app.models.run_annotation import RunAnnotation
from app.models.approval_request import ApprovalRequest
from app.models.membership import ProjectMember

logger = logging.getLogger(__name__)


# ── Indexing ─────────────────────────────────────────────────────


async def index_task(db: AsyncSession, task: Task) -> SearchIndex:
    """Index or update a task in the search index."""
    run = None
    project_id = None
    if task.run_id:
        run_result = await db.execute(select(Run).where(Run.id == task.run_id))
        run = run_result.scalar_one_or_none()
        if run:
            project_id = run.project_id

    return await _upsert_index(
        db,
        entity_type=SearchEntityType.TASK,
        entity_id=task.id,
        project_id=project_id,
        run_id=task.run_id,
        title=task.title or "",
        body=task.description or "",
        entity_status=task.status.value if task.status else None,
        entity_meta={"task_type": task.task_type, "agent": task.assigned_agent_slug},
    )


async def index_artifact(db: AsyncSession, artifact: Artifact) -> SearchIndex:
    """Index or update an artifact in the search index."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.ARTIFACT,
        entity_id=artifact.id,
        project_id=artifact.project_id,
        run_id=artifact.run_id,
        title=artifact.title or "",
        body=(artifact.content or "")[:5000],  # Limit indexed content
        entity_status=artifact.artifact_type.value if artifact.artifact_type else None,
        entity_meta={
            "artifact_type": artifact.artifact_type.value
            if artifact.artifact_type
            else None
        },
    )


async def index_comment(db: AsyncSession, comment: Comment) -> SearchIndex:
    """Index or update a comment in the search index."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.COMMENT,
        entity_id=comment.id,
        project_id=None,
        run_id=None,
        title=f"Comment on {comment.entity_type.value if comment.entity_type else 'entity'}",
        body=comment.body or "",
        author_id=comment.author_id,
    )


async def index_run(db: AsyncSession, run: Run) -> SearchIndex:
    """Index or update a run in the search index."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.RUN,
        entity_id=run.id,
        project_id=run.project_id,
        run_id=run.id,
        title=f"Run #{run.run_number}",
        body=f"Run #{run.run_number} triggered by {run.trigger or 'manual'}",
        entity_status=run.status.value if run.status else None,
    )


async def index_project(db: AsyncSession, project: Project) -> SearchIndex:
    """Index or update a project in the search index."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.PROJECT,
        entity_id=project.id,
        project_id=project.id,
        title=project.name or "",
        body=project.description or "",
        entity_status=project.status.value if project.status else None,
        author_id=project.owner_id,
    )


async def index_knowledge(db: AsyncSession, entry: ProjectKnowledge) -> SearchIndex:
    """Index or update a knowledge entry in the search index."""
    tags_str = " ".join(entry.tags) if entry.tags else ""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.KNOWLEDGE,
        entity_id=entry.id,
        project_id=entry.project_id,
        title=entry.title or "",
        body=f"{entry.content or ''} {tags_str}",
        entity_meta={
            "knowledge_type": entry.knowledge_type.value
            if entry.knowledge_type
            else None
        },
    )


async def index_annotation(db: AsyncSession, annotation: RunAnnotation) -> SearchIndex:
    """Index or update a run annotation."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.ANNOTATION,
        entity_id=annotation.id,
        run_id=annotation.run_id,
        title=f"{annotation.annotation_type.value if annotation.annotation_type else 'note'} annotation",
        body=annotation.body or "",
        author_id=annotation.author_id,
    )


async def index_approval(db: AsyncSession, approval: ApprovalRequest) -> SearchIndex:
    """Index or update an approval request."""
    return await _upsert_index(
        db,
        entity_type=SearchEntityType.APPROVAL,
        entity_id=approval.id,
        project_id=approval.project_id,
        run_id=approval.run_id,
        title=approval.title or "Approval Request",
        body=approval.description or "",
        entity_status=approval.status.value if approval.status else None,
    )


async def _upsert_index(
    db: AsyncSession,
    *,
    entity_type: SearchEntityType,
    entity_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    title: str = "",
    body: str = "",
    entity_status: str | None = None,
    entity_meta: dict | None = None,
    author_id: uuid.UUID | None = None,
) -> SearchIndex:
    """Insert or update a search index entry."""
    result = await db.execute(
        select(SearchIndex).where(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.title = title
        existing.body = body
        existing.entity_status = entity_status
        existing.entity_meta = entity_meta
        existing.project_id = project_id
        existing.run_id = run_id
        existing.author_id = author_id
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return existing

    entry = SearchIndex(
        entity_type=entity_type,
        entity_id=entity_id,
        project_id=project_id,
        run_id=run_id,
        title=title,
        body=body,
        entity_status=entity_status,
        entity_meta=entity_meta,
        author_id=author_id,
    )
    db.add(entry)
    await db.flush()
    return entry


async def remove_from_index(
    db: AsyncSession,
    entity_type: SearchEntityType,
    entity_id: uuid.UUID,
) -> bool:
    """Remove an entity from the search index."""
    result = await db.execute(
        delete(SearchIndex).where(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id,
        )
    )
    return result.rowcount > 0


# ── Bulk Indexing ────────────────────────────────────────────────


async def reindex_project(db: AsyncSession, project_id: uuid.UUID) -> int:
    """Reindex all entities in a project. Returns count of indexed items."""
    count = 0

    # Index the project itself
    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    project = proj_result.scalar_one_or_none()
    if project:
        await index_project(db, project)
        count += 1

    # Index runs
    runs_result = await db.execute(select(Run).where(Run.project_id == project_id))
    for run in runs_result.scalars().all():
        await index_run(db, run)
        count += 1

        # Index tasks for this run
        tasks_result = await db.execute(select(Task).where(Task.run_id == run.id))
        for task in tasks_result.scalars().all():
            await index_task(db, task)
            count += 1

    # Index artifacts
    arts_result = await db.execute(
        select(Artifact).where(Artifact.project_id == project_id)
    )
    for art in arts_result.scalars().all():
        await index_artifact(db, art)
        count += 1

    # Index knowledge
    know_result = await db.execute(
        select(ProjectKnowledge).where(ProjectKnowledge.project_id == project_id)
    )
    for k in know_result.scalars().all():
        await index_knowledge(db, k)
        count += 1

    # Index approvals
    appr_result = await db.execute(
        select(ApprovalRequest).where(ApprovalRequest.project_id == project_id)
    )
    for a in appr_result.scalars().all():
        await index_approval(db, a)
        count += 1

    return count


# ── Search ───────────────────────────────────────────────────────


async def search(
    db: AsyncSession,
    *,
    query: str,
    project_id: uuid.UUID | None = None,
    entity_types: list[SearchEntityType] | None = None,
    entity_status: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = 20,
    offset: int = 0,
    user_id: uuid.UUID | None = None,
    include_facets: bool = False,
) -> tuple[list[dict], int, dict | None]:
    """Execute a search query against the index.

    Returns (results, total_count, facets).
    Each result is a dict with entity_type, entity_id, title, snippet, score.
    Facets (when requested) include counts by entity_type and status.
    """
    if not query or not query.strip():
        return [], 0, None

    terms = query.strip().lower().split()

    # Build filter conditions
    conditions = []
    for term in terms:
        term_like = f"%{term}%"
        conditions.append(
            or_(
                sa_func.lower(SearchIndex.title).like(term_like),
                sa_func.lower(SearchIndex.body).like(term_like),
            )
        )

    base_filter = and_(*conditions) if conditions else None
    if base_filter is None:
        return [], 0, None

    filters = [base_filter]

    if project_id:
        filters.append(SearchIndex.project_id == project_id)

    if entity_types:
        filters.append(SearchIndex.entity_type.in_(entity_types))

    if entity_status:
        filters.append(SearchIndex.entity_status == entity_status)

    # Date-range filtering
    if created_after:
        filters.append(SearchIndex.created_at >= created_after)
    if created_before:
        filters.append(SearchIndex.created_at <= created_before)

    # RBAC filter for cross-project search: limit to projects user is member of
    if not project_id and user_id:
        member_projects = select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id
        )
        filters.append(
            or_(
                SearchIndex.project_id.in_(member_projects),
                SearchIndex.project_id.is_(None),
            )
        )

    where_clause = and_(*filters)

    # Count
    count_q = select(sa_func.count()).select_from(
        select(SearchIndex.id).where(where_clause).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    # Score: exact title match > title contains > body contains
    # Simple scoring via CASE expressions
    results_q = (
        select(SearchIndex)
        .where(where_clause)
        .order_by(SearchIndex.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(results_q)
    rows = list(result.scalars().all())

    items = []
    for row in rows:
        # Compute simple relevance score
        score = 0.0
        title_lower = (row.title or "").lower()
        body_lower = (row.body or "").lower()
        for term in terms:
            if term in title_lower:
                score += 10.0
                if title_lower.startswith(term):
                    score += 5.0
            if term in body_lower:
                score += 1.0

        # Build snippet
        snippet = _build_snippet(row.body or "", terms, max_len=200)

        items.append(
            {
                "entity_type": row.entity_type.value,
                "entity_id": str(row.entity_id),
                "project_id": str(row.project_id) if row.project_id else None,
                "run_id": str(row.run_id) if row.run_id else None,
                "title": row.title,
                "snippet": snippet,
                "entity_status": row.entity_status,
                "score": score,
                "author_id": str(row.author_id) if row.author_id else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    # Sort by score descending
    items.sort(key=lambda x: x["score"], reverse=True)

    # Facet aggregation (counts by entity_type and status)
    facets = None
    if include_facets:
        type_facet_q = (
            select(
                SearchIndex.entity_type,
                sa_func.count().label("count"),
            )
            .where(where_clause)
            .group_by(SearchIndex.entity_type)
        )
        type_rows = (await db.execute(type_facet_q)).all()

        status_facet_q = (
            select(
                SearchIndex.entity_status,
                sa_func.count().label("count"),
            )
            .where(where_clause)
            .group_by(SearchIndex.entity_status)
        )
        status_rows = (await db.execute(status_facet_q)).all()

        facets = {
            "entity_type": {
                row.entity_type.value
                if hasattr(row.entity_type, "value")
                else str(row.entity_type): row.count
                for row in type_rows
            },
            "entity_status": {
                (row.entity_status or "unknown"): row.count for row in status_rows
            },
        }

    return items, total, facets


def _build_snippet(text: str, terms: list[str], max_len: int = 200) -> str:
    """Build a snippet around the first matching term."""
    text_lower = text.lower()
    best_pos = len(text)
    for term in terms:
        pos = text_lower.find(term)
        if pos != -1 and pos < best_pos:
            best_pos = pos

    if best_pos == len(text):
        # No match found in body, return start
        return text[:max_len] + ("..." if len(text) > max_len else "")

    start = max(0, best_pos - 40)
    end = min(len(text), start + max_len)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


# ── FM-162: Find Similar (embedding-enhanced with TF-IDF fallback) ──


async def find_similar(
    db: AsyncSession,
    *,
    entity_type: SearchEntityType,
    entity_id: uuid.UUID,
    limit: int = 10,
) -> list[dict]:
    """Find entities similar to a given entity.

    Tries embedding-based cosine similarity first (FM-162 semantic search).
    Falls back to TF-IDF weighted keyword scoring when no embeddings exist.
    """
    # Try embedding-based similarity first
    from app.services import embedding_service

    emb_results = await embedding_service.find_similar_by_embedding(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    if emb_results:
        return emb_results

    # Fallback: TF-IDF weighted keyword scoring
    return await _find_similar_tfidf(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )


async def _find_similar_tfidf(
    db: AsyncSession,
    *,
    entity_type: SearchEntityType,
    entity_id: uuid.UUID,
    limit: int = 10,
) -> list[dict]:
    """TF-IDF weighted keyword similarity (fallback when no embeddings)."""
    # Get source entity
    source_result = await db.execute(
        select(SearchIndex).where(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id,
        )
    )
    source = source_result.scalar_one_or_none()
    if not source:
        return []

    # Extract key terms from title + body
    combined = f"{source.title} {source.body}".lower()
    # Simple keyword extraction: split, filter stopwords, take significant terms
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "as",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "out",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "and",
        "but",
        "or",
        "if",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "him",
        "his",
        "she",
        "her",
        "they",
        "them",
        "their",
        "what",
        "which",
        "who",
        "whom",
    }
    words = [
        w for w in combined.split() if len(w) > 2 and w.isalpha() and w not in stopwords
    ]
    # Take up to 10 most frequent terms
    from collections import Counter

    term_counts = Counter(words)
    key_terms = [t for t, _ in term_counts.most_common(10)]

    if not key_terms:
        return []

    # ── IDF computation: count documents containing each term ──
    total_docs_r = await db.execute(select(sa_func.count()).select_from(SearchIndex))
    total_docs = max((total_docs_r.scalar_one() or 1), 1)

    import math

    term_idf: dict[str, float] = {}
    for term in key_terms:
        term_like = f"%{term}%"
        doc_count_r = await db.execute(
            select(sa_func.count())
            .select_from(SearchIndex)
            .where(
                or_(
                    sa_func.lower(SearchIndex.title).like(term_like),
                    sa_func.lower(SearchIndex.body).like(term_like),
                )
            )
        )
        doc_count = max((doc_count_r.scalar_one() or 0), 1)
        term_idf[term] = math.log(total_docs / doc_count) + 1.0

    # Search for entries matching these terms (exclude self)
    conditions = []
    for term in key_terms[:5]:  # Use top 5 for efficiency
        term_like = f"%{term}%"
        conditions.append(
            or_(
                sa_func.lower(SearchIndex.title).like(term_like),
                sa_func.lower(SearchIndex.body).like(term_like),
            )
        )

    if not conditions:
        return []

    match_filter = and_(
        or_(*conditions),
        SearchIndex.entity_id != entity_id,
    )

    result = await db.execute(
        select(SearchIndex)
        .where(match_filter)
        .limit(limit * 3)  # Fetch more for scoring
    )
    candidates = list(result.scalars().all())

    # ── TF-IDF weighted scoring ──
    max_weight = sum(term_idf.get(t, 1.0) for t in key_terms)
    scored = []
    for candidate in candidates:
        title_lower = (candidate.title or "").lower()
        body_lower = (candidate.body or "").lower()
        weighted_score = 0.0
        for t in key_terms:
            idf = term_idf.get(t, 1.0)
            if t in title_lower:
                weighted_score += idf * 3.0  # Title match worth 3×
            elif t in body_lower:
                weighted_score += idf * 1.0
        # Normalize
        similarity = weighted_score / (max_weight * 3.0) if max_weight > 0 else 0.0
        scored.append((candidate, round(similarity, 3)))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "entity_type": c.entity_type.value,
            "entity_id": str(c.entity_id),
            "project_id": str(c.project_id) if c.project_id else None,
            "title": c.title,
            "snippet": (c.body or "")[:200],
            "similarity_score": score,
        }
        for c, score in scored[:limit]
        if score > 0.05
    ]


async def search_suggestions(
    db: AsyncSession,
    *,
    query: str,
    project_id: uuid.UUID | None = None,
    limit: int = 5,
) -> list[str]:
    """Return related search term suggestions based on indexed content.

    Extracts distinctive terms from top search results to suggest
    related queries. Useful for search-as-you-type or "related searches".
    """
    if not query or not query.strip():
        return []

    # Run a quick search to get top results
    items, _total, _ = await search(
        db,
        query=query,
        project_id=project_id,
        limit=10,
    )
    if not items:
        return []

    # Collect terms from result titles that are NOT in the original query
    query_terms = set(query.lower().split())
    suggestion_counter: dict[str, int] = {}
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "and",
        "or",
        "it",
        "its",
        "this",
        "that",
        "not",
        "but",
        "run",
        "task",
    }
    for item in items:
        title_words = (item.get("title") or "").lower().split()
        for w in title_words:
            w_clean = w.strip(".,;:!?#()[]{}\"'")
            if (
                len(w_clean) > 2
                and w_clean.isalpha()
                and w_clean not in query_terms
                and w_clean not in stopwords
            ):
                suggestion_counter[w_clean] = suggestion_counter.get(w_clean, 0) + 1

    # Sort by frequency, return top N
    sorted_terms = sorted(suggestion_counter.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in sorted_terms[:limit]]


# ── Index Integrity ──────────────────────────────────────────────


async def check_index_integrity(
    db: AsyncSession,
    project_id: uuid.UUID,
) -> dict:
    """Check search index integrity for a project.

    Compares indexed entities against actual database records.
    Returns a dict with: total_indexed, orphaned (index entries with no
    matching source record), missing (source records not in index),
    entity_counts, and passed (True if no orphans or missing).
    """
    # Count indexed entries for this project
    idx_result = await db.execute(
        select(SearchIndex).where(SearchIndex.project_id == project_id)
    )
    indexed = list(idx_result.scalars().all())
    total_indexed = len(indexed)

    # Group by entity type
    indexed_by_type: dict[str, set[uuid.UUID]] = {}
    for entry in indexed:
        key = entry.entity_type.value
        indexed_by_type.setdefault(key, set()).add(entry.entity_id)

    # Get actual counts from source tables
    actual_by_type: dict[str, set[uuid.UUID]] = {}

    # Tasks (via runs)
    run_ids_result = await db.execute(
        select(Run.id).where(Run.project_id == project_id)
    )
    run_ids = [r for (r,) in run_ids_result.all()]
    if run_ids:
        task_result = await db.execute(select(Task.id).where(Task.run_id.in_(run_ids)))
        actual_by_type["task"] = {r for (r,) in task_result.all()}

    # Artifacts
    art_result = await db.execute(
        select(Artifact.id).where(Artifact.project_id == project_id)
    )
    actual_by_type["artifact"] = {r for (r,) in art_result.all()}

    # Runs
    actual_by_type["run"] = set(run_ids)

    # Project itself
    proj_result = await db.execute(select(Project.id).where(Project.id == project_id))
    proj = proj_result.scalar_one_or_none()
    actual_by_type["project"] = {proj} if proj else set()

    # Knowledge
    know_result = await db.execute(
        select(ProjectKnowledge.id).where(ProjectKnowledge.project_id == project_id)
    )
    actual_by_type["knowledge"] = {r for (r,) in know_result.all()}

    # Approvals
    appr_result = await db.execute(
        select(ApprovalRequest.id).where(ApprovalRequest.project_id == project_id)
    )
    actual_by_type["approval"] = {r for (r,) in appr_result.all()}

    # Compute orphaned and missing
    orphaned: list[dict] = []
    missing: list[dict] = []
    entity_counts: dict[str, dict] = {}

    check_types = ["task", "artifact", "run", "project", "knowledge", "approval"]
    for etype in check_types:
        idx_set = indexed_by_type.get(etype, set())
        actual_set = actual_by_type.get(etype, set())

        orph = idx_set - actual_set
        miss = actual_set - idx_set

        for eid in orph:
            orphaned.append({"entity_type": etype, "entity_id": str(eid)})
        for eid in miss:
            missing.append({"entity_type": etype, "entity_id": str(eid)})

        entity_counts[etype] = {
            "indexed": len(idx_set),
            "actual": len(actual_set),
        }

    return {
        "project_id": str(project_id),
        "total_indexed": total_indexed,
        "orphaned_count": len(orphaned),
        "missing_count": len(missing),
        "orphaned": orphaned,
        "missing": missing,
        "entity_counts": entity_counts,
        "passed": len(orphaned) == 0 and len(missing) == 0,
    }


# ── FM-165: Project Directory & Related Suggestions ──────────────


async def get_project_directory(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Browse all projects the user has access to, with health summaries (FM-165).

    Returns a list of project directory entries with overview metrics.
    """
    from app.models.run import Run as RunModel

    # Get project IDs the user is a member of
    member_pids_q = select(ProjectMember.project_id).where(
        ProjectMember.user_id == user_id
    )
    member_pids_result = await db.execute(member_pids_q)
    member_pids = [r for (r,) in member_pids_result.all()]
    total = len(member_pids)

    if not member_pids:
        return [], 0

    # Load projects
    page_pids = member_pids[offset : offset + limit]
    projects_result = await db.execute(
        select(Project).where(Project.id.in_(page_pids)).order_by(Project.name)
    )
    projects = list(projects_result.scalars().all())

    entries = []
    for proj in projects:
        # Run stats
        runs_r = await db.execute(
            select(sa_func.count()).where(RunModel.project_id == proj.id)
        )
        total_runs = runs_r.scalar_one()

        success_r = await db.execute(
            select(sa_func.count()).where(
                RunModel.project_id == proj.id, RunModel.status == "completed"
            )
        )
        successful = success_r.scalar_one()

        # Health grade
        rate = (successful / total_runs * 100) if total_runs > 0 else 100
        if rate >= 90:
            grade = "A"
        elif rate >= 75:
            grade = "B"
        elif rate >= 60:
            grade = "C"
        elif rate >= 45:
            grade = "D"
        else:
            grade = "F"

        entries.append(
            {
                "project_id": str(proj.id),
                "name": proj.name,
                "description": (proj.description or "")[:200],
                "status": proj.status.value
                if hasattr(proj.status, "value")
                else str(proj.status),
                "health_grade": grade,
                "total_runs": total_runs,
                "success_rate": round(rate, 1),
                "owner_id": str(proj.owner_id) if proj.owner_id else None,
            }
        )

    return entries, total


async def get_related_projects(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    limit: int = 5,
) -> list[dict]:
    """Suggest projects related to a given project (FM-165).

    Similarity is computed from:
    1. Shared knowledge tags / task types
    2. Common search index keywords
    """
    # Get knowledge tags for target project
    from app.models.project_knowledge import ProjectKnowledge as PK

    pk_result = await db.execute(
        select(PK).where(PK.project_id == project_id).limit(50)
    )
    knowledge_entries = list(pk_result.scalars().all())
    tags: set[str] = set()
    for k in knowledge_entries:
        if k.tags:
            tags.update(k.tags)

    # Get search index terms for target project
    idx_result = await db.execute(
        select(SearchIndex).where(
            SearchIndex.project_id == project_id,
            SearchIndex.entity_type == SearchEntityType.PROJECT,
        )
    )
    proj_idx = idx_result.scalar_one_or_none()
    proj_terms: set[str] = set()
    if proj_idx:
        text = f"{proj_idx.title} {proj_idx.body}".lower()
        proj_terms = {w for w in text.split() if len(w) > 3 and w.isalpha()}

    # Get other projects user has access to
    member_pids_result = await db.execute(
        select(ProjectMember.project_id).where(
            ProjectMember.user_id == user_id,
            ProjectMember.project_id != project_id,
        )
    )
    other_pids = [r for (r,) in member_pids_result.all()]
    if not other_pids:
        return []

    scored: list[tuple[float, dict]] = []
    for pid in other_pids:
        score = 0.0

        # Tag overlap
        if tags:
            other_pk = await db.execute(
                select(PK).where(PK.project_id == pid).limit(50)
            )
            other_tags: set[str] = set()
            for k in other_pk.scalars().all():
                if k.tags:
                    other_tags.update(k.tags)
            tag_overlap = len(tags & other_tags)
            score += tag_overlap * 10.0

        # Search index term overlap
        if proj_terms:
            other_idx = await db.execute(
                select(SearchIndex).where(
                    SearchIndex.project_id == pid,
                    SearchIndex.entity_type == SearchEntityType.PROJECT,
                )
            )
            other_proj_idx = other_idx.scalar_one_or_none()
            if other_proj_idx:
                other_text = f"{other_proj_idx.title} {other_proj_idx.body}".lower()
                other_terms = {
                    w for w in other_text.split() if len(w) > 3 and w.isalpha()
                }
                term_overlap = len(proj_terms & other_terms)
                score += term_overlap * 2.0

        if score > 0:
            # Load project info
            p_result = await db.execute(select(Project).where(Project.id == pid))
            p = p_result.scalar_one_or_none()
            if p:
                scored.append(
                    (
                        score,
                        {
                            "project_id": str(p.id),
                            "name": p.name,
                            "description": (p.description or "")[:200],
                            "similarity_score": round(score, 2),
                        },
                    )
                )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]
