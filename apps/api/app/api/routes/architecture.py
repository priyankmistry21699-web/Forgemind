"""Architecture routes -- graph, topology, drift, rules, impact, recommendations, design docs, approvals.

FM-081 to FM-090: Architecture Intelligence, Topology Awareness, Drift Detection,
Structural Governance, and related subsystems.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user_id
from app.db.session import get_db
from app.services.authz_service import check_project_permission, Action

# -- Schemas --
from app.schemas.architecture import (
    ArchitectureNodeCreate,
    ArchitectureNodeRead,
    ArchitectureNodeList,
    ArchitectureNodeUpdate,
    ArchitectureEdgeCreate,
    ArchitectureEdgeRead,
    ArchitectureEdgeList,
    ArchitectureSnapshotRead,
    ArchitectureSnapshotList,
    ArchitectureGraphRead,
    NeighborRead,
    TopologyMapRequest,
    TopologySummary,
    ArchitectureDriftRead,
    ArchitectureDriftList,
    ArchitectureRuleCreate,
    ArchitectureRuleRead,
    ArchitectureRuleList,
    ArchitectureRuleResultRead,
    ArchitectureRuleResultList,
    DesignDocRead,
    ImpactAnalysisRequest,
    ChangeImpactAssessmentRead,
    RefactorRecommendation,
    RefactorRecommendationList,
    StructuralHealthScore,
)
from app.schemas.approval import ApprovalRead, ApprovalList

# -- Services --
from app.services import (
    architecture_service,
    topology_mapper_service,
    drift_detection_service,
    architecture_rule_service,
    design_doc_service,
    impact_analysis_service,
    refactor_recommendation_service,
    architecture_approval_service,
    structural_health_service,
)

from app.models.architecture import DriftStatus, NodeType, EdgeType

router = APIRouter()


# ── FM-081: Architecture Graph Foundation ────────────────────────


@router.post(
    "/projects/{project_id}/architecture/nodes",
    response_model=ArchitectureNodeRead,
    status_code=201,
)
async def create_node(
    project_id: uuid.UUID,
    body: ArchitectureNodeCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureNodeRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    node = await architecture_service.create_node(
        db,
        project_id=project_id,
        workspace_id=None,
        node_type=body.node_type,
        key=body.key,
        name=body.name,
        path=body.path,
        language=body.language,
        metadata_=body.metadata_,
        source_type=body.source_type,
        status=body.status,
        repo_id=body.repo_id,
    )
    await db.commit()
    return ArchitectureNodeRead.model_validate(node)


@router.get(
    "/projects/{project_id}/architecture/nodes",
    response_model=ArchitectureNodeList,
)
async def list_nodes(
    project_id: uuid.UUID,
    node_type: NodeType | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureNodeList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    nodes, total = await architecture_service.list_nodes(
        db,
        project_id,
        node_type=node_type,
        limit=limit,
        offset=offset,
    )
    return ArchitectureNodeList(
        items=[ArchitectureNodeRead.model_validate(n) for n in nodes],
        total=total,
    )


@router.get(
    "/projects/{project_id}/architecture/nodes/{node_id}",
    response_model=ArchitectureNodeRead,
)
async def get_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureNodeRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    node = await architecture_service.get_node(db, node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
        )
    return ArchitectureNodeRead.model_validate(node)


@router.patch(
    "/projects/{project_id}/architecture/nodes/{node_id}",
    response_model=ArchitectureNodeRead,
)
async def update_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    body: ArchitectureNodeUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureNodeRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    node = await architecture_service.update_node(
        db,
        node_id,
        **body.model_dump(exclude_unset=True),
    )
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
        )
    await db.commit()
    return ArchitectureNodeRead.model_validate(node)


@router.delete(
    "/projects/{project_id}/architecture/nodes/{node_id}",
    status_code=204,
)
async def delete_node(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    ok = await architecture_service.delete_node(db, node_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
        )
    await db.commit()


# -- Edges --


@router.post(
    "/projects/{project_id}/architecture/edges",
    response_model=ArchitectureEdgeRead,
    status_code=201,
)
async def create_edge(
    project_id: uuid.UUID,
    body: ArchitectureEdgeCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureEdgeRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    edge = await architecture_service.create_edge(
        db,
        project_id=project_id,
        workspace_id=None,
        from_node_id=body.from_node_id,
        to_node_id=body.to_node_id,
        edge_type=body.edge_type,
        confidence_score=body.confidence_score,
        metadata_=body.metadata_,
        source_type=body.source_type,
    )
    await db.commit()
    return ArchitectureEdgeRead.model_validate(edge)


@router.get(
    "/projects/{project_id}/architecture/edges",
    response_model=ArchitectureEdgeList,
)
async def list_edges(
    project_id: uuid.UUID,
    edge_type: EdgeType | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureEdgeList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    edges, total = await architecture_service.list_edges(
        db,
        project_id,
        edge_type=edge_type,
        limit=limit,
        offset=offset,
    )
    return ArchitectureEdgeList(
        items=[ArchitectureEdgeRead.model_validate(e) for e in edges],
        total=total,
    )


@router.delete(
    "/projects/{project_id}/architecture/edges/{edge_id}",
    status_code=204,
)
async def delete_edge(
    project_id: uuid.UUID,
    edge_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    ok = await architecture_service.delete_edge(db, edge_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Edge not found"
        )
    await db.commit()


# -- Graph & Neighbors --


@router.get(
    "/projects/{project_id}/architecture/graph",
    response_model=ArchitectureGraphRead,
)
async def get_graph(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureGraphRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    nodes, edges = await architecture_service.get_full_graph(db, project_id)
    return ArchitectureGraphRead(
        project_id=project_id,
        nodes=[ArchitectureNodeRead.model_validate(n) for n in nodes],
        edges=[ArchitectureEdgeRead.model_validate(e) for e in edges],
        node_count=len(nodes),
        edge_count=len(edges),
    )


@router.get(
    "/projects/{project_id}/architecture/nodes/{node_id}/neighbors",
    response_model=NeighborRead,
)
async def get_neighbors(
    project_id: uuid.UUID,
    node_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> NeighborRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    node = await architecture_service.get_node(db, node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Node not found"
        )
    incoming, outgoing = await architecture_service.get_neighbors(db, node_id)
    return NeighborRead(
        node=ArchitectureNodeRead.model_validate(node),
        incoming=[ArchitectureEdgeRead.model_validate(e) for e in incoming],
        outgoing=[ArchitectureEdgeRead.model_validate(e) for e in outgoing],
    )


# -- Snapshots --


@router.post(
    "/projects/{project_id}/architecture/snapshots",
    response_model=ArchitectureSnapshotRead,
    status_code=201,
)
async def create_snapshot(
    project_id: uuid.UUID,
    name: str = Query("snapshot", min_length=1),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureSnapshotRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    snap = await architecture_service.create_snapshot(
        db, project_id=project_id, name=name
    )
    await db.commit()
    return ArchitectureSnapshotRead.model_validate(snap)


@router.get(
    "/projects/{project_id}/architecture/snapshots",
    response_model=ArchitectureSnapshotList,
)
async def list_snapshots(
    project_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureSnapshotList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await architecture_service.list_snapshots(
        db,
        project_id,
        limit=limit,
        offset=offset,
    )
    return ArchitectureSnapshotList(
        items=[ArchitectureSnapshotRead.model_validate(s) for s in items],
        total=total,
    )


# ── FM-082: Topology Mapping ────────────────────────────────────


@router.post(
    "/projects/{project_id}/architecture/topology/map",
    response_model=TopologySummary,
)
async def map_topology(
    project_id: uuid.UUID,
    body: TopologyMapRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> TopologySummary:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    summary = await topology_mapper_service.map_topology(
        db,
        project_id=project_id,
        base_path=body.base_path or ".",
        scan_python=body.scan_python,
        scan_typescript=body.scan_typescript,
    )
    await db.commit()
    return TopologySummary(**summary)


# ── FM-083: Drift Detection ─────────────────────────────────────


@router.post(
    "/projects/{project_id}/architecture/drift/detect",
    response_model=ArchitectureDriftList,
)
async def detect_drift(
    project_id: uuid.UUID,
    snapshot_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureDriftList:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    drifts = await drift_detection_service.detect_drift(
        db,
        project_id=project_id,
        snapshot_id=snapshot_id,
    )
    await db.commit()
    return ArchitectureDriftList(
        items=[ArchitectureDriftRead.model_validate(d) for d in drifts],
        total=len(drifts),
    )


@router.get(
    "/projects/{project_id}/architecture/drift",
    response_model=ArchitectureDriftList,
)
async def list_drifts(
    project_id: uuid.UUID,
    status_filter: DriftStatus | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureDriftList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await drift_detection_service.list_drifts(
        db,
        project_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return ArchitectureDriftList(
        items=[ArchitectureDriftRead.model_validate(d) for d in items],
        total=total,
    )


@router.post(
    "/projects/{project_id}/architecture/drift/{drift_id}/resolve",
    response_model=ArchitectureDriftRead,
)
async def resolve_drift(
    project_id: uuid.UUID,
    drift_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureDriftRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    drift = await drift_detection_service.resolve_drift(db, drift_id)
    if drift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Drift not found"
        )
    await db.commit()
    return ArchitectureDriftRead.model_validate(drift)


@router.post(
    "/projects/{project_id}/architecture/drift/{drift_id}/ignore",
    response_model=ArchitectureDriftRead,
)
async def ignore_drift(
    project_id: uuid.UUID,
    drift_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureDriftRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    drift = await drift_detection_service.ignore_drift(db, drift_id)
    if drift is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Drift not found"
        )
    await db.commit()
    return ArchitectureDriftRead.model_validate(drift)


# ── FM-084: Architecture Rules ──────────────────────────────────


@router.post(
    "/projects/{project_id}/architecture/rules",
    response_model=ArchitectureRuleRead,
    status_code=201,
)
async def create_rule(
    project_id: uuid.UUID,
    body: ArchitectureRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureRuleRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    rule = await architecture_rule_service.create_rule(
        db,
        project_id=project_id,
        name=body.name,
        description=body.description,
        category=body.category,
        rule_config=body.rule_config,
        enabled=body.enabled,
        severity=body.severity,
    )
    await db.commit()
    return ArchitectureRuleRead.model_validate(rule)


@router.get(
    "/projects/{project_id}/architecture/rules",
    response_model=ArchitectureRuleList,
)
async def list_rules(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureRuleList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await architecture_rule_service.list_rules(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ArchitectureRuleList(
        items=[ArchitectureRuleRead.model_validate(r) for r in items],
        total=total,
    )


@router.post(
    "/projects/{project_id}/architecture/rules/{rule_id}/evaluate",
    response_model=ArchitectureRuleResultRead,
)
async def evaluate_rule(
    project_id: uuid.UUID,
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureRuleResultRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    try:
        result = await architecture_rule_service.evaluate_rule(
            db, rule_id=rule_id, project_id=project_id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found"
        )
    await db.commit()
    return ArchitectureRuleResultRead.model_validate(result)


@router.get(
    "/projects/{project_id}/architecture/rule-results",
    response_model=ArchitectureRuleResultList,
)
async def list_rule_results(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ArchitectureRuleResultList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await architecture_rule_service.list_rule_results(
        db,
        project_id,
        limit=limit,
        offset=offset,
    )
    return ArchitectureRuleResultList(
        items=[ArchitectureRuleResultRead.model_validate(r) for r in items],
        total=total,
    )


# ── FM-086: Design Doc Synthesis ────────────────────────────────


@router.post(
    "/projects/{project_id}/architecture/design-doc",
    response_model=DesignDocRead,
)
async def generate_design_doc(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> DesignDocRead:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    doc = await design_doc_service.generate_design_doc(db, project_id=project_id)
    return DesignDocRead(**doc)


# ── FM-087: Change Impact Analysis ──────────────────────────────


@router.post(
    "/projects/{project_id}/architecture/impact-analysis",
    response_model=ChangeImpactAssessmentRead,
    status_code=201,
)
async def analyse_impact(
    project_id: uuid.UUID,
    body: ImpactAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ChangeImpactAssessmentRead:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    assessment = await impact_analysis_service.analyse_impact(
        db,
        project_id=project_id,
        node_id=body.node_id,
        file_path=body.file_path,
        module_key=body.module_key,
    )
    await db.commit()
    return ChangeImpactAssessmentRead.model_validate(assessment)


# ── FM-088: Refactor Recommendations ────────────────────────────


@router.get(
    "/projects/{project_id}/architecture/recommendations",
    response_model=RefactorRecommendationList,
)
async def get_recommendations(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> RefactorRecommendationList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    recs = await refactor_recommendation_service.generate_recommendations(
        db,
        project_id=project_id,
    )
    return RefactorRecommendationList(
        items=[RefactorRecommendation(**r) for r in recs],
        total=len(recs),
    )


# ── FM-089: Architecture Approval Workflow ──────────────────────


@router.post(
    "/projects/{project_id}/architecture/approvals",
    response_model=ApprovalRead | None,
    status_code=201,
)
async def request_architecture_approval(
    project_id: uuid.UUID,
    assessment_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalRead | None:
    await check_project_permission(
        db, project_id, user_id, Action.PROJECT_MANAGE_ARCHITECTURE
    )
    approval = await architecture_approval_service.maybe_create_approval(
        db,
        assessment_id=assessment_id,
    )
    if approval is None:
        return None
    await db.commit()
    return ApprovalRead.model_validate(approval)


@router.get(
    "/projects/{project_id}/architecture/approvals",
    response_model=ApprovalList,
)
async def list_architecture_approvals(
    project_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ApprovalList:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    items, total = await architecture_approval_service.list_architecture_approvals(
        db,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ApprovalList(
        items=[ApprovalRead.model_validate(a) for a in items],
        total=total,
    )


# ── FM-090: Structural Health Score ─────────────────────────────


@router.get(
    "/projects/{project_id}/architecture/health-score",
    response_model=StructuralHealthScore,
)
async def get_health_score(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> StructuralHealthScore:
    await check_project_permission(db, project_id, user_id, Action.PROJECT_VIEW)
    score = await structural_health_service.compute_health_score(
        db,
        project_id=project_id,
    )
    return StructuralHealthScore(**score)
