"""Knowledge base routes — project-level multi-run memory.

FM-048: CRUD, knowledge extraction, and context assembly endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.project_knowledge import KnowledgeType
from app.schemas.knowledge import (
    ProjectKnowledgeRead,
    ProjectKnowledgeList,
    ProjectKnowledgeCreate,
    KnowledgeExtractionResult,
    KnowledgeContext,
)
from app.services import knowledge_service
from app.services.authz_service import check_project_permission, Action
from app.core.authz_deps import resolve_project_for_entity, resolve_project_for_run
from app.models.project_knowledge import ProjectKnowledge

router = APIRouter()


@router.post(
    "/projects/{project_id}/knowledge",
    response_model=ProjectKnowledgeRead,
    status_code=201,
)
async def create_knowledge(
    project_id: uuid.UUID,
    body: ProjectKnowledgeCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ProjectKnowledgeRead:
    """Add a knowledge entry to a project."""
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_KNOWLEDGE
    )
    entry = await knowledge_service.create_knowledge(
        db,
        project_id=project_id,
        knowledge_type=body.knowledge_type,
        title=body.title,
        content=body.content,
        tags=body.tags,
        metadata=body.metadata_,
        source_run_id=body.source_run_id,
        source_task_id=body.source_task_id,
    )
    await db.commit()
    return ProjectKnowledgeRead.model_validate(entry)


@router.get(
    "/projects/{project_id}/knowledge",
    response_model=ProjectKnowledgeList,
)
async def list_knowledge(
    project_id: uuid.UUID,
    knowledge_type: KnowledgeType | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ProjectKnowledgeList:
    """List knowledge entries for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    entries, total = await knowledge_service.list_knowledge(
        db,
        project_id,
        knowledge_type=knowledge_type,
        limit=limit,
        offset=offset,
    )
    return ProjectKnowledgeList(
        items=[ProjectKnowledgeRead.model_validate(e) for e in entries],
        total=total,
    )


@router.get(
    "/knowledge/{knowledge_id}",
    response_model=ProjectKnowledgeRead,
)
async def get_knowledge(
    knowledge_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ProjectKnowledgeRead:
    """Get a single knowledge entry."""
    proj_id = await resolve_project_for_entity(db, ProjectKnowledge, knowledge_id)
    if proj_id is not None:
        await check_project_permission(db, proj_id, user_id, Action.PROJECT_VIEW)
    entry = await knowledge_service.get_knowledge(db, knowledge_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found",
        )
    return ProjectKnowledgeRead.model_validate(entry)


@router.delete("/knowledge/{knowledge_id}", status_code=204)
async def delete_knowledge(
    knowledge_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Delete a knowledge entry."""
    proj_id = await resolve_project_for_entity(db, ProjectKnowledge, knowledge_id)
    if proj_id is not None:
        await check_project_permission(
            db, proj_id, user_id, Action.PROJECT_MANAGE_KNOWLEDGE
        )
    deleted = await knowledge_service.delete_knowledge(db, knowledge_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge entry not found",
        )
    await db.commit()


@router.post(
    "/runs/{run_id}/extract-knowledge",
    response_model=KnowledgeExtractionResult,
)
async def extract_knowledge(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> KnowledgeExtractionResult:
    """Extract knowledge from a completed run."""
    pid = await resolve_project_for_run(db, run_id)
    await check_project_permission(db, pid, user_id, Action.PROJECT_MANAGE_KNOWLEDGE)
    entries = await knowledge_service.extract_knowledge_from_run(db, run_id)
    await db.commit()
    return KnowledgeExtractionResult(
        run_id=run_id,
        extracted_count=len(entries),
        items=[ProjectKnowledgeRead.model_validate(e) for e in entries],
    )


@router.get(
    "/projects/{project_id}/knowledge/context",
    response_model=KnowledgeContext,
)
async def get_knowledge_context(
    project_id: uuid.UUID,
    max_entries: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> KnowledgeContext:
    """Get assembled knowledge context for agent enrichment."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    ctx = await knowledge_service.get_knowledge_context(
        db, project_id, max_entries=max_entries
    )
    await db.commit()  # usage_count increments
    return KnowledgeContext(
        project_id=project_id,
        total_entries=ctx["total_entries"],
        context_text=ctx["context_text"],
        entries=[ProjectKnowledgeRead.model_validate(e) for e in ctx["entries"]],
    )
