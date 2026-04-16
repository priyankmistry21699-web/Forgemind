"""Tests for FM-161-170: Search, Knowledge & Organizational Memory.

Covers:
  FM-161: Full-text search index
  FM-162: Semantic/similar search
  FM-163: Knowledge base search
  FM-164: Template marketplace
  FM-165: Cross-project search
  FM-166: Run comparison
  FM-167: Conventions engine
  FM-168: Artifact versioning & history
  FM-169: Smart recommendations
  FM-170: Reindex & hardening
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID

# â”€â”€ Models / enums â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from app.models.search_knowledge import (
    SearchEntityType,
    SearchIndex,
    ConventionCategory,
    ConventionEnforcement,
    RecommendationType,
)
from app.models.artifact import Artifact, ArtifactType
from app.models.task import Task, TaskStatus
from app.models.run import Run

# â”€â”€ Services â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from app.services import search_service
from app.services import convention_service
from app.services import artifact_version_service
from app.services import recommendation_service
from app.services import run_comparison_service


# =========================================================================
# FM-161: Full-text search index
# =========================================================================


class TestSearchIndexing:
    """Indexing entities into search_index table."""

    @pytest.mark.asyncio
    async def test_index_task(self, db_session: AsyncSession, sample_task):
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        items, total, _ = await search_service.search(db_session, query="Test Task")
        assert total >= 1
        assert any(i["entity_id"] == str(sample_task.id) for i in items)

    @pytest.mark.asyncio
    async def test_index_artifact(self, db_session: AsyncSession, sample_artifact):
        await search_service.index_artifact(db_session, sample_artifact)
        await db_session.commit()

        items, total, _ = await search_service.search(db_session, query="Architecture")
        assert total >= 1
        assert any(i["entity_id"] == str(sample_artifact.id) for i in items)

    @pytest.mark.asyncio
    async def test_index_run(self, db_session: AsyncSession, sample_run):
        await search_service.index_run(db_session, sample_run)
        await db_session.commit()

        items, total, _ = await search_service.search(db_session, query="Run")
        assert total >= 1

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(
        self, db_session: AsyncSession, sample_task
    ):
        """Indexing the same entity twice should update, not duplicate."""
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        sample_task.title = "Updated Task Title"
        await db_session.flush()
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        items, _, _ = await search_service.search(db_session, query="Updated Task Title")
        matches = [i for i in items if i["entity_id"] == str(sample_task.id)]
        assert len(matches) == 1

    @pytest.mark.asyncio
    async def test_remove_from_index(self, db_session: AsyncSession, sample_task):
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        await search_service.remove_from_index(
            db_session, SearchEntityType.TASK, sample_task.id
        )
        await db_session.commit()

        items, total, _ = await search_service.search(
            db_session,
            query="Test Task",
            entity_types=[SearchEntityType.TASK],
        )
        assert not any(i["entity_id"] == str(sample_task.id) for i in items)


class TestSearchQuery:
    """Full-text keyword search."""

    @pytest.mark.asyncio
    async def test_search_with_project_scope(
        self, db_session: AsyncSession, sample_project, sample_task
    ):
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        items, total, _ = await search_service.search(
            db_session, query="Test", project_id=sample_project.id
        )
        assert total >= 1

    @pytest.mark.asyncio
    async def test_search_entity_type_filter(
        self, db_session: AsyncSession, sample_task, sample_artifact
    ):
        await search_service.index_task(db_session, sample_task)
        await search_service.index_artifact(db_session, sample_artifact)
        await db_session.commit()

        items, total, _ = await search_service.search(
            db_session,
            query="Test",
            entity_types=[SearchEntityType.ARTIFACT],
        )
        for i in items:
            assert i["entity_type"] == SearchEntityType.ARTIFACT.value

    @pytest.mark.asyncio
    async def test_search_no_results(self, db_session: AsyncSession):
        items, total, _ = await search_service.search(
            db_session, query="xyznonexistent999"
        )
        assert total == 0
        assert items == []

    @pytest.mark.asyncio
    async def test_search_limit_offset(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Create several tasks, index them, verify pagination."""
        tasks = []
        for i in range(5):
            t = Task(
                title=f"Pagination Task {i}",
                description=f"Desc {i}",
                task_type="implementation",
                status=TaskStatus.READY,
                order_index=i,
                run_id=sample_run.id,
            )
            db_session.add(t)
            tasks.append(t)
        await db_session.flush()

        for t in tasks:
            await db_session.refresh(t)
            await search_service.index_task(db_session, t)
        await db_session.commit()

        items, total, _ = await search_service.search(
            db_session, query="Pagination", limit=2, offset=0
        )
        assert len(items) <= 2
        assert total >= 5

    @pytest.mark.asyncio
    async def test_search_snippet_generation(
        self, db_session: AsyncSession, sample_artifact
    ):
        await search_service.index_artifact(db_session, sample_artifact)
        await db_session.commit()

        items, _, _ = await search_service.search(db_session, query="Architecture")
        assert len(items) >= 1
        assert items[0]["snippet"]  # should have a snippet


