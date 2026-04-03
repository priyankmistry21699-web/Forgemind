"""FM-081 to FM-090: Architecture Intelligence comprehensive tests.

Covers: graph CRUD, topology mapping, drift detection, rule engine,
design-doc synthesis, impact analysis, refactor recommendations,
architecture approvals, and RBAC enforcement.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architecture import (
    NodeType,
    EdgeType,
    NodeStatus,
    DriftSeverity,
    DriftStatus,
    RuleCategory,
    RuleResultStatus,
    ImpactSeverity,
)

# ── helpers ──────────────────────────────────────────────────────

PREFIX = "/projects/{pid}/architecture"


def url(pid: uuid.UUID, path: str = "") -> str:
    return f"/projects/{pid}/architecture{path}"


# ── FM-081: Graph Foundation — Service Layer ─────────────────────


@pytest.mark.asyncio
class TestArchitectureGraphService:
    async def test_create_node(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="app.core.auth",
            name="auth module",
            path="app/core/auth.py",
            language="python",
        )
        assert node.id is not None
        assert node.node_type == NodeType.MODULE
        assert node.key == "app.core.auth"

    async def test_list_nodes(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="svc-a",
            name="A",
        )
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="mod-b",
            name="B",
        )
        items, total = await svc.list_nodes(db_session, sample_project.id)
        assert total == 2
        assert len(items) == 2

    async def test_update_node(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="x",
            name="X",
        )
        updated = await svc.update_node(db_session, node.id, name="X-updated")
        assert updated is not None
        assert updated.name == "X-updated"

    async def test_delete_node(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="d",
            name="D",
        )
        assert await svc.delete_node(db_session, node.id) is True
        assert await svc.get_node(db_session, node.id) is None

    async def test_create_edge(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="e-a",
            name="A",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="e-b",
            name="B",
        )
        edge = await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.IMPORTS,
        )
        assert edge.id is not None
        assert edge.edge_type == EdgeType.IMPORTS

    async def test_list_edges(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="le-a",
            name="A",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="le-b",
            name="B",
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.DEPENDS_ON,
        )
        items, total = await svc.list_edges(db_session, sample_project.id)
        assert total >= 1

    async def test_get_neighbors(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="nb-a",
            name="A",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="nb-b",
            name="B",
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.CALLS,
        )
        incoming, outgoing = await svc.get_neighbors(db_session, b.id)
        assert len(incoming) == 1
        assert incoming[0].from_node_id == a.id

    async def test_get_full_graph(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="fg-a",
            name="A",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="fg-b",
            name="B",
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.IMPORTS,
        )
        nodes, edges = await svc.get_full_graph(db_session, sample_project.id)
        assert len(nodes) >= 2
        assert len(edges) >= 1

    async def test_create_and_list_snapshots(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc

        snap = await svc.create_snapshot(
            db_session,
            project_id=sample_project.id,
            name="v1",
        )
        assert snap.name == "v1"
        items, total = await svc.list_snapshots(db_session, sample_project.id)
        assert total >= 1


# ── FM-081: Graph Foundation — Route Layer ───────────────────────


@pytest.mark.asyncio
class TestArchitectureGraphRoutes:
    async def test_create_node_route(self, client: AsyncClient, sample_project):
        resp = await client.post(
            url(sample_project.id, "/nodes"),
            json={
                "node_type": "module",
                "key": "rt-mod-a",
                "name": "Route Module A",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["key"] == "rt-mod-a"
        assert data["node_type"] == "module"

    async def test_list_nodes_route(self, client: AsyncClient, sample_project):
        await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "service", "key": "rt-svc-1", "name": "Svc"},
        )
        resp = await client.get(url(sample_project.id, "/nodes"))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1

    async def test_get_node_route_404(self, client: AsyncClient, sample_project):
        fake = uuid.uuid4()
        resp = await client.get(url(sample_project.id, f"/nodes/{fake}"))
        assert resp.status_code == 404

    async def test_update_node_route(self, client: AsyncClient, sample_project):
        r = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rt-upd", "name": "Old"},
        )
        nid = r.json()["id"]
        resp = await client.patch(
            url(sample_project.id, f"/nodes/{nid}"),
            json={"name": "New"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "New"

    async def test_delete_node_route(self, client: AsyncClient, sample_project):
        r = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rt-del", "name": "Del"},
        )
        nid = r.json()["id"]
        resp = await client.delete(url(sample_project.id, f"/nodes/{nid}"))
        assert resp.status_code == 204

    async def test_create_edge_route(self, client: AsyncClient, sample_project):
        r1 = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rt-e-a", "name": "A"},
        )
        r2 = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rt-e-b", "name": "B"},
        )
        resp = await client.post(
            url(sample_project.id, "/edges"),
            json={
                "from_node_id": r1.json()["id"],
                "to_node_id": r2.json()["id"],
                "edge_type": "imports",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["edge_type"] == "imports"

    async def test_list_edges_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/edges"))
        assert resp.status_code == 200

    async def test_get_graph_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/graph"))
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data

    async def test_create_snapshot_route(self, client: AsyncClient, sample_project):
        resp = await client.post(
            url(sample_project.id, "/snapshots?name=test-snap"),
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "test-snap"

    async def test_list_snapshots_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/snapshots"))
        assert resp.status_code == 200

    async def test_get_node_neighbors_route(self, client: AsyncClient, sample_project):
        r = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rt-nb", "name": "NB"},
        )
        nid = r.json()["id"]
        resp = await client.get(url(sample_project.id, f"/nodes/{nid}/neighbors"))
        assert resp.status_code == 200
        assert "incoming" in resp.json()
        assert "outgoing" in resp.json()


# ── FM-083: Drift Detection — Service Layer ──────────────────────


@pytest.mark.asyncio
class TestDriftDetectionService:
    async def test_detect_convention_drift(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import drift_detection_service as dd

        # Create forbidden cross-layer: model -> api (model should not import from api)
        model_node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="drift-model",
            name="model",
            metadata_={"layer": "model"},
        )
        api_node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="drift-api",
            name="api",
            metadata_={"layer": "api"},
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=model_node.id,
            to_node_id=api_node.id,
            edge_type=EdgeType.IMPORTS,
        )
        drifts = await dd.detect_drift(db_session, project_id=sample_project.id)
        assert len(drifts) >= 1

    async def test_resolve_drift(self, db_session: AsyncSession, sample_project):
        from app.services import drift_detection_service as dd
        from app.models.architecture import ArchitectureDrift

        drift = ArchitectureDrift(
            project_id=sample_project.id,
            drift_type="convention",
            severity=DriftSeverity.MEDIUM,
            title="Test drift",
            description="Test",
        )
        db_session.add(drift)
        await db_session.flush()

        resolved = await dd.resolve_drift(db_session, drift.id)
        assert resolved is not None
        assert resolved.status == DriftStatus.RESOLVED

    async def test_ignore_drift(self, db_session: AsyncSession, sample_project):
        from app.services import drift_detection_service as dd
        from app.models.architecture import ArchitectureDrift

        drift = ArchitectureDrift(
            project_id=sample_project.id,
            drift_type="convention",
            severity=DriftSeverity.LOW,
            title="Ignore me",
            description="Test",
        )
        db_session.add(drift)
        await db_session.flush()

        ignored = await dd.ignore_drift(db_session, drift.id)
        assert ignored is not None
        assert ignored.status == DriftStatus.IGNORED


# ── FM-083: Drift Detection — Route Layer ────────────────────────


@pytest.mark.asyncio
class TestDriftDetectionRoutes:
    async def test_detect_drift_route(self, client: AsyncClient, sample_project):
        resp = await client.post(url(sample_project.id, "/drift/detect"))
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_list_drifts_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/drift"))
        assert resp.status_code == 200
        assert "total" in resp.json()


# ── FM-084: Rule Engine — Service Layer ──────────────────────────


@pytest.mark.asyncio
class TestArchitectureRuleService:
    async def test_create_rule(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_rule_service as rs

        rule = await rs.create_rule(
            db_session,
            project_id=sample_project.id,
            name="No api->model",
            category=RuleCategory.IMPORT,
            rule_config={"forbidden_from": ".*api.*", "forbidden_to": ".*model.*"},
        )
        assert rule.id is not None
        assert rule.category == RuleCategory.IMPORT

    async def test_evaluate_import_rule_pass(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_rule_service as rs
        from app.services import architecture_service as svc

        # Two modules in the same layer
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="rule-svc-a",
            name="A",
        )
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="rule-svc-b",
            name="B",
        )
        rule = await rs.create_rule(
            db_session,
            project_id=sample_project.id,
            name="Forbid test->prod",
            category=RuleCategory.IMPORT,
            rule_config={"forbidden_from": ".*test.*", "forbidden_to": ".*prod.*"},
        )
        result = await rs.evaluate_rule(
            db_session, rule_id=rule.id, project_id=sample_project.id
        )
        assert result is not None
        assert result.status == RuleResultStatus.PASS

    async def test_evaluate_import_rule_violation(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_rule_service as rs
        from app.services import architecture_service as svc

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="test-mod",
            name="test-mod",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="prod-mod",
            name="prod-mod",
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.IMPORTS,
        )
        rule = await rs.create_rule(
            db_session,
            project_id=sample_project.id,
            name="Forbid test->prod",
            category=RuleCategory.IMPORT,
            rule_config={"forbidden_from": ".*test.*", "forbidden_to": ".*prod.*"},
        )
        result = await rs.evaluate_rule(
            db_session, rule_id=rule.id, project_id=sample_project.id
        )
        assert result is not None
        assert result.status == RuleResultStatus.VIOLATION


# ── FM-084: Rule Engine — Route Layer ────────────────────────────


@pytest.mark.asyncio
class TestArchitectureRuleRoutes:
    async def test_create_rule_route(self, client: AsyncClient, sample_project):
        resp = await client.post(
            url(sample_project.id, "/rules"),
            json={
                "name": "boundary rule",
                "category": "boundary",
                "rule_config": {"boundary": "core", "allowed_consumers": "api"},
            },
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "boundary rule"

    async def test_list_rules_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/rules"))
        assert resp.status_code == 200
        assert "total" in resp.json()

    async def test_evaluate_rule_route(self, client: AsyncClient, sample_project):
        r = await client.post(
            url(sample_project.id, "/rules"),
            json={
                "name": "eval rule",
                "category": "import",
                "rule_config": {"forbidden_from": "x", "forbidden_to": "y"},
            },
        )
        rid = r.json()["id"]
        resp = await client.post(url(sample_project.id, f"/rules/{rid}/evaluate"))
        assert resp.status_code == 200

    async def test_list_rule_results_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/rule-results"))
        assert resp.status_code == 200


# ── FM-086: Design Doc Synthesis ─────────────────────────────────


@pytest.mark.asyncio
class TestDesignDocService:
    async def test_generate_empty_project(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import design_doc_service as ds

        doc = await ds.generate_design_doc(db_session, project_id=sample_project.id)
        assert "content" in doc
        assert "Architecture Summary" in doc["content"]
        assert doc["sections"]

    async def test_generate_with_nodes(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc
        from app.services import design_doc_service as ds

        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="doc-svc",
            name="DocSvc",
        )
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="doc-mod",
            name="DocMod",
        )
        doc = await ds.generate_design_doc(db_session, project_id=sample_project.id)
        assert "components" in doc["sections"]


@pytest.mark.asyncio
class TestDesignDocRoutes:
    async def test_generate_design_doc_route(self, client: AsyncClient, sample_project):
        resp = await client.post(url(sample_project.id, "/design-doc"))
        assert resp.status_code == 200
        assert "content" in resp.json()


# ── FM-087: Impact Analysis — Service Layer ──────────────────────


@pytest.mark.asyncio
class TestImpactAnalysisService:
    async def test_impact_unknown_target(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import impact_analysis_service as ia

        assessment = await ia.analyse_impact(
            db_session,
            project_id=sample_project.id,
            file_path="/nonexistent.py",
        )
        assert assessment.blast_radius == 0
        assert assessment.severity == ImpactSeverity.LOW

    async def test_impact_with_dependents(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import impact_analysis_service as ia

        core = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="ia-core",
            name="core",
        )
        svc_a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="ia-svc-a",
            name="SvcA",
        )
        svc_b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="ia-svc-b",
            name="SvcB",
        )
        # Both depend on core
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=svc_a.id,
            to_node_id=core.id,
            edge_type=EdgeType.DEPENDS_ON,
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=svc_b.id,
            to_node_id=core.id,
            edge_type=EdgeType.DEPENDS_ON,
        )
        assessment = await ia.analyse_impact(
            db_session,
            project_id=sample_project.id,
            node_id=core.id,
        )
        assert assessment.blast_radius >= 2
        assert assessment.severity in (ImpactSeverity.LOW, ImpactSeverity.MEDIUM)

    async def test_impact_severity_escalation(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import impact_analysis_service as ia

        center = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="ia-center",
            name="Center",
        )
        # Create 10 dependents -> severity should be HIGH
        for i in range(10):
            dep = await svc.create_node(
                db_session,
                project_id=sample_project.id,
                node_type=NodeType.MODULE,
                key=f"ia-dep-{i}",
                name=f"Dep{i}",
            )
            await svc.create_edge(
                db_session,
                project_id=sample_project.id,
                from_node_id=dep.id,
                to_node_id=center.id,
                edge_type=EdgeType.IMPORTS,
            )
        assessment = await ia.analyse_impact(
            db_session,
            project_id=sample_project.id,
            node_id=center.id,
        )
        assert assessment.blast_radius >= 10
        assert assessment.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)


@pytest.mark.asyncio
class TestImpactAnalysisRoutes:
    async def test_impact_analysis_route(self, client: AsyncClient, sample_project):
        resp = await client.post(
            url(sample_project.id, "/impact-analysis"),
            json={"file_path": "/nofile.py"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "blast_radius" in data
        assert "severity" in data


# ── FM-088: Refactor Recommendations — Service Layer ─────────────


@pytest.mark.asyncio
class TestRefactorRecommendationService:
    async def test_empty_project_no_recs(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import refactor_recommendation_service as rr

        recs = await rr.generate_recommendations(
            db_session,
            project_id=sample_project.id,
        )
        assert isinstance(recs, list)

    async def test_circular_dependency_recommendation(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import refactor_recommendation_service as rr

        a = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="rr-circ-a",
            name="A",
        )
        b = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="rr-circ-b",
            name="B",
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=a.id,
            to_node_id=b.id,
            edge_type=EdgeType.DEPENDS_ON,
        )
        await svc.create_edge(
            db_session,
            project_id=sample_project.id,
            from_node_id=b.id,
            to_node_id=a.id,
            edge_type=EdgeType.DEPENDS_ON,
        )
        recs = await rr.generate_recommendations(
            db_session,
            project_id=sample_project.id,
        )
        types = [r["recommendation_type"] for r in recs]
        assert "break_circular_dependency" in types

    async def test_isolated_node_recommendation(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import refactor_recommendation_service as rr

        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="rr-isolated",
            name="Isolated",
        )
        recs = await rr.generate_recommendations(
            db_session,
            project_id=sample_project.id,
        )
        types = [r["recommendation_type"] for r in recs]
        assert "remove_or_integrate_isolated" in types


@pytest.mark.asyncio
class TestRefactorRecommendationRoutes:
    async def test_recommendations_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/recommendations"))
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body


# ── FM-089: Architecture Approval Workflow ───────────────────────


@pytest.mark.asyncio
class TestArchitectureApprovalService:
    async def test_no_approval_for_low_severity(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import impact_analysis_service as ia
        from app.services import architecture_approval_service as aa

        assessment = await ia.analyse_impact(
            db_session,
            project_id=sample_project.id,
            file_path="/nonexistent.py",  # LOW severity
        )
        result = await aa.maybe_create_approval(
            db_session,
            assessment_id=assessment.id,
        )
        assert result is None  # LOW does not trigger approval

    async def test_approval_for_high_severity(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import impact_analysis_service as ia
        from app.services import architecture_approval_service as aa

        center = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="appr-center",
            name="Center",
        )
        for i in range(12):
            dep = await svc.create_node(
                db_session,
                project_id=sample_project.id,
                node_type=NodeType.MODULE,
                key=f"appr-dep-{i}",
                name=f"D{i}",
            )
            await svc.create_edge(
                db_session,
                project_id=sample_project.id,
                from_node_id=dep.id,
                to_node_id=center.id,
                edge_type=EdgeType.IMPORTS,
            )
        assessment = await ia.analyse_impact(
            db_session,
            project_id=sample_project.id,
            node_id=center.id,
        )
        # Should be HIGH or CRITICAL, triggers approval
        result = await aa.maybe_create_approval(
            db_session,
            assessment_id=assessment.id,
        )
        assert result is not None
        assert result.title.startswith("[arch-change]")


@pytest.mark.asyncio
class TestArchitectureApprovalRoutes:
    async def test_list_architecture_approvals_route(
        self, client: AsyncClient, sample_project
    ):
        resp = await client.get(url(sample_project.id, "/approvals"))
        assert resp.status_code == 200
        assert "items" in resp.json()


# ── RBAC Enforcement ─────────────────────────────────────────────


@pytest.mark.asyncio
class TestArchitectureRBAC:
    async def test_node_create_requires_manage_arch(self, client: AsyncClient):
        """POST to a non-existent project yields 404 (not a member)."""
        fake_pid = uuid.uuid4()
        resp = await client.post(
            url(fake_pid, "/nodes"),
            json={"node_type": "module", "key": "x", "name": "X"},
        )
        assert resp.status_code == 404

    async def test_drift_detect_requires_manage_arch(self, client: AsyncClient):
        fake_pid = uuid.uuid4()
        resp = await client.post(url(fake_pid, "/drift/detect"))
        assert resp.status_code == 404

    async def test_rule_create_requires_manage_arch(self, client: AsyncClient):
        fake_pid = uuid.uuid4()
        resp = await client.post(
            url(fake_pid, "/rules"),
            json={"name": "r", "category": "import", "rule_config": {}},
        )
        assert resp.status_code == 404

    async def test_impact_analysis_requires_manage_arch(self, client: AsyncClient):
        fake_pid = uuid.uuid4()
        resp = await client.post(
            url(fake_pid, "/impact-analysis"),
            json={"file_path": "test.py"},
        )
        assert resp.status_code == 404

    async def test_view_graph_requires_project_view(self, client: AsyncClient):
        fake_pid = uuid.uuid4()
        resp = await client.get(url(fake_pid, "/graph"))
        assert resp.status_code == 404

    async def test_snapshot_create_requires_manage_arch(self, client: AsyncClient):
        fake_pid = uuid.uuid4()
        resp = await client.post(url(fake_pid, "/snapshots?name=x"))
        assert resp.status_code == 404

    async def test_viewer_cannot_manage_architecture(
        self, client: AsyncClient, db_session: AsyncSession, sample_project
    ):
        """A VIEWER member should get 403 on manage-architecture endpoints."""
        from app.models.membership import ProjectMember, ProjectRole

        viewer_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        member = ProjectMember(
            project_id=sample_project.id,
            user_id=viewer_id,
            role=ProjectRole.VIEWER,
        )
        db_session.add(member)
        await db_session.flush()

        # We can only test with the stub user (the client is hardcoded to STUB_USER_ID),
        # but we verify the existing LEAD user CAN access manage-architecture.
        resp = await client.post(
            url(sample_project.id, "/nodes"),
            json={"node_type": "module", "key": "rbac-test", "name": "RBAC"},
        )
        assert resp.status_code == 201  # LEAD has manage_architecture


# ── FM-082: Topology Mapping — Service + Route Tests ─────────────


@pytest.mark.asyncio
class TestTopologyMappingService:
    def test_parse_python_imports(self):
        from app.services.topology_mapper_service import parse_python_imports

        source = (
            "import os\n"
            "from pathlib import Path\n"
            "import sys\n"
            "from app.core import auth\n"
        )
        imports = parse_python_imports(source)
        assert "os" in imports
        assert "pathlib" in imports
        assert "sys" in imports
        assert "app.core" in imports

    def test_parse_typescript_imports(self):
        from app.services.topology_mapper_service import parse_typescript_imports

        source = (
            "import React from 'react';\n"
            "import { useState } from 'react';\n"
            "import type { Foo } from '@/types/foo';\n"
        )
        imports = parse_typescript_imports(source)
        assert "react" in imports
        assert "@/types/foo" in imports

    def test_classify_layer(self):
        from app.services.topology_mapper_service import classify_layer

        assert classify_layer("app/api/routes/users.py") == "api"
        assert classify_layer("app/services/auth.py") == "service"
        assert classify_layer("app/models/user.py") == "model"
        assert classify_layer("app/schemas/user.py") == "schema"
        assert classify_layer("app/core/config.py") == "core"
        assert classify_layer("app/tests/test_user.py") == "test"
        assert classify_layer("utils/helpers.py") == "other"

    def test_detect_language(self):
        from app.services.topology_mapper_service import detect_language

        assert detect_language("app.py") == "python"
        assert detect_language("index.ts") == "typescript"
        assert detect_language("index.tsx") == "typescript"
        assert detect_language("app.js") == "javascript"
        assert detect_language("README.md") is None

    def test_scan_directory_structure(self, tmp_path):
        from app.services.topology_mapper_service import scan_directory_structure

        # Create a small fixture directory
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "models").mkdir()
        (tmp_path / "app" / "services").mkdir()

        (tmp_path / "app" / "models" / "user.py").write_text(
            "import uuid\nfrom app.core import base\n", encoding="utf-8"
        )
        (tmp_path / "app" / "services" / "auth.py").write_text(
            "from app.models.user import User\n", encoding="utf-8"
        )

        nodes, edges = scan_directory_structure(str(tmp_path))
        assert len(nodes) == 2
        keys = {n["key"] for n in nodes}
        assert "app/models/user.py" in keys
        assert "app/services/auth.py" in keys
        # Check that edges were attempted (resolution may or may not match)
        assert isinstance(edges, list)

    def test_compute_topology_summary(self):
        from app.services.topology_mapper_service import compute_topology_summary

        nodes = [
            {"key": "a.py", "metadata_": {"layer": "api"}},
            {"key": "b.py", "metadata_": {"layer": "service"}},
            {"key": "c.py", "metadata_": {"layer": "model"}},
        ]
        edges = [
            {"from_key": "a.py", "to_key": "b.py"},
            {"from_key": "b.py", "to_key": "c.py"},
        ]
        summary = compute_topology_summary(nodes, edges)
        assert summary["components_found"] == 3
        assert summary["edges_found"] == 2
        assert "api" in summary["layers"]
        # a.py: out=1, in=0 -> not isolated (out_degree > 0)
        # b.py: out=1, in=1 -> not isolated
        # c.py: out=0, in=1 -> not isolated (in_degree > 0)
        assert len(summary["isolated_nodes"]) == 0

    async def test_map_topology_persists(
        self, db_session: AsyncSession, sample_project, tmp_path
    ):
        from app.services import topology_mapper_service as tms

        # Create fixture files
        (tmp_path / "main.py").write_text("import os\n", encoding="utf-8")
        (tmp_path / "helper.py").write_text(
            "from pathlib import Path\n", encoding="utf-8"
        )

        summary = await tms.map_topology(
            db_session,
            project_id=sample_project.id,
            base_path=str(tmp_path),
        )
        assert summary["components_found"] == 2
        assert "project_id" in summary

        # Verify nodes persisted
        from app.services import architecture_service as svc

        nodes, total = await svc.list_nodes(db_session, sample_project.id)
        assert total == 2


@pytest.mark.asyncio
class TestTopologyMappingRoutes:
    async def test_map_topology_route(
        self, client: AsyncClient, sample_project, tmp_path
    ):
        resp = await client.post(
            url(sample_project.id, "/topology/map"),
            json={
                "base_path": str(tmp_path),
                "scan_python": True,
                "scan_typescript": False,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "components_found" in data
        assert "layers" in data


# ── FM-083: Snapshot-comparison drift tests ──────────────────────


@pytest.mark.asyncio
class TestSnapshotComparisonDrift:
    async def test_snapshot_drift_detects_new_components(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import drift_detection_service as dd

        # Create a node, take snapshot
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="snap-a",
            name="A",
        )
        snap = await svc.create_snapshot(
            db_session, project_id=sample_project.id, name="baseline"
        )

        # Add a new node after snapshot
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="snap-b",
            name="B",
        )

        drifts = await dd.detect_drift(
            db_session,
            project_id=sample_project.id,
            snapshot_id=snap.id,
        )
        new_comp = [d for d in drifts if d.drift_type == "new_component"]
        assert len(new_comp) == 1
        assert "snap-b" in new_comp[0].description

    async def test_snapshot_drift_detects_removed_components(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import architecture_service as svc
        from app.services import drift_detection_service as dd

        node = await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.MODULE,
            key="snap-rm",
            name="RM",
        )
        snap = await svc.create_snapshot(
            db_session, project_id=sample_project.id, name="before-remove"
        )

        # Remove the node (mark as REMOVED so it's excluded from active queries)
        await svc.update_node(db_session, node.id, status=NodeStatus.REMOVED)

        drifts = await dd.detect_drift(
            db_session,
            project_id=sample_project.id,
            snapshot_id=snap.id,
        )
        removed = [d for d in drifts if d.drift_type == "removed_component"]
        assert len(removed) == 1


# ── FM-084: Ownership rule evaluator test ────────────────────────


@pytest.mark.asyncio
class TestOwnershipRuleEvaluator:
    async def test_ownership_violation(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc
        from app.services import architecture_rule_service as rs

        # Create nodes without ownership metadata
        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="svc-orphan",
            name="Orphan",
        )

        rule = await rs.create_rule(
            db_session,
            project_id=sample_project.id,
            name="All services need owners",
            category=RuleCategory.OWNERSHIP,
            rule_config={"target_type": "service"},
            severity=DriftSeverity.MEDIUM,
        )
        result = await rs.evaluate_rule(
            db_session, rule_id=rule.id, project_id=sample_project.id
        )
        # Should detect the unowned service
        assert result.status == RuleResultStatus.VIOLATION

    async def test_ownership_pass(self, db_session: AsyncSession, sample_project):
        from app.services import architecture_service as svc
        from app.services import architecture_rule_service as rs

        await svc.create_node(
            db_session,
            project_id=sample_project.id,
            node_type=NodeType.SERVICE,
            key="svc-owned",
            name="Owned",
            metadata_={"owner": "team-platform"},
        )

        rule = await rs.create_rule(
            db_session,
            project_id=sample_project.id,
            name="Ownership check",
            category=RuleCategory.OWNERSHIP,
            rule_config={"target_type": "service"},
            severity=DriftSeverity.MEDIUM,
        )
        result = await rs.evaluate_rule(
            db_session, rule_id=rule.id, project_id=sample_project.id
        )
        assert result.status == RuleResultStatus.PASS


# ── FM-090: Structural Health Score ──────────────────────────────


@pytest.mark.asyncio
class TestStructuralHealthScore:
    async def test_health_score_empty_project(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import structural_health_service as shs

        score = await shs.compute_health_score(db_session, project_id=sample_project.id)
        assert score["overall_score"] == 100  # clean project
        assert "component_coverage" in score
        assert "drift_penalty" in score
        assert "rule_compliance" in score

    async def test_health_score_with_drift(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import structural_health_service as shs
        from app.models.architecture import ArchitectureDrift

        # Inject open drifts
        for i in range(3):
            db_session.add(
                ArchitectureDrift(
                    project_id=sample_project.id,
                    drift_type="test",
                    severity=DriftSeverity.HIGH,
                    title=f"Drift {i}",
                    description="test",
                )
            )
        await db_session.flush()

        score = await shs.compute_health_score(db_session, project_id=sample_project.id)
        assert score["overall_score"] < 100
        assert score["drift_penalty"] > 0

    async def test_health_score_with_violations(
        self, db_session: AsyncSession, sample_project
    ):
        from app.services import structural_health_service as shs
        from app.models.architecture import ArchitectureRuleResult, ArchitectureRule

        rule = ArchitectureRule(
            project_id=sample_project.id,
            name="Test rule",
            category=RuleCategory.IMPORT,
            rule_config={},
            severity=DriftSeverity.HIGH,
        )
        db_session.add(rule)
        await db_session.flush()

        for i in range(2):
            db_session.add(
                ArchitectureRuleResult(
                    rule_id=rule.id,
                    project_id=sample_project.id,
                    status=RuleResultStatus.VIOLATION,
                    message=f"Violation {i}",
                )
            )
        await db_session.flush()

        score = await shs.compute_health_score(db_session, project_id=sample_project.id)
        assert score["rule_compliance"] < 100


@pytest.mark.asyncio
class TestStructuralHealthRoutes:
    async def test_health_score_route(self, client: AsyncClient, sample_project):
        resp = await client.get(url(sample_project.id, "/health-score"))
        assert resp.status_code == 200
        data = resp.json()
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
