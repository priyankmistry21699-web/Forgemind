import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.task import (
    TaskRead,
    TaskList,
    TaskStatusUpdate,
    ReadyTasksResponse,
    TaskClaimRequest,
    TaskCompleteRequest,
    TaskFailRequest,
)
from app.services import task_service, execution_service

router = APIRouter()


@router.get("/runs/{run_id}/tasks", response_model=TaskList)
async def list_tasks(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskList:
    """List all tasks for a given run, ordered by execution index."""
    tasks, total = await task_service.list_tasks_by_run(db, run_id)
    return TaskList(
        items=[TaskRead.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/runs/{run_id}/tasks/ready", response_model=ReadyTasksResponse)
async def get_ready_tasks(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ReadyTasksResponse:
    """Return tasks whose dependencies are all satisfied and are ready to execute."""
    tasks, total = await task_service.get_ready_tasks(db, run_id)
    return ReadyTasksResponse(
        items=[TaskRead.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    task = await task_service.get_task(db, task_id)
    return TaskRead.model_validate(task)


@router.patch("/tasks/{task_id}/status", response_model=TaskRead)
async def update_task_status(
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Transition a task to a new status with state-machine validation."""
    task = await task_service.update_task_status(db, task_id, data.status)
    return TaskRead.model_validate(task)


@router.post("/tasks/{task_id}/claim", response_model=TaskRead)
async def claim_task(
    task_id: uuid.UUID,
    data: TaskClaimRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Claim a READY task for an agent, setting it to RUNNING."""
    task = await execution_service.claim_task(db, task_id, data.agent_slug)
    await db.commit()
    return TaskRead.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: uuid.UUID,
    data: TaskCompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Complete a RUNNING task, optionally creating an output artifact."""
    task = await execution_service.complete_task(
        db,
        task_id,
        artifact_title=data.artifact_title,
        artifact_content=data.artifact_content,
        artifact_type=data.artifact_type,
    )
    await db.commit()
    return TaskRead.model_validate(task)


@router.post("/tasks/{task_id}/fail", response_model=TaskRead)
async def fail_task(
    task_id: uuid.UUID,
    data: TaskFailRequest,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Fail a RUNNING task with an error message."""
    task = await execution_service.fail_task(db, task_id, data.error_message)
    await db.commit()
    return TaskRead.model_validate(task)


@router.post("/tasks/{task_id}/retry", response_model=TaskRead)
async def retry_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Retry a FAILED task, resetting it to READY for re-execution."""
    task = await execution_service.retry_task(db, task_id)
    await db.commit()
    return TaskRead.model_validate(task)


@router.post("/tasks/{task_id}/cancel", response_model=TaskRead)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TaskRead:
    """Cancel a READY or RUNNING task."""
    task = await execution_service.cancel_task(db, task_id)
    await db.commit()
    return TaskRead.model_validate(task)
