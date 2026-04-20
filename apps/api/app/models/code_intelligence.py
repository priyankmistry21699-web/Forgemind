"""Code Intelligence models — FM-181 through FM-189.

New tables:
- module_dependencies: File & module dependency graph (FM-181)
- coverage_maps: Test-to-source coverage mapping (FM-183)
- pattern_rules: Configurable code pattern rules (FM-185)
- pattern_occurrences: Detected pattern instances (FM-185)
- debt_entries: Technical debt tracking entries (FM-186)
- debt_snapshots: Point-in-time debt score snapshots (FM-186)
- test_results: Per-test outcome tracking (FM-187)
- complexity_metrics: Cyclomatic/cognitive complexity metrics (FM-188)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Boolean,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSON as PG_JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


# ── FM-181: Module Dependencies (Codebase Graph) ────────────────


class DependencyType(str, enum.Enum):
    IMPORT = "import"
    DYNAMIC = "dynamic"
    TYPE_ONLY = "type_only"


class ModuleDependency(Base):
    """Directed edge in the codebase dependency graph."""

    __tablename__ = "module_dependencies"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    target_file: Mapped[str] = mapped_column(String(500), nullable=False)
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType, name="dependency_type"),
        default=DependencyType.IMPORT,
        nullable=False,
    )
    import_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_scanned: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index(
            "ix_module_dep_project_source",
            "project_id",
            "source_file",
        ),
        Index(
            "ix_module_dep_project_target",
            "project_id",
            "target_file",
        ),
    )


# ── FM-183: Test Coverage Mapping ────────────────────────────────


class CoverageMap(Base):
    """Maps source files to test files that cover them."""

    __tablename__ = "coverage_maps"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    test_file: Mapped[str] = mapped_column(String(500), nullable=False)
    coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_coverage_project_source", "project_id", "source_file"),)


# ── FM-185: Code Pattern Detection ──────────────────────────────


class PatternType(str, enum.Enum):
    ANTI_PATTERN = "anti_pattern"
    POSITIVE_PATTERN = "positive_pattern"


class PatternSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PatternRule(Base):
    """Configurable code pattern detection rule."""

    __tablename__ = "pattern_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    pattern_type: Mapped[PatternType] = mapped_column(
        Enum(PatternType, name="pattern_type"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(50), default="python", nullable=False)
    rule_definition: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[PatternSeverity] = mapped_column(
        Enum(PatternSeverity, name="pattern_severity"),
        default=PatternSeverity.WARNING,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PatternOccurrence(Base):
    """Instance of a detected code pattern in a file."""

    __tablename__ = "pattern_occurrences"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("pattern_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    line_start: Mapped[int] = mapped_column(Integer, nullable=False)
    line_end: Mapped[int] = mapped_column(Integer, nullable=False)
    snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-186: Technical Debt Tracking ──────────────────────────────


class DebtType(str, enum.Enum):
    PATTERN = "pattern"
    COMMENT = "comment"  # TODO/FIXME/HACK
    AGE = "age"
    COMPLEXITY = "complexity"


class DebtEntry(Base):
    """Individual technical debt item in a file."""

    __tablename__ = "debt_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    debt_type: Mapped[DebtType] = mapped_column(
        Enum(DebtType, name="debt_type"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DebtSnapshot(Base):
    """Point-in-time debt summary for trend tracking."""

    __tablename__ = "debt_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    total_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    entry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    breakdown: Mapped[dict | None] = mapped_column(PG_JSON, nullable=True)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ── FM-187: Test Flakiness Detection ────────────────────────────


class TestOutcome(str, enum.Enum):
    # Pytest otherwise tries to collect this enum as a test class (because of
    # the `Test*` prefix) and emits a PytestCollectionWarning when the enum
    # is re-imported in a test module. Dunder attributes on enum classes are
    # treated as metadata rather than members, so this is the safe opt-out.
    __test__ = False

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestResult(Base):
    """Individual test execution result for flakiness tracking."""

    __tablename__ = "test_results"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    test_name: Mapped[str] = mapped_column(String(500), nullable=False)
    test_file: Mapped[str] = mapped_column(String(500), nullable=False)
    outcome: Mapped[TestOutcome] = mapped_column(
        Enum(TestOutcome, name="test_outcome"), nullable=False
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarantined: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_test_result_project_name", "project_id", "test_name"),)


# ── FM-188: Code Complexity Metrics ──────────────────────────────


class MetricType(str, enum.Enum):
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    LINES_OF_CODE = "lines_of_code"
    FUNCTION_COUNT = "function_count"


class ComplexityMetric(Base):
    """Code complexity measurement for a file or function."""

    __tablename__ = "complexity_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    function_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(MetricType, name="metric_type"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    exceeds_threshold: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_complexity_project_file", "project_id", "file_path"),)
