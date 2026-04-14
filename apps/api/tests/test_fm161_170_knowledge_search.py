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
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import STUB_USER_ID

# ── Models / enums ──────────────────────────────────────────────
from app.models.search_knowledge import (
    SearchEntityType,
    ConventionCategory,
    ConventionEnforcement,
    RecommendationType,
)
from app.models.artifact import Artifact, ArtifactType
from app.models.task import Task, TaskStatus
from app.models.run import Run

# ── Services ────────────────────────────────────────────────────
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

        items, total = await search_service.search(db_session, query="Test Task")
        assert total >= 1
        assert any(i["entity_id"] == str(sample_task.id) for i in items)

    @pytest.mark.asyncio
    async def test_index_artifact(self, db_session: AsyncSession, sample_artifact):
        await search_service.index_artifact(db_session, sample_artifact)
        await db_session.commit()

        items, total = await search_service.search(db_session, query="Architecture")
        assert total >= 1
        assert any(i["entity_id"] == str(sample_artifact.id) for i in items)

    @pytest.mark.asyncio
    async def test_index_run(self, db_session: AsyncSession, sample_run):
        await search_service.index_run(db_session, sample_run)
        await db_session.commit()

        items, total = await search_service.search(db_session, query="Run")
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

        items, _ = await search_service.search(db_session, query="Updated Task Title")
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

        items, total = await search_service.search(
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

        items, total = await search_service.search(
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

        items, total = await search_service.search(
            db_session,
            query="Test",
            entity_types=[SearchEntityType.ARTIFACT],
        )
        for i in items:
            assert i["entity_type"] == SearchEntityType.ARTIFACT.value

    @pytest.mark.asyncio
    async def test_search_no_results(self, db_session: AsyncSession):
        items, total = await search_service.search(
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

        items, total = await search_service.search(
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

        items, _ = await search_service.search(db_session, query="Architecture")
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
        items, total = await search_service.search(
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
        new_ver = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=sample_artifact.id,
            content="# Architecture\nCompletely different content",
            created_by="test-agent",
        )
        await db_session.commit()
        assert new_ver is not None

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

        v3 = await artifact_version_service.create_new_version(
            db_session,
            parent_artifact_id=v2.id,
            content="Version 3",
            created_by="agent",
        )
        await db_session.commit()
        assert v3 is not None

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

        recs1 = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        assert isinstance(recs1, list)
        await db_session.commit()

        recs2 = await recommendation_service.generate_recommendations(
            db_session, sample_project.id
        )
        assert isinstance(recs2, list)
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
