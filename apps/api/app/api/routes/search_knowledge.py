"""Search, knowledge discovery, conventions & recommendations routes.

FM-161: GET /search — full-text search
FM-162: GET /search/similar — find similar entities
FM-163: GET /knowledge/search — knowledge-specific search
FM-164: GET /templates/marketplace — template marketplace
FM-165: GET /search (scope=global) — cross-project search (RBAC enforced)
FM-166: GET /runs/{id}/compare/{id2} — run comparison
FM-167: CRUD /projects/{id}/conventions, POST /runs/{id}/check-conventions
FM-168: GET /artifacts/{id}/versions, GET /artifacts/{id}/diff, PATCH /artifacts/{id}/tag
FM-169: GET /projects/{id}/recommendations, PATCH /recommendations/{id}/dismiss
FM-170: POST /projects/{id}/reindex — search index maintenance
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.search_knowledge import (
    SearchEntityType,
    ConventionCategory,
)
from app.schemas.search_knowledge import (
    SearchResponse,
    SimilarSearchResponse,
    ConventionCreate,
    ConventionUpdate,
    ConventionRead,
    ConventionList,
    ComplianceCheckResult,
    ArtifactVersionHistory,
    ArtifactVersionEntry,
    ArtifactDiff,
    ArtifactVersionTag,
    RecommendationRead,
    RecommendationList,
    RecommendationDismiss,
    RunComparisonSummary,
    KnowledgeSearchResponse,
    TemplateMarketplaceList,
    TemplateMarketplaceEntry,
)
from app.services import search_service
from app.services import convention_service
from app.services import artifact_version_service
from app.services import recommendation_service
from app.services import run_comparison_service
from app.services.authz_service import check_project_permission, Action
from app.models.project_knowledge import KnowledgeType

router = APIRouter()


# ── FM-161 / FM-165: Search ──────────────────────────────────────


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=500),
    project_id: uuid.UUID | None = Query(None),
    entity_type: str | None = Query(None, description="Comma-separated: task,artifact,comment,run,project,knowledge,annotation,approval"),
    entity_status: str | None = Query(None),
    created_after: str | None = Query(None, description="ISO date filter (e.g. 2026-01-01)"),
    created_before: str | None = Query(None, description="ISO date filter"),
    facets: bool = Query(False, description="Include facet counts by entity_type and status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SearchResponse:
    """Full-text search across all indexed entities.

    - With project_id: scoped search within one project
    - Without project_id: cross-project search (RBAC filtered)
    - With facets=true: returns aggregation counts by entity_type and status
    """
    if project_id:
        await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)

    # Parse entity types
    types = None
    if entity_type:
        try:
            types = [SearchEntityType(t.strip()) for t in entity_type.split(",")]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity_type. Valid: {[e.value for e in SearchEntityType]}",
            )

    # Parse date-range filters
    from datetime import datetime as _dt

    dt_after = None
    dt_before = None
    if created_after:
        try:
            dt_after = _dt.fromisoformat(created_after)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_after date format")
    if created_before:
        try:
            dt_before = _dt.fromisoformat(created_before)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid created_before date format")

    items, total, facet_data = await search_service.search(
        db,
        query=q,
        project_id=project_id,
        entity_types=types,
        entity_status=entity_status,
        created_after=dt_after,
        created_before=dt_before,
        limit=limit,
        offset=offset,
        user_id=user_id if not project_id else None,
        include_facets=facets,
    )

    resp = SearchResponse(
        query=q,
        total=total,
        items=items,
        scope=f"project:{project_id}" if project_id else "global",
        filters={"entity_type": entity_type, "entity_status": entity_status},
    )
    if facet_data:
        resp.facets = facet_data
    return resp


# ── FM-162: Find Similar ─────────────────────────────────────────


@router.get("/search/similar", response_model=SimilarSearchResponse)
async def find_similar(
    entity_type: SearchEntityType = Query(...),
    entity_id: uuid.UUID = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> SimilarSearchResponse:
    """Find entities similar to a given entity based on content overlap."""
    items = await search_service.find_similar(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
    return SimilarSearchResponse(
        source_entity_type=entity_type.value,
        source_entity_id=entity_id,
        items=items,
        total=len(items),
    )


# ── FM-163: Knowledge Search ─────────────────────────────────────


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(..., min_length=1, max_length=500),
    project_id: uuid.UUID | None = Query(None),
    knowledge_type: KnowledgeType | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> KnowledgeSearchResponse:
    """Search knowledge entries across projects."""
    # Use the search service filtered to knowledge type
    items, total = await search_service.search(
        db,
        query=q,
        project_id=project_id,
        entity_types=[SearchEntityType.KNOWLEDGE],
        limit=limit,
        user_id=user_id if not project_id else None,
    )
    return KnowledgeSearchResponse(query=q, items=items, total=total)


# ── FM-164: Template Marketplace ──────────────────────────────────


@router.get("/templates/marketplace", response_model=TemplateMarketplaceList)
async def template_marketplace(
    category: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> TemplateMarketplaceList:
    """Browse the template marketplace with optional search and category filter."""
    from app.models.project_template import ProjectTemplate
    from sqlalchemy import select, func as sa_func, and_, or_

    filters = [ProjectTemplate.is_active.is_(True)]
    if category:
        filters.append(ProjectTemplate.category == category)
    if q:
        q_like = f"%{q.lower()}%"
        filters.append(
            or_(
                sa_func.lower(ProjectTemplate.name).like(q_like),
                sa_func.lower(ProjectTemplate.description).like(q_like),
            )
        )

    where = and_(*filters)

    count_q = select(sa_func.count()).select_from(
        select(ProjectTemplate.id).where(where).subquery()
    )
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        select(ProjectTemplate)
        .where(where)
        .order_by(ProjectTemplate.name)
        .offset(offset)
        .limit(limit)
    )
    templates = list(result.scalars().all())

    items = [
        TemplateMarketplaceEntry(
            id=t.id,
            slug=t.slug,
            name=t.name,
            description=t.description,
            category=t.category or "general",
            is_builtin=t.is_builtin if hasattr(t, "is_builtin") else False,
            has_knowledge=bool(getattr(t, "knowledge_snapshot", None)),
            has_views=bool(getattr(t, "views_snapshot", None)),
            version=getattr(t, "version", None),
            created_at=t.created_at,
        )
        for t in templates
    ]
    return TemplateMarketplaceList(items=items, total=total)


# ── FM-166: Run Comparison ────────────────────────────────────────


@router.get("/runs/{run_a_id}/compare/{run_b_id}", response_model=RunComparisonSummary)
async def compare_runs(
    run_a_id: uuid.UUID,
    run_b_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RunComparisonSummary:
    """Compare two runs side-by-side."""
    result = await run_comparison_service.compare_runs(db, run_a_id, run_b_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both runs not found",
        )
    return RunComparisonSummary(**result)


# ── FM-167: Conventions ──────────────────────────────────────────


@router.post(
    "/projects/{project_id}/conventions",
    response_model=ConventionRead,
    status_code=201,
)
async def create_convention(
    project_id: uuid.UUID,
    body: ConventionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ConventionRead:
    """Create a new organizational convention."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    conv = await convention_service.create_convention(
        db,
        project_id=project_id,
        category=body.category,
        name=body.name,
        description=body.description,
        rule_text=body.rule_text,
        enforcement_level=body.enforcement_level,
        author_id=user_id,
    )
    await db.commit()
    return ConventionRead.model_validate(conv)