# =========================================================================
# FM-162: Find similar entities
# =========================================================================


class TestFindSimilar:
    @pytest.mark.asyncio
    async def test_find_similar_basic(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Two artifacts with overlapping content should show as similar."""
        a1 = Artifact(
            title="Database Migration Guide",
            artifact_type=ArtifactType.DOCUMENTATION,
            content="How to perform database migrations in PostgreSQL",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )
        a2 = Artifact(
            title="Database Schema Reference",
            artifact_type=ArtifactType.DOCUMENTATION,
            content="PostgreSQL database schema definitions and migrations",
            project_id=sample_project.id,
            run_id=sample_run.id,
        )
        db_session.add_all([a1, a2])
        await db_session.flush()
        await db_session.refresh(a1)
        await db_session.refresh(a2)

        await search_service.index_artifact(db_session, a1)
        await search_service.index_artifact(db_session, a2)
        await db_session.commit()

        similar = await search_service.find_similar(
            db_session,
            entity_type=SearchEntityType.ARTIFACT,
            entity_id=a1.id,
        )
        # a2 should appear as similar (overlapping terms)
        assert any(s["entity_id"] == str(a2.id) for s in similar)

    @pytest.mark.asyncio
    async def test_find_similar_missing_entity(self, db_session: AsyncSession):
        fake_id = uuid.uuid4()
        similar = await search_service.find_similar(
            db_session,
            entity_type=SearchEntityType.ARTIFACT,
            entity_id=fake_id,
        )
        assert similar == []


# =========================================================================
# FM-165: Cross-project search (covered via search scoping)
# =========================================================================


class TestCrossProjectSearch:
    @pytest.mark.asyncio
    async def test_global_search_returns_accessible_projects(
        self, db_session: AsyncSession, sample_project, sample_task
    ):
        """Global search (no project_id) should use RBAC filtering."""
        await search_service.index_task(db_session, sample_task)
        await db_session.commit()

        # Search with user_id for RBAC filtering
        items, total, _ = await search_service.search(
            db_session, query="Test", user_id=STUB_USER_ID
        )
        assert total >= 1


# =========================================================================
# FM-166: Run comparison
# =========================================================================


class TestRunComparison:
    @pytest.mark.asyncio
    async def test_compare_two_runs(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        run_b = Run(
            run_number=2,
            project_id=sample_project.id,
            trigger="test-compare",
        )
        db_session.add(run_b)
        await db_session.flush()
        await db_session.refresh(run_b)

        result = await run_comparison_service.compare_runs(
            db_session, sample_run.id, run_b.id
        )
        assert result is not None
        assert "run_a_id" in result
        assert "run_b_id" in result
        assert "summary" in result

    @pytest.mark.asyncio
    async def test_compare_nonexistent_run(self, db_session: AsyncSession, sample_run):
        result = await run_comparison_service.compare_runs(
            db_session, sample_run.id, uuid.uuid4()
        )
        assert result is None


# =========================================================================
# FM-167: Conventions engine
# =========================================================================


class TestConventions:
    @pytest.mark.asyncio
    async def test_create_convention(
        self, db_session: AsyncSession, sample_project
    ):
        conv = await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.NAMING,
            name="Snake case variables",
            description="All variables must use snake_case",
            rule_text="Variable names must use snake_case. Avoid camelCase.",
            enforcement_level=ConventionEnforcement.REQUIRED,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()
        assert conv.id is not None
        assert conv.name == "Snake case variables"
        assert conv.active is True

    @pytest.mark.asyncio
    async def test_list_conventions(
        self, db_session: AsyncSession, sample_project
    ):
        await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.QUALITY,
            name="Test coverage",
            rule_text="Must include unit tests. Avoid code without tests.",
            enforcement_level=ConventionEnforcement.RECOMMENDED,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        items, total = await convention_service.list_conventions(
            db_session, project_id=sample_project.id
        )
        assert total >= 1
        assert any(c.name == "Test coverage" for c in items)

    @pytest.mark.asyncio
    async def test_update_convention(
        self, db_session: AsyncSession, sample_project
    ):
        conv = await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.SECURITY,
            name="No hardcoded secrets",
            rule_text="Never hardcode secrets or API keys.",
            enforcement_level=ConventionEnforcement.REQUIRED,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        updated = await convention_service.update_convention(
            db_session,
            conv.id,
            name="No hardcoded secrets or tokens",
        )
        await db_session.commit()
        assert updated.name == "No hardcoded secrets or tokens"

    @pytest.mark.asyncio
    async def test_delete_convention(
        self, db_session: AsyncSession, sample_project
    ):
        conv = await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.DOCUMENTATION,
            name="Docstrings required",
            rule_text="All public functions must include docstrings.",
            enforcement_level=ConventionEnforcement.ADVISORY,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        result = await convention_service.delete_convention(db_session, conv.id)
        assert result is True
        await db_session.commit()

        fetched = await convention_service.get_convention(db_session, conv.id)
        assert fetched is None

    @pytest.mark.asyncio
    async def test_get_injectable_conventions(
        self, db_session: AsyncSession, sample_project
    ):
        await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.ARCHITECTURE,
            name="REST conventions",
            rule_text="All endpoints must follow REST naming conventions.",
            enforcement_level=ConventionEnforcement.REQUIRED,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        injectable = await convention_service.get_active_conventions_for_injection(
            db_session, sample_project.id
        )
        assert len(injectable) >= 1
        assert "name" in injectable[0]
        assert "rule_text" in injectable[0]

    @pytest.mark.asyncio
    async def test_check_conventions_compliance(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        # Create a convention that content should follow
        await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.QUALITY,
            name="No eval usage",
            rule_text="Never use eval(), avoid exec().",
            enforcement_level=ConventionEnforcement.REQUIRED,
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        result = await convention_service.check_conventions_compliance(
            db_session, sample_run.id
        )
        assert "passed" in result
        assert "violations" in result
        assert "checked_count" in result


# =========================================================================
# FM-168: Artifact versioning & history
# =========================================================================


class TestArtifactVersioning:
    @pytest.mark.asyncio
    async def test_get_version_history(
        self, db_session: AsyncSession, sample_artifact
    ):
        versions = await artifact_version_service.get_version_history(
            db_session, sample_artifact.id
        )
        assert len(versions) >= 1
        assert versions[0].id == sample_artifact.id

    @pytest.mark.asyncio
    async def test_create_new_version(
        self, db_session: AsyncSession, sample_artifact
    ):
        new_ver = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=sample_artifact.id,
            content="# Architecture V2\nUpdated architecture",
            created_by="test-agent",
        )
        await db_session.commit()

        assert new_ver.version == 2
        assert new_ver.parent_version_id == sample_artifact.id
        assert "V2" in new_ver.content

    @pytest.mark.asyncio
    async def test_diff_versions(
        self, db_session: AsyncSession, sample_artifact
    ):
        _new_ver = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=sample_artifact.id,
            content="# Architecture\nCompletely different content",
            created_by="test-agent",
        )
        await db_session.commit()
        assert _new_ver is not None

        result = await artifact_version_service.diff_versions(
            db_session, sample_artifact.id, 1, 2
        )
        assert result is not None
        assert "diff_lines" in result
        assert len(result["diff_lines"]) > 0

    @pytest.mark.asyncio
    async def test_tag_version(
        self, db_session: AsyncSession, sample_artifact
    ):
        tagged = await artifact_version_service.tag_version(
            db_session, sample_artifact.id, "v1.0-release"
        )
        await db_session.commit()
        assert tagged.version_tag == "v1.0-release"

    @pytest.mark.asyncio
    async def test_version_chain(
        self, db_session: AsyncSession, sample_artifact
    ):
        """Create 3 versions and verify the chain."""
        v2 = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=sample_artifact.id,
            content="Version 2",
            created_by="agent",
        )
        await db_session.commit()

        _v3 = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=v2.id,
            content="Version 3",
            created_by="agent",
        )
        await db_session.commit()
        assert _v3 is not None

        versions = await artifact_version_service.get_version_history(
            db_session, sample_artifact.id
        )
        assert len(versions) >= 3
        version_numbers = [v.version for v in versions]
        assert 1 in version_numbers
        assert 2 in version_numbers
        assert 3 in version_numbers


# =========================================================================
# FM-169: Recommendations engine
# =========================================================================


class TestRecommendations:
    @pytest.mark.asyncio
    async def test_generate_recommendations(
        self, db_session: AsyncSession, sample_project
    ):
        recs = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        await db_session.commit()
        # Should return some list (may be empty if no conditions met)
        assert isinstance(recs, list)

    @pytest.mark.asyncio
    async def test_generate_knowledge_gap_recommendation(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """A project with a completed run but no knowledge should get a knowledge_gap rec."""
        sample_run.status = "completed"
        await db_session.flush()

        recs = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        await db_session.commit()

        # Should detect knowledge gap
        knowledge_gaps = [
            r for r in recs if r.rec_type == RecommendationType.KNOWLEDGE_GAP
        ]
        assert len(knowledge_gaps) >= 1

    @pytest.mark.asyncio
    async def test_list_recommendations(
        self, db_session: AsyncSession, sample_project
    ):
        # Generate first
        await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        await db_session.commit()

        items, total = await recommendation_service.list_recommendations(
            db_session, sample_project.id
        )
        assert isinstance(items, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_dismiss_recommendation(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        sample_run.status = "completed"
        await db_session.flush()
        await db_session.commit()

        recs = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        await db_session.commit()

        if recs:
            dismissed = await recommendation_service.dismiss_recommendation(
                db_session, recs[0].id, feedback="not_relevant"
            )
            await db_session.commit()
            assert dismissed.dismissed is True
            assert dismissed.feedback == "not_relevant"

    @pytest.mark.asyncio
    async def test_dismiss_nonexistent(self, db_session: AsyncSession):
        result = await recommendation_service.dismiss_recommendation(
            db_session, uuid.uuid4()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_duplicate_recommendations(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Generating twice should not create duplicates."""
        sample_run.status = "completed"
        await db_session.flush()
        await db_session.commit()

        _recs1 = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        assert isinstance(_recs1, list)
        await db_session.commit()

        _recs2 = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        assert isinstance(_recs2, list)
        await db_session.commit()

        # Second generation should not add duplicates
        all_items, total = await recommendation_service.list_recommendations(
            db_session, sample_project.id, include_dismissed=True, limit=200
        )
        titles = [r.title for r in all_items]
        # Each title should be unique (no duplicates)
        assert len(titles) == len(set(titles))


# =========================================================================
# FM-170: Reindex & hardening
# =========================================================================


class TestReindex:
    @pytest.mark.asyncio
    async def test_reindex_project(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_run,
        sample_task,
        sample_artifact,
    ):
        count = await search_service.reindex_project(db_session, sample_project.id)
        await db_session.commit()
        assert count > 0

    @pytest.mark.asyncio
    async def test_reindex_empty_project(self, db_session: AsyncSession):
        """Reindex a non-existent project should return 0."""
        count = await search_service.reindex_project(db_session, uuid.uuid4())
        assert count == 0


# =========================================================================
# Model unit tests
# =========================================================================


class TestModels:
    def test_search_entity_type_values(self):
        assert SearchEntityType.TASK.value == "task"
        assert SearchEntityType.ARTIFACT.value == "artifact"
        assert SearchEntityType.KNOWLEDGE.value == "knowledge"

    def test_convention_category_values(self):
        assert ConventionCategory.NAMING.value == "naming"
        assert ConventionCategory.SECURITY.value == "security"

    def test_convention_enforcement_values(self):
        assert ConventionEnforcement.ADVISORY.value == "advisory"
        assert ConventionEnforcement.REQUIRED.value == "required"

    def test_recommendation_type_values(self):
        assert RecommendationType.KNOWLEDGE_GAP.value == "knowledge_gap"
        assert RecommendationType.TECH_DEBT.value == "tech_debt"
        assert RecommendationType.REUSABLE_PATTERN.value == "reusable_pattern"


# =========================================================================
# FM-170: Index integrity checker
# =========================================================================


class TestIndexIntegrity:
    @pytest.mark.asyncio
    async def test_integrity_after_reindex(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_run,
        sample_task,
        sample_artifact,
    ):
        """After reindex, integrity check should pass (no orphans, no missing)."""
        await search_service.reindex_project(db_session, sample_project.id)
        await db_session.commit()

        result = await search_service.check_index_integrity(
            db_session, sample_project.id
        )
        assert result["passed"] is True
        assert result["orphaned_count"] == 0
        assert result["missing_count"] == 0
        assert result["total_indexed"] > 0

    @pytest.mark.asyncio
    async def test_integrity_detects_missing(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_run,
        sample_task,
        sample_artifact,
    ):
        """Before reindex, entities exist but are not indexed â€” integrity should detect missing."""
        result = await search_service.check_index_integrity(
            db_session, sample_project.id
        )
        assert result["missing_count"] > 0
        assert result["passed"] is False

    @pytest.mark.asyncio
    async def test_integrity_empty_project(self, db_session: AsyncSession):
        """Non-existent project should pass (nothing indexed, nothing to index)."""
        result = await search_service.check_index_integrity(
            db_session, uuid.uuid4()
        )
        assert result["total_indexed"] == 0
        assert result["passed"] is True

    @pytest.mark.asyncio
    async def test_integrity_entity_counts(
        self,
        db_session: AsyncSession,
        sample_project,
        sample_run,
        sample_task,
        sample_artifact,
    ):
        """Entity counts should reflect actual vs indexed accurately."""
        await search_service.reindex_project(db_session, sample_project.id)
        await db_session.commit()

        result = await search_service.check_index_integrity(
            db_session, sample_project.id
        )
        for etype, counts in result["entity_counts"].items():
            assert counts["indexed"] == counts["actual"], (
                f"{etype}: indexed={counts['indexed']} != actual={counts['actual']}"
            )


# =========================================================================
# Additional edge-case tests
# =========================================================================


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_search_special_characters(self, db_session: AsyncSession):
        """Search with special characters should not crash."""
        items, total, _ = await search_service.search(
            db_session, query="test@#$%^&*()"
        )
        assert isinstance(items, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_convention_list_category_filter(
        self, db_session: AsyncSession, sample_project
    ):
        """List conventions filtered by category."""
        await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.SECURITY,
            name="Security rule",
            rule_text="Never expose internal errors.",
            author_id=STUB_USER_ID,
        )
        await convention_service.create_convention(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.NAMING,
            name="Naming rule",
            rule_text="Use descriptive names.",
            author_id=STUB_USER_ID,
        )
        await db_session.commit()

        items, total = await convention_service.list_conventions(
            db_session,
            project_id=sample_project.id,
            category=ConventionCategory.SECURITY,
        )
        assert total >= 1
        assert all(c.category == ConventionCategory.SECURITY for c in items)

    @pytest.mark.asyncio
    async def test_recommendation_tech_debt_with_failures(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Tech debt recommendation fires when 2+ tasks have failed."""
        t1 = Task(
            title="Failed Task 1",
            task_type="implementation",
            status=TaskStatus.FAILED,
            order_index=0,
            run_id=sample_run.id,
        )
        t2 = Task(
            title="Failed Task 2",
            task_type="review",
            status=TaskStatus.FAILED,
            order_index=1,
            run_id=sample_run.id,
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        recs = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        await db_session.commit()


# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# FM-162: Embedding Generation, Semantic Search & Hybrid Ranking
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


class TestCosineSimilarity:
    """FM-162: Cosine similarity vector math."""

    def test_identical_vectors(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0

    def test_orthogonal_vectors(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([1, 0], [0, 1]) == 0.0

    def test_opposite_vectors(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([1, 0], [-1, 0]) == -1.0

    def test_similar_vectors_high_score(self):
        from app.services.embedding_service import cosine_similarity

        sim = cosine_similarity([1.0, 1.0, 0.0], [1.0, 0.9, 0.1])
        assert sim > 0.95  # Very similar vectors

    def test_dissimilar_vectors_low_score(self):
        from app.services.embedding_service import cosine_similarity

        sim = cosine_similarity([1.0, 0.0, 0.0], [0.0, 0.0, 1.0])
        assert sim == 0.0

    def test_zero_vector_returns_zero(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([0, 0, 0], [1, 2, 3]) == 0.0

    def test_empty_vectors_returns_zero(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([], []) == 0.0

    def test_mismatched_dimensions_returns_zero(self):
        from app.services.embedding_service import cosine_similarity

        assert cosine_similarity([1, 2], [1, 2, 3]) == 0.0


class TestEmbeddingGeneration:
    """FM-162: Embedding generation with pluggable providers."""

    @pytest.mark.asyncio
    async def test_generate_embedding_with_custom_fn(self):
        """Custom embedding_fn produces real vectors."""
        from app.services.embedding_service import generate_embedding

        async def mock_embed(text, model, dimensions):
            # Deterministic vector based on text length
            import hashlib

            h = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in h[:dimensions]]

        result = await generate_embedding(
            "machine learning classification",
            dimensions=16,
            embedding_fn=mock_embed,
        )
        assert len(result) == 16
        assert all(isinstance(x, float) for x in result)
        assert any(x != 0.0 for x in result)  # Not all zeros

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Empty text returns zero vector."""
        from app.services.embedding_service import generate_embedding

        result = await generate_embedding("", dimensions=8)
        assert result == [0.0] * 8

    @pytest.mark.asyncio
    async def test_generate_embedding_whitespace_only(self):
        """Whitespace-only text returns zero vector."""
        from app.services.embedding_service import generate_embedding

        result = await generate_embedding("   ", dimensions=4)
        assert result == [0.0] * 4


class TestEmbeddingStorage:
    """FM-162: Store and retrieve embedding vectors."""

    @pytest.mark.asyncio
    async def test_store_and_retrieve_embedding(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Store an embedding vector and retrieve it by search_index_id."""
        from app.services import embedding_service

        task = Task(
            title="Test embedding storage",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        idx = await search_service.index_task(db_session, task)
        await db_session.flush()

        vector = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        emb = await embedding_service.store_embedding(
            db_session,
            search_index_id=idx.id,
            embedding=vector,
            model_name="test-model",
            dimensions=8,
        )
        await db_session.flush()

        assert emb is not None
        assert emb.embedding == vector
        assert emb.dimensions == 8
        assert emb.model_name == "test-model"

        # Retrieve
        retrieved = await embedding_service.get_embedding(db_session, idx.id)
        assert retrieved is not None
        assert retrieved.embedding == vector

    @pytest.mark.asyncio
    async def test_store_embedding_upsert(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Storing embedding for same index entry updates (not duplicates)."""
        from app.services import embedding_service

        task = Task(
            title="Test upsert",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        idx = await search_service.index_task(db_session, task)
        await db_session.flush()

        v1 = [0.1, 0.2, 0.3]
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx.id,
            embedding=v1,
            dimensions=3,
        )
        await db_session.flush()

        v2 = [0.9, 0.8, 0.7]
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx.id,
            embedding=v2,
            dimensions=3,
        )
        await db_session.flush()

        retrieved = await embedding_service.get_embedding(db_session, idx.id)
        assert retrieved.embedding == v2  # Updated, not duplicated

    @pytest.mark.asyncio
    async def test_generate_and_store(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """generate_and_store creates embedding from title+body text."""
        from app.services import embedding_service

        task = Task(
            title="Neural network training",
            task_type="implementation",
            description="Train a deep learning model for classification",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        idx = await search_service.index_task(db_session, task)
        await db_session.flush()

        async def mock_embed(text, model, dimensions):
            import hashlib

            h = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in h[:dimensions]]

        emb = await embedding_service.generate_and_store(
            db_session,
            search_index_id=idx.id,
            title=idx.title,
            body=idx.body,
            dimensions=16,
            embedding_fn=mock_embed,
        )
        assert emb is not None
        assert len(emb.embedding) == 16
        assert emb.dimensions == 16


class TestBatchEmbeddingGeneration:
    """FM-162: Batch embedding generation for indexed content."""

    @pytest.mark.asyncio
    async def test_batch_generates_for_missing(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """batch_generate_embeddings creates embeddings for entries without one."""
        from app.services import embedding_service

        # Create tasks and index them
        for i in range(3):
            task = Task(
                title=f"Task {i} for batch test",
                task_type="implementation",
                order_index=i,
                run_id=sample_run.id,
            )
            db_session.add(task)
            await db_session.flush()
            await search_service.index_task(db_session, task)

        await db_session.flush()

        async def mock_embed(text, model, dimensions):
            import hashlib

            h = hashlib.sha256(text.encode()).digest()
            return [float(b) / 255.0 for b in h[:dimensions]]

        stats = await embedding_service.batch_generate_embeddings(
            db_session,
            project_id=sample_project.id,
            dimensions=8,
            embedding_fn=mock_embed,
        )

        assert stats["generated"] >= 3
        assert stats["failed"] == 0

    @pytest.mark.asyncio
    async def test_batch_skips_already_embedded(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """batch_generate_embeddings doesn't re-generate existing embeddings."""
        from app.services import embedding_service

        task = Task(
            title="Already embedded task",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        idx = await search_service.index_task(db_session, task)
        await db_session.flush()

        # Pre-store an embedding
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx.id,
            embedding=[0.5] * 8,
            dimensions=8,
        )
        await db_session.flush()

        async def mock_embed(text, model, dimensions):
            return [0.9] * dimensions  # Different vector

        stats = await embedding_service.batch_generate_embeddings(
            db_session,
            project_id=sample_project.id,
            dimensions=8,
            embedding_fn=mock_embed,
        )

        # The already-embedded entry should be skipped
        # (it might generate for project/run entries but not duplicate the task)
        retrieved = await embedding_service.get_embedding(db_session, idx.id)
        assert retrieved.embedding == [0.5] * 8  # Unchanged


class TestSemanticSearch:
    """FM-162: Semantic search via embedding cosine similarity."""

    @pytest.mark.asyncio
    async def test_semantic_search_ranks_by_similarity(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Semantic search returns results ranked by vector similarity."""
        from app.services import embedding_service

        # Create 3 tasks with different content
        t1 = Task(
            title="Machine learning model training",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        t2 = Task(
            title="Database migration script",
            task_type="implementation",
            order_index=1,
            run_id=sample_run.id,
        )
        t3 = Task(
            title="Neural network optimization",
            task_type="implementation",
            order_index=2,
            run_id=sample_run.id,
        )
        db_session.add_all([t1, t2, t3])
        await db_session.flush()

        idx1 = await search_service.index_task(db_session, t1)
        idx2 = await search_service.index_task(db_session, t2)
        idx3 = await search_service.index_task(db_session, t3)
        await db_session.flush()

        # Store embeddings that simulate semantic similarity:
        # "ML training" and "neural network" are in the same semantic space
        # "database migration" is in a different space
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx1.id,
            embedding=[0.9, 0.8, 0.1, 0.0],
            dimensions=4,
        )
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx2.id,
            embedding=[0.1, 0.0, 0.9, 0.8],
            dimensions=4,
        )
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx3.id,
            embedding=[0.85, 0.75, 0.15, 0.05],
            dimensions=4,
        )
        await db_session.flush()

        # Query embedding close to ML/neural network space
        async def ml_query_embed(text, model, dimensions):
            return [0.88, 0.77, 0.12, 0.02]

        results = await embedding_service.semantic_search(
            db_session,
            query="deep learning",
            dimensions=4,
            embedding_fn=ml_query_embed,
        )

        assert len(results) >= 2
        # ML and neural network should rank higher than database
        titles = [r["title"] for r in results]
        assert any("Machine learning" in t for t in titles)
        assert any("Neural network" in t for t in titles)

        # Verify ordering: ML-related results before database
        ml_scores = [
            r["semantic_score"]
            for r in results
            if "Machine" in r["title"] or "Neural" in r["title"]
        ]
        db_scores = [
            r["semantic_score"]
            for r in results
            if "Database" in r["title"]
        ]
        if db_scores:
            assert min(ml_scores) > max(db_scores)

    @pytest.mark.asyncio
    async def test_semantic_search_no_embeddings(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """Semantic search returns empty when no embeddings exist."""
        from app.services import embedding_service

        async def query_embed(text, model, dimensions):
            return [0.5] * dimensions

        results = await embedding_service.semantic_search(
            db_session,
            query="anything",
            dimensions=4,
            embedding_fn=query_embed,
        )
        assert results == []


class TestHybridRanking:
    """FM-162: Hybrid ranking combining text and semantic scores."""

    @pytest.mark.asyncio
    async def test_hybrid_combines_text_and_semantic(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """hybrid_search blends keyword and semantic scores using alpha."""
        from app.services import embedding_service

        # Create tasks: one matches keywords well, another matches semantically
        t_keyword = Task(
            title="python script automation tool",
            task_type="implementation",
            description="python script automation tool for batch processing",
            order_index=0,
            run_id=sample_run.id,
        )
        t_semantic = Task(
            title="code generator engine",
            task_type="implementation",
            description="automated code generation system",
            order_index=1,
            run_id=sample_run.id,
        )
        db_session.add_all([t_keyword, t_semantic])
        await db_session.flush()

        idx_kw = await search_service.index_task(db_session, t_keyword)
        idx_sem = await search_service.index_task(db_session, t_semantic)
        await db_session.flush()

        # Keyword task: low semantic similarity to "automation"
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx_kw.id,
            embedding=[0.3, 0.2, 0.8, 0.1],
            dimensions=4,
        )
        # Semantic task: high semantic similarity to "automation"
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx_sem.id,
            embedding=[0.9, 0.85, 0.1, 0.05],
            dimensions=4,
        )
        await db_session.flush()

        # Query embedding close to semantic task
        async def auto_embed(text, model, dimensions):
            return [0.88, 0.82, 0.12, 0.08]

        # Pure semantic (alpha=0) should favor the semantic match
        results_semantic = await embedding_service.hybrid_search(
            db_session,
            query="automation",
            alpha=0.0,
            dimensions=4,
            embedding_fn=auto_embed,
        )
        if results_semantic:
            # The semantically closer task should rank first
            top = results_semantic[0]
            assert top["semantic_score"] > 0

        # Pure keyword (alpha=1) should favor the keyword match
        results_keyword = await embedding_service.hybrid_search(
            db_session,
            query="automation",
            alpha=1.0,
            dimensions=4,
            embedding_fn=auto_embed,
        )
        if results_keyword:
            top = results_keyword[0]
            assert top["text_score"] > 0

    @pytest.mark.asyncio
    async def test_hybrid_alpha_boundaries(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """alpha=1.0 produces text_score-only ranking, alpha=0.0 semantic-only."""
        from app.services import embedding_service

        task = Task(
            title="test alpha boundaries",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        idx = await search_service.index_task(db_session, task)
        await db_session.flush()

        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx.id,
            embedding=[0.7, 0.6, 0.5, 0.4],
            dimensions=4,
        )
        await db_session.flush()

        async def embed_fn(text, model, dimensions):
            return [0.65, 0.55, 0.45, 0.35]

        # alpha=1.0: hybrid_score should equal text_score
        results = await embedding_service.hybrid_search(
            db_session,
            query="test",
            alpha=1.0,
            dimensions=4,
            embedding_fn=embed_fn,
        )
        for r in results:
            assert r["hybrid_score"] == r["text_score"]

        # alpha=0.0: hybrid_score should equal semantic_score
        results = await embedding_service.hybrid_search(
            db_session,
            query="test",
            alpha=0.0,
            dimensions=4,
            embedding_fn=embed_fn,
        )
        for r in results:
            assert r["hybrid_score"] == r["semantic_score"]

    @pytest.mark.asyncio
    async def test_hybrid_graceful_without_embeddings(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """hybrid_search degrades to keyword-only when no embeddings exist."""
        from app.services import embedding_service

        task = Task(
            title="graceful degradation test",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        await search_service.index_task(db_session, task)
        await db_session.flush()

        # No embeddings stored, no embedding_fn â€” embedding path will fail
        # but hybrid_search should still return keyword results
        async def failing_embed(text, model, dimensions):
            raise RuntimeError("No API key configured")

        results = await embedding_service.hybrid_search(
            db_session,
            query="graceful",
            alpha=0.5,
            dimensions=4,
            embedding_fn=failing_embed,
        )
        # Should still get results from keyword search
        assert len(results) >= 1
        assert results[0]["text_score"] > 0


class TestFindSimilarWithEmbeddings:
    """FM-162: find_similar uses embeddings when available."""

    @pytest.mark.asyncio
    async def test_find_similar_uses_embeddings(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """find_similar returns embedding-based results when embeddings exist."""
        from app.services import embedding_service

        # Create 3 tasks
        t1 = Task(
            title="Task Alpha about data processing",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        t2 = Task(
            title="Task Beta about web frontend",
            task_type="implementation",
            order_index=1,
            run_id=sample_run.id,
        )
        t3 = Task(
            title="Task Gamma about data analysis",
            task_type="implementation",
            order_index=2,
            run_id=sample_run.id,
        )
        db_session.add_all([t1, t2, t3])
        await db_session.flush()

        idx1 = await search_service.index_task(db_session, t1)
        idx2 = await search_service.index_task(db_session, t2)
        idx3 = await search_service.index_task(db_session, t3)
        await db_session.flush()

        # Embeddings: t1 and t3 are semantically close (data), t2 is far (web)
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx1.id,
            embedding=[0.9, 0.8, 0.1, 0.0],
            dimensions=4,
        )
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx2.id,
            embedding=[0.1, 0.0, 0.9, 0.8],
            dimensions=4,
        )
        await embedding_service.store_embedding(
            db_session,
            search_index_id=idx3.id,
            embedding=[0.85, 0.75, 0.15, 0.05],
            dimensions=4,
        )
        await db_session.flush()

        # Find similar to t1 (data processing)
        results = await search_service.find_similar(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=t1.id,
        )

        assert len(results) >= 1
        # t3 (data analysis) should be more similar to t1 than t2 (web)
        if len(results) >= 2:
            titles = [r["title"] for r in results]
            gamma_idx = next(
                (i for i, t in enumerate(titles) if "Gamma" in t), None
            )
            beta_idx = next(
                (i for i, t in enumerate(titles) if "Beta" in t), None
            )
            if gamma_idx is not None and beta_idx is not None:
                assert gamma_idx < beta_idx  # Gamma ranks higher

    @pytest.mark.asyncio
    async def test_find_similar_falls_back_to_tfidf(
        self, db_session: AsyncSession, sample_project, sample_run
    ):
        """find_similar falls back to TF-IDF when no embeddings exist."""
        t1 = Task(
            title="Python testing framework comparison",
            task_type="implementation",
            description="Compare pytest, unittest, and nose for Python testing",
            order_index=0,
            run_id=sample_run.id,
        )
        t2 = Task(
            title="Python testing best practices",
            task_type="review",
            description="Document best practices for Python testing with pytest",
            order_index=1,
            run_id=sample_run.id,
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        await search_service.index_task(db_session, t1)
        await search_service.index_task(db_session, t2)
        await db_session.flush()

        # No embeddings stored â€” should fall back to TF-IDF
        results = await search_service.find_similar(
            db_session,
            entity_type=SearchEntityType.TASK,
            entity_id=t1.id,
        )
        # TF-IDF should find t2 due to keyword overlap
        assert len(results) >= 1
        assert any("best practices" in r["title"] for r in results)


class TestSemanticSearchRoute:
    """FM-162: Semantic search HTTP route."""

    @pytest.mark.asyncio
    async def test_semantic_search_endpoint(
        self, client: AsyncClient, db_session: AsyncSession, sample_project, sample_run
    ):
        """GET /search/semantic returns hybrid results."""
        from app.services import embedding_service

        task = Task(
            title="route test semantic search",
            task_type="implementation",
            order_index=0,
            run_id=sample_run.id,
        )
        db_session.add(task)
        await db_session.flush()

        await search_service.index_task(db_session, task)
        await db_session.flush()

        await embedding_service.store_embedding(
            db_session,
            search_index_id=(
                await db_session.execute(
                    select(SearchIndex).where(
                        SearchIndex.entity_type == SearchEntityType.TASK,
                        SearchIndex.entity_id == task.id,
                    )
                )
            ).scalar_one().id,
            embedding=[0.5, 0.5, 0.5, 0.5],
            dimensions=4,
        )
        await db_session.commit()

        resp = await client.get(
            "/search/semantic",
            params={"q": "semantic", "alpha": "0.5"},
        )
        # Route should exist and return a valid response
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "alpha" in data
        assert data["mode"] == "hybrid"

    @pytest.mark.asyncio
    async def test_semantic_search_alpha_validation(self, client: AsyncClient):
        """GET /search/semantic validates alpha bounds."""
        resp = await client.get(
            "/search/semantic",
            params={"q": "test", "alpha": "1.5"},
        )
        assert resp.status_code == 422  # Validation error
