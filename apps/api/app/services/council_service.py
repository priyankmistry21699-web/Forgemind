"""Council decision service — multi-agent deliberation and consensus.

FM-047A: Provides:
- Council session management (convene, deliberate, decide)
- Vote casting with confidence and weight
- Multiple decision methods (consensus, majority, supermajority, weighted)
- Automatic escalation when deadlocked
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from collections import Counter

from sqlalchemy import select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.council import (
    CouncilSession,
    CouncilVote,
    CouncilStatus,
    DecisionMethod,
    VoteDecision,
)

logger = logging.getLogger(__name__)


async def convene_council(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    topic: str,
    run_id: uuid.UUID | None = None,
    task_id: uuid.UUID | None = None,
    description: str | None = None,
    context: dict | None = None,
    decision_method: DecisionMethod = DecisionMethod.MAJORITY,
) -> CouncilSession:
    """Convene a new council session for a topic."""
    session = CouncilSession(
        project_id=project_id,
        run_id=run_id,
        task_id=task_id,
        topic=topic,
        description=description,
        context=context,
        decision_method=decision_method,
        status=CouncilStatus.CONVENED,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session, attribute_names=["votes"])
    return session


async def get_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> CouncilSession | None:
    """Retrieve a council session with its votes."""
    result = await db.execute(
        select(CouncilSession)
        .options(selectinload(CouncilSession.votes))
        .where(CouncilSession.id == session_id)
    )
    return result.scalar_one_or_none()


async def cast_vote(
    db: AsyncSession,
    session_id: uuid.UUID,
    *,
    agent_slug: str,
    decision: VoteDecision,
    reasoning: str | None = None,
    confidence: float = 0.5,
    suggested_modifications: dict | None = None,
    weight: float = 1.0,
) -> CouncilVote:
    """Cast a vote in a council session."""
    session = await get_session(db, session_id)
    if session is None:
        raise ValueError(f"Council session {session_id} not found")

    if session.status not in (CouncilStatus.CONVENED, CouncilStatus.DELIBERATING):
        raise ValueError(
            f"Cannot cast vote — session is {session.status.value}"
        )

    # Move to deliberating on first vote
    if session.status == CouncilStatus.CONVENED:
        session.status = CouncilStatus.DELIBERATING

    vote = CouncilVote(
        session_id=session_id,
        agent_slug=agent_slug,
        decision=decision,
        reasoning=reasoning,
        confidence=confidence,
        weight=weight,
        suggested_modifications=suggested_modifications,
    )
    db.add(vote)
    await db.flush()
    return vote


def _resolve_decision(
    votes: list[CouncilVote],
    method: DecisionMethod,
) -> tuple[str | None, str, dict]:
    """Resolve a decision based on votes and method.

    Returns (final_decision, rationale, vote_summary).
    """
    if not votes:
        return None, "No votes cast", {}

    # Build vote summary
    decision_counts: Counter[str] = Counter()
    weighted_scores: dict[str, float] = {}
    for v in votes:
        decision_counts[v.decision.value] += 1
        weighted_scores[v.decision.value] = (
            weighted_scores.get(v.decision.value, 0.0)
            + v.weight * v.confidence
        )

    total_votes = len(votes)
    non_abstain = [v for v in votes if v.decision != VoteDecision.ABSTAIN]
    total_non_abstain = len(non_abstain)

    vote_summary = {
        "total_votes": total_votes,
        "breakdown": dict(decision_counts),
        "weighted_scores": {k: round(v, 3) for k, v in weighted_scores.items()},
    }

    if total_non_abstain == 0:
        return None, "All agents abstained", vote_summary

    if method == DecisionMethod.CONSENSUS:
        # All non-abstain votes must agree
        decisions = {v.decision for v in non_abstain}
        if len(decisions) == 1:
            winner = decisions.pop().value
            return winner, f"Unanimous consensus: {winner}", vote_summary
        return None, "No consensus — votes are split", vote_summary

    elif method == DecisionMethod.MAJORITY:
        winner_decision, winner_count = decision_counts.most_common(1)[0]
        if winner_decision == VoteDecision.ABSTAIN.value:
            # Second most common that isn't abstain
            non_abstain_counts = Counter(
                {k: v for k, v in decision_counts.items() if k != VoteDecision.ABSTAIN.value}
            )
            if not non_abstain_counts:
                return None, "All abstained", vote_summary
            winner_decision, winner_count = non_abstain_counts.most_common(1)[0]
        if winner_count > total_non_abstain / 2:
            return winner_decision, f"Majority decision: {winner_decision} ({winner_count}/{total_non_abstain})", vote_summary
        return None, "No majority reached", vote_summary

    elif method == DecisionMethod.SUPERMAJORITY:
        for decision_val, count in decision_counts.most_common():
            if decision_val == VoteDecision.ABSTAIN.value:
                continue
            if count >= (total_non_abstain * 2 / 3):
                return decision_val, f"Supermajority: {decision_val} ({count}/{total_non_abstain})", vote_summary
        return None, "No supermajority reached", vote_summary

    elif method == DecisionMethod.WEIGHTED:
        # Highest weighted score wins
        best = max(
            ((k, v) for k, v in weighted_scores.items() if k != VoteDecision.ABSTAIN.value),
            key=lambda x: x[1],
            default=(None, 0),
        )
        if best[0] is not None:
            return best[0], f"Weighted decision: {best[0]} (score: {best[1]:.3f})", vote_summary
        return None, "No weighted decision possible", vote_summary

    return None, "Unknown decision method", vote_summary


async def resolve_council(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> dict[str, Any]:
    """Resolve a council session — tally votes and determine outcome."""
    session = await get_session(db, session_id)
    if session is None:
        return {"error": f"Council session {session_id} not found"}

    if session.status in (CouncilStatus.DECIDED, CouncilStatus.ESCALATED):
        return {
            "session_id": str(session_id),
            "status": session.status.value,
            "final_decision": session.final_decision,
            "decision_rationale": session.decision_rationale,
            "message": "Session already resolved",
        }

    final_decision, rationale, vote_summary = _resolve_decision(
        session.votes, session.decision_method
    )

    now = datetime.now(timezone.utc)

    if final_decision is not None:
        session.status = CouncilStatus.DECIDED
        session.final_decision = final_decision
        session.decision_rationale = rationale
        session.decision_metadata = vote_summary
        session.decided_at = now
    else:
        # Deadlocked — escalate
        session.status = CouncilStatus.DEADLOCKED
        session.decision_rationale = rationale
        session.decision_metadata = vote_summary

    await db.flush()

    return {
        "session_id": str(session_id),
        "status": session.status.value,
        "final_decision": final_decision,
        "decision_rationale": rationale,
        "vote_summary": vote_summary,
    }


async def escalate_council(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> dict[str, Any]:
    """Escalate a deadlocked council to human review."""
    session = await get_session(db, session_id)
    if session is None:
        return {"error": f"Council session {session_id} not found"}

    session.status = CouncilStatus.ESCALATED
    await db.flush()

    return {
        "session_id": str(session_id),
        "status": "escalated",
        "message": "Council escalated to human review",
    }


async def list_sessions(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    status_filter: CouncilStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CouncilSession], int]:
    """List council sessions with optional filters."""
    query = select(CouncilSession).options(selectinload(CouncilSession.votes))

    if project_id:
        query = query.where(CouncilSession.project_id == project_id)
    if run_id:
        query = query.where(CouncilSession.run_id == run_id)
    if status_filter:
        query = query.where(CouncilSession.status == status_filter)

    count_result = await db.execute(
        select(sa_func.count()).select_from(
            select(CouncilSession.id)
            .where(
                *([CouncilSession.project_id == project_id] if project_id else []),
                *([CouncilSession.run_id == run_id] if run_id else []),
                *([CouncilSession.status == status_filter] if status_filter else []),
            )
            .subquery()
        )
    )
    total = count_result.scalar_one()

    result = await db.execute(
        query.order_by(CouncilSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().unique().all()), total
