"""Comment routes — threaded comments API (FM-141)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.comment import CommentEntityType
from app.schemas.comment import CommentCreate, CommentUpdate, CommentRead, CommentList
from app.services import comment_service

router = APIRouter()


@router.post("/comments", response_model=CommentRead, status_code=201)
async def create_comment(
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CommentRead:
    comment = await comment_service.create_comment(db, data, author_id=user_id)
    return CommentRead.model_validate(comment)


@router.get("/comments/{comment_id}", response_model=CommentRead)
async def get_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CommentRead:
    comment = await comment_service.get_comment(db, comment_id)
    return CommentRead.model_validate(comment)


@router.get("/comments", response_model=CommentList)
async def list_comments(
    entity_type: CommentEntityType,
    entity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CommentList:
    items, total = await comment_service.list_comments(db, entity_type, entity_id)
    return CommentList(
        items=[CommentRead.model_validate(c) for c in items],
        total=total,
    )


@router.patch("/comments/{comment_id}", response_model=CommentRead)
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CommentRead:
    comment = await comment_service.update_comment(db, comment_id, data, user_id)
    return CommentRead.model_validate(comment)


@router.delete("/comments/{comment_id}", response_model=CommentRead)
async def delete_comment(
    comment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CommentRead:
    comment = await comment_service.delete_comment(db, comment_id, user_id)
    return CommentRead.model_validate(comment)
