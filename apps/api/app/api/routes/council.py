"""Council routes — multi-agent decision engine endpoints.

FM-047A: Convene councils, cast votes, resolve decisions, escalate deadlocks.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.council import CouncilStatus
from app.schemas.council import (
    CouncilSessionRead,
    CouncilSessionList,
    ConveneCouncilRequest,
    CastVoteRequest,
    CouncilVoteRead,
    CouncilDecisionResult,
)
from app.services import council_service

router = APIRouter(prefix="/council")


@router.post("/sessions", response_model=CouncilSessionRead, status_code=201)
async def convene_council(
    body: ConveneCouncilRequest,
    db: AsyncSession = Depends(get_db),
) -> CouncilSessionRead:
    """Convene a new council session for multi-agent deliberation."""
    session = await council_service.convene_council(
        db,
        project_id=body.project_id,
        run_id=body.run_id,
        task_id=body.task_id,
        topic=body.topic,
        description=body.description,
        context=body.context,
        decision_method=body.decision_method,
    )
    await db.commit()
    return CouncilSessionRead.model_validate(session)


@router.get("/sessions", response_model=CouncilSessionList)
async def list_sessions(
    project_id: uuid.UUID | None = Query(None),
    run_id: uuid.UUID | None = Query(None),
    status_filter: CouncilStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> CouncilSessionList:
    """List council sessions with optional filters."""
    sessions, total = await council_service.list_sessions(
        db,
        project_id=project_id,
        run_id=run_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )
    return CouncilSessionList(
        items=[CouncilSessionRead.model_validate(s) for s in sessions],
        total=total,
    )


@router.get("/sessions/{session_id}", response_model=CouncilSessionRead)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CouncilSessionRead:
    """Get a council session with its votes."""
    session = await council_service.get_session(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Council session not found",
        )
    return CouncilSessionRead.model_validate(session)


@router.post(
    "/sessions/{session_id}/vote",
    response_model=CouncilVoteRead,
    status_code=201,
)
async def cast_vote(
    session_id: uuid.UUID,
    body: CastVoteRequest,
    db: AsyncSession = Depends(get_db),
) -> CouncilVoteRead:
    """Cast a vote in a council session."""
    try:
        vote = await council_service.cast_vote(
            db,
            session_id,
            agent_slug=body.agent_slug,
            decision=body.decision,
            reasoning=body.reasoning,
            confidence=body.confidence,
            suggested_modifications=body.suggested_modifications,
        )
        await db.commit()
        return CouncilVoteRead.model_validate(vote)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/sessions/{session_id}/resolve")
async def resolve_council(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a council session — tally votes and determine outcome."""
    result = await council_service.resolve_council(db, session_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result


@router.post("/sessions/{session_id}/escalate")
async def escalate_council(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Escalate a deadlocked council to human review."""
    result = await council_service.escalate_council(db, session_id)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"],
        )
    await db.commit()
    return result
