"""FM-222/223/224/228/230: Agent intelligence endpoints.

Routes:
  GET  /projects/{id}/memory                  — list agent memory entries
  POST /projects/{id}/memory                  — store a memory entry
  GET  /projects/{id}/security-findings       — list security findings
  POST /projects/{id}/generate-docs           — trigger doc generation task
  GET  /runs/{id}/llm-cost-summary            — per-run LLM cost breakdown
  GET  /runs/{id}/stream                      — SSE stream of live agent output
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.models.agent_intelligence import (
    AgentMemoryEntry,
    FindingSeverity,
    LLMCallLog,
    SecurityFinding,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# FM-222: Agent memory
# ---------------------------------------------------------------------------


class MemoryIn(BaseModel):
    agent_type: str
    key: str
    value: dict[str, Any]


@router.get("/projects/{project_id}/memory")
async def list_memory(
    project_id: uuid.UUID,
    agent_type: str | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    q = select(AgentMemoryEntry).where(AgentMemoryEntry.project_id == project_id)
    if agent_type:
        q = q.where(AgentMemoryEntry.agent_type == agent_type)
    q = q.order_by(AgentMemoryEntry.created_at.desc()).limit(limit)
    result = await db.execute(q)
    entries = result.scalars().all()
    return {
        "items": [
            {
                "id": str(e.id),
                "agent_type": e.agent_type,
                "key": e.key,
                "value": e.value_json,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
        "total": len(entries),
    }


@router.post("/projects/{project_id}/memory", status_code=201)
async def store_memory(
    project_id: uuid.UUID,
    body: MemoryIn,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services import agent_memory_service

    entry = await agent_memory_service.store_memory(
        db,
        project_id=project_id,
        agent_type=body.agent_type,
        key=body.key,
        value=body.value,
    )
    await db.commit()
    return {"id": str(entry.id), "key": entry.key}


# ---------------------------------------------------------------------------
# FM-230: Security findings
# ---------------------------------------------------------------------------


@router.get("/projects/{project_id}/security-findings")
async def list_security_findings(
    project_id: uuid.UUID,
    severity: FindingSeverity | None = Query(None),
    resolved: bool | None = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    q = select(SecurityFinding).where(SecurityFinding.project_id == project_id)
    if severity:
        q = q.where(SecurityFinding.severity == severity)
    if resolved is not None:
        q = q.where(SecurityFinding.resolved == resolved)
    q = q.order_by(SecurityFinding.created_at.desc()).limit(limit)
    result = await db.execute(q)
    findings = result.scalars().all()
    return {
        "items": [
            {
                "id": str(f.id),
                "severity": f.severity.value,
                "source": f.source.value,
                "title": f.title,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "cwe_id": f.cwe_id,
                "cve_id": f.cve_id,
                "resolved": f.resolved,
                "created_at": f.created_at.isoformat(),
            }
            for f in findings
        ],
        "total": len(findings),
    }


@router.patch("/projects/{project_id}/security-findings/{finding_id}/resolve")
async def resolve_finding(
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    result = await db.execute(
        select(SecurityFinding).where(
            SecurityFinding.id == finding_id,
            SecurityFinding.project_id == project_id,
        )
    )
    finding = result.scalar_one_or_none()
    if finding is None:
        raise HTTPException(status_code=404, detail="Finding not found")
    finding.resolved = True
    await db.commit()
    return {"id": str(finding.id), "resolved": True}


# ---------------------------------------------------------------------------
# FM-228: Generate docs
# ---------------------------------------------------------------------------


class GenerateDocsIn(BaseModel):
    doc_type: str = "readme"  # readme | api | architecture


@router.post("/projects/{project_id}/generate-docs", status_code=202)
async def generate_docs(
    project_id: uuid.UUID,
    body: GenerateDocsIn,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> dict:
    from sqlalchemy import func as _func
    from app.models.project import Project
    from app.models.run import Run, RunStatus
    from app.models.task import Task, TaskStatus

    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine next run_number for this project
    count_result = await db.execute(
        select(_func.count()).select_from(Run).where(Run.project_id == project_id)
    )
    run_number = (count_result.scalar_one() or 0) + 1

    run = Run(
        project_id=project_id,
        run_number=run_number,
        status=RunStatus.RUNNING,
        trigger="generate-docs",
    )
    db.add(run)
    await db.flush()

    task = Task(
        run_id=run.id,
        title=f"Generate {body.doc_type} docs",
        description=body.doc_type,
        task_type="documentation",
        status=TaskStatus.READY,
        assigned_agent_slug="doc-agent",
        order_index=0,
    )
    db.add(task)
    await db.commit()

    return {"run_id": str(run.id), "task_id": str(task.id), "status": "queued"}


# ---------------------------------------------------------------------------
# FM-223: LLM cost summary
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/llm-cost-summary")
async def llm_cost_summary(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(get_current_user_id),
) -> dict:
    from app.services.llm_cost_service import get_run_cost_summary

    return await get_run_cost_summary(db, run_id)


# ---------------------------------------------------------------------------
# FM-224: SSE stream
# ---------------------------------------------------------------------------


@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: uuid.UUID,
    _: str = Depends(get_current_user_id),
) -> StreamingResponse:
    from app.services.agent_stream_service import stream_run_events

    async def event_generator():
        async for chunk in stream_run_events(run_id):
            yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
