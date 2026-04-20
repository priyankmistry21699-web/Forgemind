"""Comment service — CRUD + threading for FM-141.

Provides threaded comments on runs, tasks, artifacts, and other entities.
"""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment, CommentEntityType
from app.schemas.comment import CommentCreate, CommentUpdate


async def create_comment(
    db: AsyncSession,
    data: CommentCreate,
    author_id: uuid.UUID,
) -> Comment:
    """Create a comment, optionally threaded under a parent."""
    if data.parent_id:
        parent = await db.get(Comment, data.parent_id)
        if parent is None or parent.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent.entity_type != data.entity_type or parent.entity_id != data.entity_id:
            raise HTTPException(
                status_code=400,
                detail="Parent comment belongs to a different entity",
            )

    comment = Comment(
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        parent_id=data.parent_id,
        author_id=author_id,
        body=data.body,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)
    # Eagerly load replies to avoid MissingGreenlet during Pydantic serialization
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment.id)
        .options(selectinload(Comment.replies))
    )
    return result.scalar_one()


async def get_comment(db: AsyncSession, comment_id: uuid.UUID) -> Comment:
    """Get a single comment by ID."""
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.replies))
    )
    comment = result.scalar_one_or_none()
    if comment is None or comment.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


async def list_comments(
    db: AsyncSession,
    entity_type: CommentEntityType,
    entity_id: uuid.UUID,
    *,
    include_deleted: bool = False,
) -> tuple[list[Comment], int]:
    """List top-level comments for an entity with nested replies."""
    base = select(Comment).where(
        Comment.entity_type == entity_type,
        Comment.entity_id == entity_id,
        Comment.parent_id.is_(None),
    )
    if not include_deleted:
        base = base.where(Comment.deleted_at.is_(None))

    base = base.options(selectinload(Comment.replies)).order_by(
        Comment.created_at.asc()
    )

    count_q = select(func.count()).select_from(
        select(Comment.id)
        .where(
            Comment.entity_type == entity_type,
            Comment.entity_id == entity_id,
        )
        .where(Comment.deleted_at.is_(None) if not include_deleted else True)
        .subquery()
    )

    result = await db.execute(base)
    comments = list(result.scalars().unique().all())

    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    return comments, total


async def update_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    data: CommentUpdate,
    user_id: uuid.UUID,
) -> Comment:
    """Update a comment body. Only the author may edit."""
    comment = await get_comment(db, comment_id)
    if comment.author_id != user_id:
        raise HTTPException(
            status_code=403, detail="Only the author can edit this comment"
        )
    comment.body = data.body
    await db.flush()
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.replies))
    )
    return result.scalar_one()


async def delete_comment(
    db: AsyncSession,
    comment_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Comment:
    """Soft-delete a comment (preserves audit trail)."""
    comment = await get_comment(db, comment_id)
    if comment.author_id != user_id:
        raise HTTPException(
            status_code=403, detail="Only the author can delete this comment"
        )
    comment.deleted_at = datetime.now(timezone.utc)
    await db.flush()
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.replies))
    )
    return result.scalar_one()
