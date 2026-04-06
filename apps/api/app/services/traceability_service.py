"""FM-126: End-to-End Traceability service.

Computes lifecycle lineage from spec to delivery artifact for a run or project.
Uses explicit linkage fields (spec_artifact_id, run_id, task_id) rather than
separate traceability tables.
"""

import uuid
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.artifact import Artifact, ArtifactType
from app.models.run import Run
from app.models.task import Task
from app.models.execution_checkpoint import ExecutionCheckpoint
from app.models.planner_result import PlannerResult

logger = logging.getLogger(__name__)


async def compute_traceability(
    db: AsyncSession,
    run_id: uuid.UUID,
) -> dict[str, Any]:
    """Compute end-to-end traceability graph for a run.

    Returns a graph with nodes and edges representing the lifecycle:
    request/prompt → spec → plan → tasks → artifacts → checkpoints → delivery artifacts
    """
    # Load run
    run_result = await db.execute(select(Run).where(Run.id == run_id))
    run = run_result.scalar_one_or_none()
    if run is None:
        return {"error": "run_not_found"}

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    # Run node
    run_node = {
        "id": f"run:{run.id}",
        "type": "run",
        "label": f"Run #{run.run_number}",
        "status": run.status.value,
        "entity_id": str(run.id),
    }
    nodes.append(run_node)

    # Planner result (prompt → plan context)
    pr_result = await db.execute(
        select(PlannerResult).where(PlannerResult.run_id == run_id)
    )
    planner = pr_result.scalar_one_or_none()
    if planner:
        prompt_node = {
            "id": f"prompt:{planner.id}",
            "type": "prompt",
            "label": "User Prompt / Planner Input",
            "entity_id": str(planner.id),
        }
        nodes.append(prompt_node)
        edges.append(
            {"from": prompt_node["id"], "to": run_node["id"], "label": "triggers"}
        )

    # Artifacts (spec, plan, delivery)
    art_result = await db.execute(
        select(Artifact).where(Artifact.run_id == run_id).order_by(Artifact.created_at)
    )
    artifacts = list(art_result.scalars().all())

    spec_node_id = None
    plan_node_id = None

    for art in artifacts:
        art_node = {
            "id": f"artifact:{art.id}",
            "type": "artifact",
            "subtype": art.artifact_type.value,
            "label": art.title,
            "entity_id": str(art.id),
        }
        nodes.append(art_node)

        if art.artifact_type == ArtifactType.SPEC:
            spec_node_id = art_node["id"]
            edges.append(
                {"from": run_node["id"], "to": art_node["id"], "label": "produces"}
            )
            if planner:
                edges.append(
                    {
                        "from": f"prompt:{planner.id}",
                        "to": art_node["id"],
                        "label": "specifies",
                    }
                )

        elif art.artifact_type == ArtifactType.PLAN:
            plan_node_id = art_node["id"]
            if art.spec_artifact_id:
                edges.append(
                    {
                        "from": f"artifact:{art.spec_artifact_id}",
                        "to": art_node["id"],
                        "label": "planned_from",
                    }
                )
            elif spec_node_id:
                edges.append(
                    {
                        "from": spec_node_id,
                        "to": art_node["id"],
                        "label": "planned_from",
                    }
                )
            else:
                edges.append(
                    {"from": run_node["id"], "to": art_node["id"], "label": "produces"}
                )

        elif art.task_id:
            edges.append(
                {
                    "from": f"task:{art.task_id}",
                    "to": art_node["id"],
                    "label": "produces",
                }
            )

        else:
            edges.append(
                {"from": run_node["id"], "to": art_node["id"], "label": "produces"}
            )

    # Tasks
    task_result = await db.execute(
        select(Task).where(Task.run_id == run_id).order_by(Task.created_at)
    )
    tasks = list(task_result.scalars().all())

    for task in tasks:
        task_node = {
            "id": f"task:{task.id}",
            "type": "task",
            "label": task.title,
            "status": task.status.value,
            "entity_id": str(task.id),
        }
        nodes.append(task_node)

        # Link plan → task
        if plan_node_id:
            edges.append(
                {"from": plan_node_id, "to": task_node["id"], "label": "decomposes_to"}
            )
        else:
            edges.append(
                {"from": run_node["id"], "to": task_node["id"], "label": "contains"}
            )

    # Checkpoints
    cp_result = await db.execute(
        select(ExecutionCheckpoint)
        .where(ExecutionCheckpoint.run_id == run_id)
        .order_by(ExecutionCheckpoint.sequence_number)
    )
    checkpoints = list(cp_result.scalars().all())

    for cp in checkpoints:
        cp_node = {
            "id": f"checkpoint:{cp.id}",
            "type": "checkpoint",
            "subtype": cp.checkpoint_type.value,
            "label": cp.name or f"Checkpoint #{cp.sequence_number}",
            "entity_id": str(cp.id),
        }
        nodes.append(cp_node)
        edges.append(
            {"from": run_node["id"], "to": cp_node["id"], "label": "checkpoints"}
        )

        if cp.task_id:
            edges.append(
                {
                    "from": f"task:{cp.task_id}",
                    "to": cp_node["id"],
                    "label": "captured_at",
                }
            )

    return {
        "run_id": str(run_id),
        "project_id": str(run.project_id),
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
