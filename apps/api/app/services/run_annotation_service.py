"""Run annotation service — CRUD for FM-146."""

import uuid

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.run_annotation import RunAnnotation, AnnotationType
from app.schemas.run_annotation import AnnotationCreate, AnnotationUpdate


async def create_annotation(
    db: AsyncSession,
    run_id: uuid.UUID,
    data: AnnotationCreate,
    author_id: uuid.UUID,
) -> RunAnnotation:
    annotation = RunAnnotation(
        run_id=run_id,
        author_id=author_id,
        annotation_type=data.annotation_type,
        body=data.body,
        pinned_event_id=data.pinned_event_id,
    )
    db.add(annotation)
    await db.flush()
    await db.refresh(annotation)
    return annotation


async def list_annotations(
    db: AsyncSession,
    run_id: uuid.UUID,
    annotation_type: AnnotationType | None = None,
) -> tuple[list[RunAnnotation], int]:
    base = select(RunAnnotation).where(RunAnnotation.run_id == run_id)
    if annotation_type:
        base = base.where(RunAnnotation.annotation_type == annotation_type)

    count_q = select(func.count()).select_from(base.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    result = await db.execute(base.order_by(RunAnnotation.created_at.asc()))
    return list(result.scalars().all()), total


async def update_annotation(
    db: AsyncSession,
    annotation_id: uuid.UUID,
    data: AnnotationUpdate,
    user_id: uuid.UUID,
) -> RunAnnotation:
    annotation = await db.get(RunAnnotation, annotation_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail="Annotation not found")
    if annotation.author_id != user_id:
        raise HTTPException(status_code=403, detail="Only the author can edit this annotation")
    annotation.body = data.body
    await db.flush()
    await db.refresh(annotation)
    return annotation


async def delete_annotation(
    db: AsyncSession,
    annotation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    annotation = await db.get(RunAnnotation, annotation_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail="Annotation not found")
    if annotation.author_id != user_id:
        raise HTTPException(status_code=403, detail="Only the author can delete this annotation")
    await db.delete(annotation)
    await db.flush()