@router.get(
    "/projects/{project_id}/conventions",
    response_model=ConventionList,
)
async def list_conventions(
    project_id: uuid.UUID,
    category: ConventionCategory | None = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ConventionList:
    """List conventions for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await convention_service.list_conventions(
        db,
        project_id=project_id,
        category=category,
        active_only=active_only,
        limit=limit,
        offset=offset,
    )
    return ConventionList(
        items=[ConventionRead.model_validate(c) for c in items],
        total=total,
    )


@router.put("/conventions/{convention_id}", response_model=ConventionRead)
async def update_convention(
    convention_id: uuid.UUID,
    body: ConventionUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ConventionRead:
    """Update a convention."""
    conv = await convention_service.update_convention(
        db,
        convention_id,
        **body.model_dump(exclude_none=True),
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Convention not found")
    await db.commit()
    return ConventionRead.model_validate(conv)


@router.delete("/conventions/{convention_id}", status_code=204)
async def delete_convention(
    convention_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a convention."""
    deleted = await convention_service.delete_convention(db, convention_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Convention not found")
    await db.commit()


@router.get(
    "/projects/{project_id}/conventions/injectable",
    response_model=list[dict],
)
async def get_injectable_conventions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> list[dict]:
    """Get active conventions formatted for agent prompt injection."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await convention_service.get_active_conventions_for_injection(db, project_id)


@router.post(
    "/runs/{run_id}/check-conventions",
    response_model=ComplianceCheckResult,
)
async def check_conventions(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ComplianceCheckResult:
    """Check a run's outputs against active conventions."""
    result = await convention_service.check_conventions_compliance(db, run_id)
    return ComplianceCheckResult(**result)


# ── FM-168: Artifact Versioning ──────────────────────────────────


@router.get("/artifacts/{artifact_id}/versions", response_model=ArtifactVersionHistory)
async def get_artifact_versions(
    artifact_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactVersionHistory:
    """Get version history for an artifact."""
    versions = await artifact_version_service.get_version_history(db, artifact_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactVersionHistory(
        artifact_id=artifact_id,
        versions=[
            ArtifactVersionEntry(
                id=v.id,
                version=v.version,
                version_tag=getattr(v, "version_tag", None),
                title=v.title,
                artifact_type=v.artifact_type.value if v.artifact_type else "other",
                created_by=v.created_by,
                created_at=v.created_at,
            )
            for v in versions
        ],
        total=len(versions),
    )


@router.get("/artifacts/{artifact_id}/diff")
async def get_artifact_diff(
    artifact_id: uuid.UUID,
    version_a: int = Query(..., ge=1),
    version_b: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArtifactDiff:
    """Compute diff between two versions of an artifact."""
    result = await artifact_version_service.diff_versions(
        db, artifact_id, version_a, version_b
    )
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Artifact or requested versions not found",
        )
    return ArtifactDiff(**result)


@router.patch("/artifacts/{artifact_id}/tag")
async def tag_artifact_version(
    artifact_id: uuid.UUID,
    body: ArtifactVersionTag,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Tag an artifact version."""
    art = await artifact_version_service.tag_version(db, artifact_id, body.version_tag)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    await db.commit()
    return {"id": str(art.id), "version": art.version, "version_tag": art.version_tag}


# ── FM-169: Recommendations ──────────────────────────────────────


@router.get(
    "/projects/{project_id}/recommendations",
    response_model=RecommendationList,
)
async def get_recommendations(
    project_id: uuid.UUID,
    include_dismissed: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RecommendationList:
    """Get smart recommendations for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await recommendation_service.list_recommendations(
        db,
        project_id,
        include_dismissed=include_dismissed,
        limit=limit,
        offset=offset,
    )
    return RecommendationList(
        items=[RecommendationRead.model_validate(r) for r in items],
        total=total,
    )


@router.post(
    "/projects/{project_id}/recommendations/generate",
    response_model=RecommendationList,
)
async def generate_recommendations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RecommendationList:
    """Analyze project state and generate new recommendations."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    generated = await recommendation_service.generate_recommendations(db, project_id)
    await db.commit()
    return RecommendationList(
        items=[RecommendationRead.model_validate(r) for r in generated],
        total=len(generated),
    )


@router.patch("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: uuid.UUID,
    body: RecommendationDismiss | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Dismiss a recommendation with optional feedback."""
    feedback = body.feedback if body else None
    rec = await recommendation_service.dismiss_recommendation(
        db, recommendation_id, feedback=feedback
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    await db.commit()
    return {
        "id": str(rec.id),
        "dismissed": rec.dismissed,
        "feedback": rec.feedback,
    }


# ── FM-170: Reindex ──────────────────────────────────────────────


@router.post("/projects/{project_id}/reindex")
async def reindex_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Rebuild the search index for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    count = await search_service.reindex_project(db, project_id)
    await db.commit()
    return {"project_id": str(project_id), "indexed_count": count}


@router.get("/projects/{project_id}/search-integrity")
async def check_search_integrity(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Check search index integrity for a project.

    Compares indexed entries against actual database records. Reports
    orphaned index entries and missing source records.
    """
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    return await search_service.check_index_integrity(db, project_id)


# ── FM-165: Project Directory & Related Suggestions ───────────────


@router.get("/project-directory")
async def project_directory(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Browse all accessible projects with health summaries (FM-165).

    Returns a paginated directory of projects the current user can access,
    each annotated with run stats and a health grade.
    """
    items, total = await search_service.get_project_directory(
        db, user_id, limit=limit, offset=offset,
    )
    return {"items": items, "total": total}


@router.get("/projects/{project_id}/related")
async def related_projects(
    project_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> dict:
    """Suggest related projects based on shared knowledge and content (FM-165)."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items = await search_service.get_related_projects(
        db, project_id, user_id, limit=limit,
    )
    return {"project_id": str(project_id), "related": items, "total": len(items)}
