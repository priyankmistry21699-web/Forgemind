"""FM-117: Constitution Suggestion routes — generate and resolve suggestions."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.constitution_suggestion import SuggestionStatus
from app.schemas.constitution_suggestion import (
    ConstitutionSuggestionList,
    ConstitutionSuggestionRead,
    ConstitutionSuggestionResolve,
)
from app.services import constitution_suggestion_service
from app.services.authz_service import check_project_permission, Action

router = APIRouter()


@router.post(
    "/projects/{project_id}/constitution-suggestions/generate",
    response_model=ConstitutionSuggestionList,
)
async def generate_suggestions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Analyze project history and generate constitution suggestions."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items = await constitution_suggestion_service.generate_suggestions(db, project_id)
    return ConstitutionSuggestionList(items=items, total=len(items))


@router.get(
    "/projects/{project_id}/constitution-suggestions",
    response_model=ConstitutionSuggestionList,
)
async def list_suggestions(
    project_id: uuid.UUID,
    status_filter: SuggestionStatus | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """List constitution suggestions for a project."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await constitution_suggestion_service.list_suggestions(
        db, project_id, status=status_filter
    )
    return ConstitutionSuggestionList(items=items, total=total)


@router.post(
    "/projects/{project_id}/constitution-suggestions/{suggestion_id}/resolve",
    response_model=ConstitutionSuggestionRead,
)
async def resolve_suggestion(
    project_id: uuid.UUID,
    suggestion_id: uuid.UUID,
    data: ConstitutionSuggestionResolve,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
):
    """Accept or reject a constitution suggestion."""
    await check_project_permission(db, project_id, user_id, Action.PROJECT_UPDATE)
    try:
        return await constitution_suggestion_service.resolve_suggestion(
            db, suggestion_id, data.action
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
