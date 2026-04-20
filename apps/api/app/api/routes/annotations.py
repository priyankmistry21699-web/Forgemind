"""Run annotation routes — FM-146: Collaborative Run Annotations."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user_id
from app.models.run_annotation import AnnotationType
from app.schemas.run_annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationRead,
    AnnotationList,
)
from app.services import run_annotation_service

router = APIRouter()


@router.post(
    "/runs/{run_id}/annotations",
    response_model=AnnotationRead,
    status_code=201,
)
async def create_annotation(
    run_id: uuid.UUID,
    data: AnnotationCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AnnotationRead:
    annotation = await run_annotation_service.create_annotation(
        db, run_id, data, user_id
    )
    return AnnotationRead.model_validate(annotation)


@router.get("/runs/{run_id}/annotations", response_model=AnnotationList)
async def list_annotations(
    run_id: uuid.UUID,
    annotation_type: Optional[AnnotationType] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AnnotationList:
    items, total = await run_annotation_service.list_annotations(
        db, run_id, annotation_type
    )
    return AnnotationList(
        items=[AnnotationRead.model_validate(a) for a in items],
        total=total,
    )


@router.patch("/annotations/{annotation_id}", response_model=AnnotationRead)
async def update_annotation(
    annotation_id: uuid.UUID,
    data: AnnotationUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> AnnotationRead:
    annotation = await run_annotation_service.update_annotation(
        db, annotation_id, data, user_id
    )
    return AnnotationRead.model_validate(annotation)


@router.delete("/annotations/{annotation_id}", status_code=204)
async def delete_annotation(
    annotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await run_annotation_service.delete_annotation(db, annotation_id, user_id)
