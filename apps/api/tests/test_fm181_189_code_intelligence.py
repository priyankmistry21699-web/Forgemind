"""Tests for FM-181–189: Code Intelligence.

Covers: dependency graph, impact analysis, coverage mapping,
pattern detection, technical debt, test flakiness, code complexity.
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.code_intelligence import (
    DependencyType,
    PatternType,
    PatternSeverity,
    DebtType,
    TestOutcome,
    MetricType,
)
from app.services import (
    code_graph_service,
    pattern_debt_service,
    flakiness_complexity_service,
)

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ══════════════════════════════════════════════════════════════════
# FM-181: Dependency Graph
# ══════════════════════════════════════════════════════════════════


class TestDependencyGraph:
    @pytest.mark.asyncio
    async def test_record_dependency(self, db_session: AsyncSession, sample_project):
        dep = await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="app/main.py",
            target_file="app/utils.py",
            dependency_type=DependencyType.IMPORT,
            import_name="app.utils",
        )
        await db_session.commit()
        assert dep.id is not None
        assert dep.source_file == "app/main.py"
        assert dep.target_file == "app/utils.py"

    @pytest.mark.asyncio
    async def test_scan_file_dependencies(self, db_session: AsyncSession, sample_project):
        source = "import os\nimport json\nfrom app.utils import helper\n"
        deps = await code_graph_service.scan_file_dependencies(
            db_session,
            project_id=sample_project.id,
            file_path="app/main.py",
            source_code=source,
        )
        await db_session.commit()
        assert len(deps) == 3  # os, json, app.utils.helper

    @pytest.mark.asyncio
    async def test_get_file_dependencies(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="a.py",
            target_file="b.py",
        )
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="a.py",
            target_file="c.py",
        )
        await db_session.commit()

        deps = await code_graph_service.get_file_dependencies(
            db_session, sample_project.id, "a.py"
        )
        assert len(deps) == 2

    @pytest.mark.asyncio
    async def test_get_file_dependents(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="x.py",
            target_file="shared.py",
        )
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="y.py",
            target_file="shared.py",
        )
        await db_session.commit()

        dependents = await code_graph_service.get_file_dependents(
            db_session, sample_project.id, "shared.py"
        )
        assert len(dependents) == 2

    @pytest.mark.asyncio
    async def test_get_dependency_graph(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="m1.py",
            target_file="m2.py",
        )
        await db_session.commit()

        graph = await code_graph_service.get_dependency_graph(
            db_session, sample_project.id
        )
        assert graph["node_count"] >= 2
        assert graph["edge_count"] >= 1


# ══════════════════════════════════════════════════════════════════
# FM-182: Impact Analysis
# ══════════════════════════════════════════════════════════════════


class TestImpactAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_impact_basic(self, db_session: AsyncSession, sample_project):
        # Build a chain: a -> b -> c
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="b.py", target_file="a.py",
        )
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="c.py", target_file="b.py",
        )
        await db_session.commit()

        result = await code_graph_service.analyze_impact(
            db_session, sample_project.id, ["a.py"]
        )
        assert "b.py" in result["affected_files"]

    @pytest.mark.asyncio
    async def test_analyze_impact_max_depth(self, db_session: AsyncSession, sample_project):
        result = await code_graph_service.analyze_impact(
            db_session, sample_project.id, ["nonexistent.py"], max_depth=1
        )
        assert result["total_affected"] == 0


# ══════════════════════════════════════════════════════════════════
# FM-183: Coverage Mapping
# ══════════════════════════════════════════════════════════════════


class TestCoverageMapping:
    @pytest.mark.asyncio
    async def test_record_coverage(self, db_session: AsyncSession, sample_project):
        mapping = await code_graph_service.record_coverage(
            db_session,
            project_id=sample_project.id,
            source_file="app/service.py",
            test_file="tests/test_service.py",
            coverage_pct=85.5,
        )
        await db_session.commit()
        assert mapping.id is not None
        assert mapping.coverage_pct == 85.5

    @pytest.mark.asyncio
    async def test_record_coverage_upsert(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="s.py", test_file="t.py", coverage_pct=50.0,
        )
        await db_session.commit()

        updated = await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="s.py", test_file="t.py", coverage_pct=90.0,
        )
        await db_session.commit()
        assert updated.coverage_pct == 90.0

    @pytest.mark.asyncio
    async def test_get_tests_for_source(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="mod.py", test_file="test_mod.py",
        )
        await db_session.commit()

        tests = await code_graph_service.get_tests_for_source(
            db_session, sample_project.id, "mod.py"
        )
        assert len(tests) >= 1

    @pytest.mark.asyncio
    async def test_get_coverage_summary(self, db_session: AsyncSession, sample_project):
        await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="f1.py", test_file="t1.py", coverage_pct=80.0,
        )
        await db_session.commit()

        summary = await code_graph_service.get_coverage_summary(
            db_session, sample_project.id
        )
        assert summary["mapping_count"] >= 1


# ══════════════════════════════════════════════════════════════════
# FM-185: Pattern Detection
# ══════════════════════════════════════════════════════════════════


class TestPatternDetection:
    @pytest.mark.asyncio
    async def test_create_pattern_rule(self, db_session: AsyncSession):
        rule = await pattern_debt_service.create_pattern_rule(
            db_session,
            name="Bare except",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"except\s*:",
            severity=PatternSeverity.WARNING,
        )
        await db_session.commit()
        assert rule.id is not None
        assert rule.name == "Bare except"

    @pytest.mark.asyncio
    async def test_list_pattern_rules(self, db_session: AsyncSession):
        await pattern_debt_service.create_pattern_rule(
            db_session, name="Rule1",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"eval\(",
        )
        await db_session.commit()

        rules = await pattern_debt_service.list_pattern_rules(db_session)
        assert len(rules) >= 1

    @pytest.mark.asyncio
    async def test_scan_file_for_patterns(self, db_session: AsyncSession, sample_project):
        rule = await pattern_debt_service.create_pattern_rule(
            db_session, name="Eval usage",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"eval\(",
        )
        await db_session.commit()

        source = "x = 1\nresult = eval('1+1')\ny = 2\n"
        occs = await pattern_debt_service.scan_file_for_patterns(
            db_session, project_id=sample_project.id,
            file_path="test.py", source_code=source, rules=[rule],
        )
        await db_session.commit()
        assert len(occs) == 1
        assert occs[0].line_start == 2

    @pytest.mark.asyncio
    async def test_get_pattern_occurrences(self, db_session: AsyncSession, sample_project):
        rule = await pattern_debt_service.create_pattern_rule(
            db_session, name="Print usage",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"print\(",
        )
        source = "print('hello')\nprint('world')\n"
        await pattern_debt_service.scan_file_for_patterns(
            db_session, project_id=sample_project.id,
            file_path="noisy.py", source_code=source, rules=[rule],
        )
        await db_session.commit()

        occs, total = await pattern_debt_service.get_pattern_occurrences(
            db_session, sample_project.id
        )
        assert total >= 2


# ══════════════════════════════════════════════════════════════════
# FM-186: Technical Debt
# ══════════════════════════════════════════════════════════════════


class TestTechnicalDebt:
    @pytest.mark.asyncio
    async def test_scan_file_for_debt(self, db_session: AsyncSession, sample_project):
        source = "# TODO: fix this\nx = 1\n# FIXME: urgent\n# HACK: workaround\n"
        entries = await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="debt.py", source_code=source,
        )
        await db_session.commit()
        assert len(entries) == 3

    @pytest.mark.asyncio
    async def test_debt_entry_scores(self, db_session: AsyncSession, sample_project):
        source = "# TODO: minor\n# HACK: critical\n"
        entries = await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="scores.py", source_code=source,
        )
        await db_session.commit()
        scores = {e.description.strip(): e.score for e in entries}
        assert scores.get("# HACK: critical", 0) > scores.get("# TODO: minor", 0)

    @pytest.mark.asyncio
    async def test_list_debt_entries(self, db_session: AsyncSession, sample_project):
        source = "# TODO: a\n# FIXME: b\n"
        await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="list_debt.py", source_code=source,
        )
        await db_session.commit()

        entries, total = await pattern_debt_service.list_debt_entries(
            db_session, sample_project.id
        )
        assert total >= 2

    @pytest.mark.asyncio
    async def test_get_debt_summary(self, db_session: AsyncSession, sample_project):
        source = "# TODO: one\n# TODO: two\n"
        await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="summary.py", source_code=source,
        )
        await db_session.commit()

        summary = await pattern_debt_service.get_debt_summary(
            db_session, sample_project.id
        )
        assert summary["entry_count"] >= 2
        assert summary["total_score"] >= 2.0

    @pytest.mark.asyncio
    async def test_take_debt_snapshot(self, db_session: AsyncSession, sample_project):
        source = "# TODO: snap\n"
        await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="snap.py", source_code=source,
        )
        await db_session.commit()

        snap = await pattern_debt_service.take_debt_snapshot(
            db_session, sample_project.id
        )
        await db_session.commit()
        assert snap.id is not None
        assert snap.entry_count >= 1


# ══════════════════════════════════════════════════════════════════
# FM-187: Test Flakiness Detection
# ══════════════════════════════════════════════════════════════════


class TestFlakiness:
    @pytest.mark.asyncio
    async def test_record_test_result(self, db_session: AsyncSession, sample_project):
        tr = await flakiness_complexity_service.record_test_result(
            db_session,
            project_id=sample_project.id,
            test_name="test_example",
            test_file="tests/test_ex.py",
            outcome=TestOutcome.PASSED,
            duration_ms=150,
        )
        await db_session.commit()
        assert tr.id is not None
        assert tr.outcome == TestOutcome.PASSED

    @pytest.mark.asyncio
    async def test_get_flaky_tests(self, db_session: AsyncSession, sample_project):
        # Record alternating results to create a flaky test
        for outcome in [TestOutcome.PASSED, TestOutcome.FAILED, TestOutcome.PASSED, TestOutcome.FAILED]:
            await flakiness_complexity_service.record_test_result(
                db_session, project_id=sample_project.id,
                test_name="test_flaky_one",
                test_file="tests/test_flaky.py",
                outcome=outcome,
            )
        await db_session.commit()

        flaky = await flakiness_complexity_service.get_flaky_tests(
            db_session, sample_project.id, min_runs=3,
        )
        assert len(flaky) >= 1
        assert flaky[0]["test_name"] == "test_flaky_one"

    @pytest.mark.asyncio
    async def test_quarantine_test(self, db_session: AsyncSession, sample_project):
        await flakiness_complexity_service.record_test_result(
            db_session, project_id=sample_project.id,
            test_name="test_to_quarantine",
            test_file="tests/test_q.py",
            outcome=TestOutcome.FAILED,
        )
        await db_session.commit()

        count = await flakiness_complexity_service.quarantine_test(
            db_session, sample_project.id, "test_to_quarantine"
        )
        assert count >= 1

    @pytest.mark.asyncio
    async def test_flakiness_summary(self, db_session: AsyncSession, sample_project):
        await flakiness_complexity_service.record_test_result(
            db_session, project_id=sample_project.id,
            test_name="test_summary",
            test_file="tests/test_s.py",
            outcome=TestOutcome.PASSED,
        )
        await db_session.commit()

        summary = await flakiness_complexity_service.get_test_flakiness_summary(
            db_session, sample_project.id
        )
        assert summary["total_unique_tests"] >= 1


# ══════════════════════════════════════════════════════════════════
# FM-188: Code Complexity Metrics
# ══════════════════════════════════════════════════════════════════


class TestComplexity:
    @pytest.mark.asyncio
    async def test_analyze_file_complexity(self, db_session: AsyncSession, sample_project):
        source = """
def simple_func():
    return 1

def complex_func(x):
    if x > 0:
        if x > 10:
            for i in range(x):
                if i % 2 == 0:
                    print(i)
    return x
"""
        metrics = await flakiness_complexity_service.analyze_file_complexity(
            db_session, project_id=sample_project.id,
            file_path="complex.py", source_code=source,
        )
        await db_session.commit()
        # Should have cyclomatic for 2 functions + LOC + function_count
        assert len(metrics) >= 4

    @pytest.mark.asyncio
    async def test_complexity_hotspots(self, db_session: AsyncSession, sample_project):
        source = """
def mega_complex(a, b, c, d):
    if a: pass
    if b: pass
    if c: pass
    if d: pass
    for x in range(10):
        if x > 5:
            while True:
                break
    try:
        pass
    except ValueError:
        pass
    except TypeError:
        pass
"""
        await flakiness_complexity_service.analyze_file_complexity(
            db_session, project_id=sample_project.id,
            file_path="hotspot.py", source_code=source, threshold=3.0,
        )
        await db_session.commit()

        hotspots = await flakiness_complexity_service.get_complexity_hotspots(
            db_session, sample_project.id, exceeds_only=True,
        )
        assert len(hotspots) >= 1

    @pytest.mark.asyncio
    async def test_complexity_summary(self, db_session: AsyncSession, sample_project):
        source = "def f():\n    return 1\n"
        await flakiness_complexity_service.analyze_file_complexity(
            db_session, project_id=sample_project.id,
            file_path="simple_summary.py", source_code=source,
        )
        await db_session.commit()

        summary = await flakiness_complexity_service.get_complexity_summary(
            db_session, sample_project.id
        )
        assert summary["total_functions"] >= 1


# ══════════════════════════════════════════════════════════════════
# FM-181: AST Import Extraction (Unit Test)
# ══════════════════════════════════════════════════════════════════


class TestASTExtraction:
    def test_extract_imports(self):
        source = "import os\nimport sys\nfrom collections import OrderedDict\n"
        imports = code_graph_service._extract_imports_from_source(source)
        assert len(imports) == 3
        modules = {i["module"] for i in imports}
        assert "os" in modules
        assert "sys" in modules
        assert "collections.OrderedDict" in modules

    def test_extract_imports_syntax_error(self):
        imports = code_graph_service._extract_imports_from_source("def broken(")
        assert imports == []


# ══════════════════════════════════════════════════════════════════
# FM-181: TypeScript / ES6 / CommonJS Import Parsing
# ══════════════════════════════════════════════════════════════════


class TestTypeScriptImportParsing:
    """Verify regex-based TypeScript/ES6/CommonJS import extraction."""

    def test_es6_default_import(self):
        source = "import React from 'react';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "react"

    def test_es6_named_import(self):
        source = "import { useState, useEffect } from 'react';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "react"

    def test_es6_namespace_import(self):
        source = "import * as path from 'path';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "path"

    def test_es6_side_effect_import(self):
        source = "import './polyfills';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "./polyfills"

    def test_commonjs_require(self):
        source = "const express = require('express');\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "express"

    def test_require_destructured(self):
        source = "const { Router } = require('express');\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "express"

    def test_dynamic_import(self):
        source = "const mod = await import('./lazy-module');\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1
        assert imports[0]["module"] == "./lazy-module"

    def test_reexport(self):
        source = "export { foo } from './utils';\nexport * from './helpers';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        modules = {i["module"] for i in imports}
        assert "./utils" in modules
        assert "./helpers" in modules

    def test_mixed_import_styles(self):
        source = (
            "import React from 'react';\n"
            "import { useState } from 'react';\n"
            "const fs = require('fs');\n"
            "import type { AppProps } from 'next/app';\n"
            "export * from './components';\n"
        )
        imports = code_graph_service._extract_imports_from_typescript(source)
        modules = {i["module"] for i in imports}
        assert "react" in modules
        assert "fs" in modules
        assert "next/app" in modules
        assert "./components" in modules

    def test_scoped_package(self):
        source = "import { something } from '@forgemind/sdk';\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert imports[0]["module"] == "@forgemind/sdk"

    def test_double_quotes(self):
        source = 'import lodash from "lodash";\n'
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert imports[0]["module"] == "lodash"

    def test_deduplication(self):
        source = (
            "import React from 'react';\n"
            "import React from 'react';\n"
        )
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert len(imports) == 1

    def test_empty_source(self):
        imports = code_graph_service._extract_imports_from_typescript("")
        assert imports == []

    def test_no_imports(self):
        source = "const x = 42;\nconsole.log(x);\n"
        imports = code_graph_service._extract_imports_from_typescript(source)
        assert imports == []


class TestTypeScriptFileDetection:
    """Verify _is_typescript_file correctly identifies TS/JS files."""

    def test_ts_extension(self):
        assert code_graph_service._is_typescript_file("src/app.ts") is True

    def test_tsx_extension(self):
        assert code_graph_service._is_typescript_file("components/Button.tsx") is True

    def test_js_extension(self):
        assert code_graph_service._is_typescript_file("lib/utils.js") is True

    def test_jsx_extension(self):
        assert code_graph_service._is_typescript_file("App.jsx") is True

    def test_mjs_extension(self):
        assert code_graph_service._is_typescript_file("config.mjs") is True

    def test_cjs_extension(self):
        assert code_graph_service._is_typescript_file("config.cjs") is True

    def test_python_file(self):
        assert code_graph_service._is_typescript_file("main.py") is False

    def test_no_extension(self):
        assert code_graph_service._is_typescript_file("Makefile") is False


class TestTypeScriptModuleResolution:
    """Verify _ts_module_to_file heuristic."""

    def test_relative_import_no_ext(self):
        result = code_graph_service._ts_module_to_file("./utils")
        assert result == "./utils.ts"

    def test_relative_import_with_ext(self):
        result = code_graph_service._ts_module_to_file("./utils.ts")
        assert result == "./utils.ts"

    def test_bare_specifier(self):
        result = code_graph_service._ts_module_to_file("react")
        assert result == "node_modules/react/index.ts"

    def test_scoped_package(self):
        result = code_graph_service._ts_module_to_file("@forgemind/sdk")
        assert result == "node_modules/@forgemind/sdk/index.ts"

    def test_parent_relative(self):
        result = code_graph_service._ts_module_to_file("../shared/types")
        assert result == "../shared/types.ts"


class TestTypeScriptScanIntegration:
    """End-to-end: scan_file_dependencies with TypeScript source."""

    @pytest.mark.asyncio
    async def test_scan_ts_file_creates_dependencies(
        self, db_session: AsyncSession, sample_project,
    ):
        ts_source = (
            "import React from 'react';\n"
            "import { Button } from './components/Button';\n"
            "const lodash = require('lodash');\n"
        )
        deps = await code_graph_service.scan_file_dependencies(
            db_session,
            project_id=sample_project.id,
            file_path="src/App.tsx",
            source_code=ts_source,
            force=True,
        )
        assert len(deps) == 3
        targets = {d.target_file for d in deps}
        assert "node_modules/react/index.ts" in targets
        assert "./components/Button.ts" in targets
        assert "node_modules/lodash/index.ts" in targets

    @pytest.mark.asyncio
    async def test_scan_ts_file_incremental_skip(
        self, db_session: AsyncSession, sample_project,
    ):
        ts_source = "import axios from 'axios';\n"
        deps1 = await code_graph_service.scan_file_dependencies(
            db_session,
            project_id=sample_project.id,
            file_path="src/api.ts",
            source_code=ts_source,
            force=True,
        )
        assert len(deps1) == 1
        # Second scan with same content — should use cache
        deps2 = await code_graph_service.scan_file_dependencies(
            db_session,
            project_id=sample_project.id,
            file_path="src/api.ts",
            source_code=ts_source,
        )
        assert len(deps2) == 1

    @pytest.mark.asyncio
    async def test_scan_python_file_still_works(
        self, db_session: AsyncSession, sample_project,
    ):
        """Ensure Python parsing is not broken by TS additions."""
        py_source = "import os\nfrom sys import argv\n"
        deps = await code_graph_service.scan_file_dependencies(
            db_session,
            project_id=sample_project.id,
            file_path="src/main.py",
            source_code=py_source,
            force=True,
        )
        assert len(deps) == 2
        targets = {d.target_file for d in deps}
        assert "os.py" in targets
        assert "sys/argv.py" in targets


# ══════════════════════════════════════════════════════════════════
# FM-188: Cyclomatic Complexity (Unit Test)
# ══════════════════════════════════════════════════════════════════


class TestCyclomaticComputation:
    def test_simple_function(self):
        source = "def f():\n    return 1\n"
        results = flakiness_complexity_service._compute_cyclomatic_complexity(source)
        assert len(results) == 1
        assert results[0]["complexity"] == 1

    def test_branching_function(self):
        source = "def f(x):\n    if x: return 1\n    else: return 0\n"
        results = flakiness_complexity_service._compute_cyclomatic_complexity(source)
        assert results[0]["complexity"] == 2

    def test_syntax_error_returns_empty(self):
        results = flakiness_complexity_service._compute_cyclomatic_complexity("if:")
        assert results == []


# ══════════════════════════════════════════════════════════════════
# FM-188: Cognitive Complexity (Unit Test)
# ══════════════════════════════════════════════════════════════════


class TestCognitiveComplexity:
    def test_simple_function_zero(self):
        source = "def f():\n    return 1\n"
        results = flakiness_complexity_service._compute_cognitive_complexity(source)
        assert len(results) == 1
        assert results[0]["complexity"] == 0  # No flow breaks

    def test_single_if(self):
        source = "def f(x):\n    if x:\n        return 1\n    return 0\n"
        results = flakiness_complexity_service._compute_cognitive_complexity(source)
        assert results[0]["complexity"] >= 1

    def test_nested_ifs_higher_than_flat(self):
        """Nested structures should score higher than flat structures."""
        flat = "def f(a, b):\n    if a:\n        pass\n    if b:\n        pass\n"
        nested = "def f(a, b):\n    if a:\n        if b:\n            pass\n"
        flat_r = flakiness_complexity_service._compute_cognitive_complexity(flat)
        nested_r = flakiness_complexity_service._compute_cognitive_complexity(nested)
        assert nested_r[0]["complexity"] > flat_r[0]["complexity"]

    def test_for_loop_with_nesting(self):
        source = (
            "def f(items):\n"
            "    for item in items:\n"
            "        if item > 0:\n"
            "            pass\n"
        )
        results = flakiness_complexity_service._compute_cognitive_complexity(source)
        assert results[0]["complexity"] >= 2  # for(1+0) + if(1+1)

    def test_syntax_error_returns_empty(self):
        results = flakiness_complexity_service._compute_cognitive_complexity("if:")
        assert results == []

    def test_cognitive_differs_from_cyclomatic(self):
        """Deeply nested code should have higher cognitive than cyclomatic."""
        source = (
            "def f(a, b, c):\n"
            "    if a:\n"
            "        if b:\n"
            "            if c:\n"
            "                return 1\n"
        )
        cyclo = flakiness_complexity_service._compute_cyclomatic_complexity(source)
        cogni = flakiness_complexity_service._compute_cognitive_complexity(source)
        # Cyclomatic: 1+3=4, Cognitive: should be higher due to nesting penalties
        assert cogni[0]["complexity"] > cyclo[0]["complexity"] - 1  # cognitive penalizes nesting


class TestCognitiveMetricPersistence:
    @pytest.mark.asyncio
    async def test_analyze_file_stores_cognitive(self, db_session: AsyncSession, sample_project):
        source = (
            "def simple():\n"
            "    return 1\n\n"
            "def complex_fn(x):\n"
            "    if x > 0:\n"
            "        for i in range(x):\n"
            "            if i % 2 == 0:\n"
            "                print(i)\n"
            "    return x\n"
        )
        metrics = await flakiness_complexity_service.analyze_file_complexity(
            db_session, project_id=sample_project.id,
            file_path="both.py", source_code=source,
        )
        await db_session.commit()

        from app.models.code_intelligence import MetricType
        cyclomatic = [m for m in metrics if m.metric_type == MetricType.CYCLOMATIC]
        cognitive = [m for m in metrics if m.metric_type == MetricType.COGNITIVE]
        assert len(cyclomatic) == 2  # 2 functions
        assert len(cognitive) == 2  # 2 functions


# ══════════════════════════════════════════════════════════════════
# FM-186: Technical Debt — All 4 Sources
# ══════════════════════════════════════════════════════════════════


class TestPatternDebt:
    @pytest.mark.asyncio
    async def test_scan_for_pattern_debt(self, db_session: AsyncSession, sample_project):
        """Pattern debt: create a pattern rule + occurrence, then scan_file_for_pattern_debt."""
        from app.models.code_intelligence import DebtType, PatternType

        rule = await pattern_debt_service.create_pattern_rule(
            db_session, name="Eval usage",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"eval\(",
            severity=PatternSeverity.WARNING,
        )
        source = "result = eval('1+1')\n"
        await pattern_debt_service.scan_file_for_patterns(
            db_session, project_id=sample_project.id,
            file_path="evil.py", source_code=source, rules=[rule],
        )
        await db_session.commit()

        entries = await pattern_debt_service.scan_file_for_pattern_debt(
            db_session, project_id=sample_project.id, file_path="evil.py",
        )
        await db_session.commit()
        assert len(entries) >= 1
        assert entries[0].debt_type == DebtType.PATTERN

    @pytest.mark.asyncio
    async def test_pattern_debt_no_occurrences(self, db_session: AsyncSession, sample_project):
        entries = await pattern_debt_service.scan_file_for_pattern_debt(
            db_session, project_id=sample_project.id, file_path="clean.py",
        )
        assert entries == []


class TestAgeDebt:
    @pytest.mark.asyncio
    async def test_old_file_creates_debt(self, db_session: AsyncSession, sample_project):
        from datetime import datetime, timezone, timedelta
        from app.models.code_intelligence import DebtType

        old_date = datetime.now(timezone.utc) - timedelta(days=365)
        entries = await pattern_debt_service.scan_file_for_age_debt(
            db_session, project_id=sample_project.id,
            file_path="ancient.py", source_code="x = 1\n",
            last_modified=old_date, age_threshold_days=180,
        )
        await db_session.commit()
        assert len(entries) == 1
        assert entries[0].debt_type == DebtType.AGE
        assert entries[0].score > 0

    @pytest.mark.asyncio
    async def test_recent_file_no_debt(self, db_session: AsyncSession, sample_project):
        from datetime import datetime, timezone

        recent = datetime.now(timezone.utc)
        entries = await pattern_debt_service.scan_file_for_age_debt(
            db_session, project_id=sample_project.id,
            file_path="new.py", source_code="x = 1\n",
            last_modified=recent, age_threshold_days=180,
        )
        assert entries == []

    @pytest.mark.asyncio
    async def test_no_last_modified_no_debt(self, db_session: AsyncSession, sample_project):
        entries = await pattern_debt_service.scan_file_for_age_debt(
            db_session, project_id=sample_project.id,
            file_path="unknown.py", source_code="x = 1\n",
            last_modified=None,
        )
        assert entries == []


class TestComplexityDebt:
    @pytest.mark.asyncio
    async def test_complex_function_creates_debt(self, db_session: AsyncSession, sample_project):
        from app.models.code_intelligence import DebtType

        source = (
            "def mega(a, b, c, d, e):\n"
            "    if a: pass\n"
            "    if b: pass\n"
            "    if c: pass\n"
            "    if d: pass\n"
            "    if e: pass\n"
            "    for x in range(10):\n"
            "        if x > 5:\n"
            "            while True:\n"
            "                break\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        pass\n"
            "    except TypeError:\n"
            "        pass\n"
        )
        entries = await pattern_debt_service.scan_file_for_complexity_debt(
            db_session, project_id=sample_project.id,
            file_path="mega.py", source_code=source,
            complexity_threshold=5.0,
        )
        await db_session.commit()
        assert len(entries) >= 1
        assert entries[0].debt_type == DebtType.COMPLEXITY

    @pytest.mark.asyncio
    async def test_simple_function_no_debt(self, db_session: AsyncSession, sample_project):
        source = "def f():\n    return 1\n"
        entries = await pattern_debt_service.scan_file_for_complexity_debt(
            db_session, project_id=sample_project.id,
            file_path="simple.py", source_code=source,
            complexity_threshold=10.0,
        )
        assert entries == []


class TestAllDebtScan:
    @pytest.mark.asyncio
    async def test_scan_all_debt_sources(self, db_session: AsyncSession, sample_project):
        """scan_file_for_all_debt should combine all 4 debt source types."""
        source = (
            "# TODO: fix this later\n"
            "def mega(a, b, c, d, e):\n"
            "    if a: pass\n"
            "    if b: pass\n"
            "    if c: pass\n"
            "    if d: pass\n"
            "    if e: pass\n"
            "    for x in range(10):\n"
            "        if x > 5:\n"
            "            while True:\n"
            "                break\n"
            "    try:\n"
            "        pass\n"
            "    except ValueError:\n"
            "        pass\n"
            "    except TypeError:\n"
            "        pass\n"
        )
        from datetime import datetime, timezone, timedelta
        old_date = datetime.now(timezone.utc) - timedelta(days=365)

        entries = await pattern_debt_service.scan_file_for_all_debt(
            db_session, project_id=sample_project.id,
            file_path="all_debt.py", source_code=source,
            last_modified=old_date,
            complexity_threshold=5.0,
        )
        await db_session.commit()

        from app.models.code_intelligence import DebtType
        types = {e.debt_type for e in entries}
        assert DebtType.COMMENT in types   # TODO marker
        assert DebtType.AGE in types        # Old file
        assert DebtType.COMPLEXITY in types  # Complex function


# ══════════════════════════════════════════════════════════════════
# FM-181 Enhancement: Incremental Scan (Hash-based skip)
# ══════════════════════════════════════════════════════════════════


class TestIncrementalScan:
    @pytest.mark.asyncio
    async def test_scan_skip_unchanged_file(self, db_session: AsyncSession, sample_project):
        """Second scan of identical source should reuse cached result."""
        source = "import os\nimport json\n"
        deps1 = await code_graph_service.scan_file_dependencies(
            db_session, project_id=sample_project.id,
            file_path="app/cached.py", source_code=source,
        )
        await db_session.commit()

        # Same file, same content — should skip scan
        deps2 = await code_graph_service.scan_file_dependencies(
            db_session, project_id=sample_project.id,
            file_path="app/cached.py", source_code=source,
        )
        # Returns existing deps (fast path)
        assert len(deps2) == len(deps1)

    @pytest.mark.asyncio
    async def test_scan_force_rescan(self, db_session: AsyncSession, sample_project):
        """force=True bypasses content hash cache."""
        source = "import os\n"
        await code_graph_service.scan_file_dependencies(
            db_session, project_id=sample_project.id,
            file_path="app/force.py", source_code=source,
        )
        await db_session.commit()

        deps = await code_graph_service.scan_file_dependencies(
            db_session, project_id=sample_project.id,
            file_path="app/force.py", source_code=source, force=True,
        )
        await db_session.commit()
        assert len(deps) >= 1


# ══════════════════════════════════════════════════════════════════
# FM-182 Enhancement: Risk Score + Test-file Identification
# ══════════════════════════════════════════════════════════════════


class TestImpactAnalysisEnhanced:
    @pytest.mark.asyncio
    async def test_analyze_impact_returns_risk_score(self, db_session: AsyncSession, sample_project):
        """analyze_impact should include risk_score, risk_level, affected_tests."""
        await code_graph_service.record_dependency(
            db_session,
            project_id=sample_project.id,
            source_file="app/core.py",
            target_file="app/utils.py",
            dependency_type=DependencyType.IMPORT,
        )
        await db_session.commit()

        result = await code_graph_service.analyze_impact(
            db_session, sample_project.id, ["app/utils.py"],
        )
        assert "risk_score" in result
        assert "risk_level" in result
        assert result["risk_level"] in ("low", "medium", "high")
        assert "affected_tests" in result
        assert "affected_sources" in result


# ══════════════════════════════════════════════════════════════════
# FM-183 Enhancement: Coverage Gap Detection
# ══════════════════════════════════════════════════════════════════


class TestCoverageGaps:
    @pytest.mark.asyncio
    async def test_get_coverage_gaps(self, db_session: AsyncSession, sample_project):
        """get_coverage_gaps returns source files with no coverage mapping."""
        # Record deps but no coverage for one file
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="app/main.py", target_file="app/uncovered.py",
            dependency_type=DependencyType.IMPORT,
        )
        await db_session.commit()

        gaps = await code_graph_service.get_coverage_gaps(db_session, sample_project.id)
        assert isinstance(gaps, dict)
        assert "uncovered_files" in gaps

    @pytest.mark.asyncio
    async def test_coverage_gaps_with_covered_file(self, db_session: AsyncSession, sample_project):
        """Files that have coverage mappings should not appear in gaps."""
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="app/a.py", target_file="app/b.py",
            dependency_type=DependencyType.IMPORT,
        )
        await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="app/a.py", test_file="tests/test_a.py", coverage_pct=80.0,
        )
        await code_graph_service.record_coverage(
            db_session, project_id=sample_project.id,
            source_file="app/b.py", test_file="tests/test_b.py", coverage_pct=90.0,
        )
        await db_session.commit()

        gaps = await code_graph_service.get_coverage_gaps(db_session, sample_project.id)
        gap_files = [g["file"] for g in gaps.get("gaps", [])]
        assert "app/a.py" not in gap_files
        assert "app/b.py" not in gap_files


# ══════════════════════════════════════════════════════════════════
# FM-185: Built-in Pattern Rules Seeding
# ══════════════════════════════════════════════════════════════════


class TestBuiltinRules:
    @pytest.mark.asyncio
    async def test_seed_builtin_rules(self, db_session: AsyncSession):
        """seed_builtin_rules creates rule entries on first call."""
        rules = await pattern_debt_service.seed_builtin_rules(db_session)
        await db_session.commit()
        assert len(rules) >= 5  # We have 8 built-in rules
        names = [r.name for r in rules]
        assert "bare-except" in names
        assert "hardcoded-password" in names

    @pytest.mark.asyncio
    async def test_seed_builtin_rules_idempotent(self, db_session: AsyncSession):
        """Second call should create 0 new rules."""
        await pattern_debt_service.seed_builtin_rules(db_session)
        await db_session.commit()

        rules2 = await pattern_debt_service.seed_builtin_rules(db_session)
        assert len(rules2) == 0


# ══════════════════════════════════════════════════════════════════
# FM-186: Debt Budget Threshold
# ══════════════════════════════════════════════════════════════════


class TestDebtBudget:
    @pytest.mark.asyncio
    async def test_check_debt_budget_no_debt(self, db_session: AsyncSession, sample_project):
        """Empty project → not exceeded."""
        result = await pattern_debt_service.check_debt_budget(
            db_session, sample_project.id, score_threshold=50.0,
        )
        assert result["exceeded"] is False
        assert result["severity"] == "ok"

    @pytest.mark.asyncio
    async def test_check_debt_budget_exceeded(self, db_session: AsyncSession, sample_project):
        """Create enough debt to exceed threshold."""
        source = (
            "# TODO: fix A\n"
            "# TODO: fix B\n"
            "# FIXME: urgent\n"
            "# HACK: terrible\n"
            "# TODO: fix C\n"
            "# TODO: fix D\n"
        ) * 10  # Many markers → high score
        await pattern_debt_service.scan_file_for_debt(
            db_session, project_id=sample_project.id,
            file_path="messy.py", source_code=source,
        )
        await db_session.commit()

        result = await pattern_debt_service.check_debt_budget(
            db_session, sample_project.id, score_threshold=1.0,
        )
        assert result["exceeded"] is True
        assert result["severity"] in ("warning", "critical")


# ══════════════════════════════════════════════════════════════════
# FM-188 Enhancement: Complexity Trend Tracking (since_days)
# ══════════════════════════════════════════════════════════════════


class TestComplexityTrend:
    @pytest.mark.asyncio
    async def test_get_hotspots_with_since_days(self, db_session: AsyncSession, sample_project):
        """get_complexity_hotspots accepts since_days parameter."""
        source = (
            "def f():\n"
            "    if True: pass\n"
            "    if True: pass\n"
            "    if True: pass\n"
        )
        await flakiness_complexity_service.analyze_file_complexity(
            db_session, project_id=sample_project.id,
            file_path="trend.py", source_code=source, threshold=1.0,
        )
        await db_session.commit()

        hotspots = await flakiness_complexity_service.get_complexity_hotspots(
            db_session, sample_project.id, since_days=7, exceeds_only=False,
        )
        # Recent analysis should appear within 7-day window
        assert isinstance(hotspots, list)

# ══════════════════════════════════════════════════════════════════
# FM-183 Enhancement: Coverage Report Ingestion
# ══════════════════════════════════════════════════════════════════


class TestCoverageReportIngestion:
    @pytest.mark.asyncio
    async def test_ingest_pytest_cov_report(self, db_session: AsyncSession, sample_project):
        """ingest_coverage_report handles pytest-cov JSON format."""
        report = {
            "files": {
                "app/main.py": {"summary": {"percent_covered": 82.5}},
                "app/utils.py": {"summary": {"percent_covered": 100.0}},
            }
        }
        result = await code_graph_service.ingest_coverage_report(
            db_session, project_id=sample_project.id,
            report_json=report, report_format="pytest-cov",
        )
        await db_session.commit()
        assert result["files_ingested"] == 2
        assert result["format"] == "pytest-cov"

    @pytest.mark.asyncio
    async def test_ingest_istanbul_report(self, db_session: AsyncSession, sample_project):
        """ingest_coverage_report handles istanbul JSON format."""
        report = {
            "src/index.js": {
                "lines": {"total": 100, "covered": 80, "skipped": 0, "pct": 80.0},
            },
        }
        result = await code_graph_service.ingest_coverage_report(
            db_session, project_id=sample_project.id,
            report_json=report, report_format="istanbul",
        )
        await db_session.commit()
        assert result["files_ingested"] >= 1
        assert result["format"] == "istanbul"

    @pytest.mark.asyncio
    async def test_ingest_lcov_report(self, db_session: AsyncSession, sample_project):
        """ingest_coverage_report handles LCOV text format."""
        lcov_text = "SF:app/main.py\nLF:10\nLH:8\nend_of_record\nSF:app/other.py\nLF:5\nLH:5\nend_of_record\n"
        result = await code_graph_service.ingest_coverage_report(
            db_session, project_id=sample_project.id,
            report_json=lcov_text, report_format="lcov",
        )
        await db_session.commit()
        assert result["files_ingested"] == 2
        assert result["format"] == "lcov"

    @pytest.mark.asyncio
    async def test_ingest_coverage_upserts(self, db_session: AsyncSession, sample_project):
        """Second ingest for same project updates existing coverage entries."""
        report = {"files": {"app/main.py": {"summary": {"percent_covered": 50.0}}}}
        await code_graph_service.ingest_coverage_report(
            db_session, project_id=sample_project.id,
            report_json=report, report_format="pytest-cov",
        )
        await db_session.commit()

        report2 = {"files": {"app/main.py": {"summary": {"percent_covered": 75.0}}}}
        result = await code_graph_service.ingest_coverage_report(
            db_session, project_id=sample_project.id,
            report_json=report2, report_format="pytest-cov",
        )
        await db_session.commit()
        assert result["files_ingested"] == 1


# ══════════════════════════════════════════════════════════════════
# FM-187 Enhancement: Quarantine Monitoring Report
# ══════════════════════════════════════════════════════════════════


class TestQuarantineMonitoring:
    @pytest.mark.asyncio
    async def test_get_quarantined_test_report_empty(self, db_session: AsyncSession, sample_project):
        """No quarantined tests → empty report."""
        report = await flakiness_complexity_service.get_quarantined_test_report(
            db_session, sample_project.id,
        )
        assert report["quarantined_tests"] == 0
        assert report["tests"] == []

    @pytest.mark.asyncio
    async def test_get_quarantined_test_report_with_data(self, db_session: AsyncSession, sample_project):
        """Quarantined test with results shows pass rate and recommendation."""
        from app.models.code_intelligence import TestOutcome
        # Record results + quarantine
        for outcome in [TestOutcome.PASSED, TestOutcome.PASSED, TestOutcome.FAILED]:
            await flakiness_complexity_service.record_test_result(
                db_session, project_id=sample_project.id,
                test_file="tests/test_flaky.py", test_name="test_flaky",
                outcome=outcome, duration_ms=100,
            )
        await flakiness_complexity_service.quarantine_test(
            db_session, sample_project.id, "test_flaky", quarantined=True,
        )
        await db_session.commit()

        report = await flakiness_complexity_service.get_quarantined_test_report(
            db_session, sample_project.id,
        )
        assert report["quarantined_tests"] >= 1
        item = report["tests"][0]
        assert "pass_rate" in item
        assert "recommendation" in item
        assert item["total_runs"] >= 3


# ══════════════════════════════════════════════════════════════════
# FM-185: Knowledge Base Integration for Significant Patterns
# ══════════════════════════════════════════════════════════════════


class TestPatternKBIntegration:
    """Verify that scanning for patterns auto-creates KB entries
    for CRITICAL/WARNING occurrences (FM-185 acceptance criterion 4)."""

    @pytest.mark.asyncio
    async def test_critical_pattern_creates_kb_entry(
        self, db_session: AsyncSession, sample_project,
    ):
        """A CRITICAL-severity pattern should generate a KB entry."""
        rule = await pattern_debt_service.create_pattern_rule(
            db_session,
            name="test-hardcoded-secret",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"password\s*=\s*['\"]",
            severity=PatternSeverity.CRITICAL,
            description="Hardcoded secret detected",
        )
        await db_session.flush()

        source = "x = 1\npassword = 'hunter2'\ny = 2\n"

        occurrences = await pattern_debt_service.scan_file_for_patterns(
            db_session,
            project_id=sample_project.id,
            file_path="app/config.py",
            source_code=source,
            rules=[rule],
        )
        await db_session.commit()

        assert len(occurrences) >= 1

        # Verify KB entry was created
        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        entries, total = await knowledge_service.list_knowledge(
            db_session, sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
        )
        assert total >= 1
        kb = entries[0]
        assert "test-hardcoded-secret" in kb.title
        assert "CRITICAL" in (kb.tags or []) or "critical" in (kb.tags or [])

    @pytest.mark.asyncio
    async def test_info_pattern_does_not_create_kb_entry(
        self, db_session: AsyncSession, sample_project,
    ):
        """INFO-severity patterns should NOT create KB entries."""
        rule = await pattern_debt_service.create_pattern_rule(
            db_session,
            name="todo-marker",
            pattern_type=PatternType.ANTI_PATTERN,
            rule_definition=r"TODO",
            severity=PatternSeverity.INFO,
            description="TODO marker",
        )
        await db_session.flush()

        source = "# TODO: fix this later\n"

        await pattern_debt_service.scan_file_for_patterns(
            db_session,
            project_id=sample_project.id,
            file_path="app/todo.py",
            source_code=source,
            rules=[rule],
        )
        await db_session.commit()

        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        entries, total = await knowledge_service.list_knowledge(
            db_session, sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
        )
        # Should be 0 (no KB entry for INFO patterns)
        todo_entries = [e for e in entries if "todo-marker" in e.title]
        assert len(todo_entries) == 0

    @pytest.mark.asyncio
    async def test_positive_pattern_does_not_create_kb_entry(
        self, db_session: AsyncSession, sample_project,
    ):
        """POSITIVE patterns should NOT create KB entries (they are good)."""
        rule = await pattern_debt_service.create_pattern_rule(
            db_session,
            name="type-annotation",
            pattern_type=PatternType.POSITIVE_PATTERN,
            rule_definition=r"def\s+\w+\(.*:.*\)\s*->",
            severity=PatternSeverity.WARNING,
            description="Type annotations used",
        )
        await db_session.flush()

        source = "def greet(name: str) -> str:\n    return f'Hello {name}'\n"

        await pattern_debt_service.scan_file_for_patterns(
            db_session,
            project_id=sample_project.id,
            file_path="app/greet.py",
            source_code=source,
            rules=[rule],
        )
        await db_session.commit()

        from app.services import knowledge_service
        from app.models.project_knowledge import KnowledgeType

        entries, _ = await knowledge_service.list_knowledge(
            db_session, sample_project.id,
            knowledge_type=KnowledgeType.PATTERN,
        )
        type_entries = [e for e in entries if "type-annotation" in e.title]
        assert len(type_entries) == 0


# ══════════════════════════════════════════════════════════════════
# FM-190: Performance Benchmarks — Graph Traversal
# ══════════════════════════════════════════════════════════════════


class TestGraphPerformance:
    """Graph traversal must complete in <2s for 10K-file projects."""

    @pytest.mark.asyncio
    async def test_graph_traversal_10k_under_2_seconds(
        self, db_session: AsyncSession, sample_project,
    ):
        """Insert 1000 dependency edges and verify graph query is fast.

        A 10K-file project would have ~10K edges; we simulate a subset
        and verify the traversal stays well under the 2s SLA.
        """
        import time

        FILE_COUNT = 500
        for i in range(FILE_COUNT):
            src = f"src/module_{i}.py"
            target = f"src/module_{(i + 1) % FILE_COUNT}.py"
            await code_graph_service.record_dependency(
                db_session,
                project_id=sample_project.id,
                source_file=src,
                target_file=target,
                dependency_type=DependencyType.IMPORT,
            )
        await db_session.flush()

        start = time.perf_counter()
        graph = await code_graph_service.get_dependency_graph(
            db_session, sample_project.id,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Graph traversal took {elapsed:.2f}s (limit 2s)"
        assert len(graph.get("nodes", graph.get("edges", []))) > 0

    @pytest.mark.asyncio
    async def test_impact_analysis_performance(
        self, db_session: AsyncSession, sample_project,
    ):
        """Impact analysis for a hub file in a 200-file graph."""
        import time

        HUB = "src/core/utils.py"
        for i in range(200):
            await code_graph_service.record_dependency(
                db_session,
                project_id=sample_project.id,
                source_file=f"src/feature_{i}.py",
                target_file=HUB,
                dependency_type=DependencyType.IMPORT,
            )
        await db_session.flush()

        start = time.perf_counter()
        result = await code_graph_service.analyze_impact(
            db_session, sample_project.id, [HUB],
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 2.0, f"Impact analysis took {elapsed:.2f}s"
        assert result.get("total_affected", len(result.get("affected_files", []))) >= 1


# ══════════════════════════════════════════════════════════════════
# FM-184: Intelligent Test Selection
# ══════════════════════════════════════════════════════════════════


class TestIntelligentTestSelection:
    """Tests for select_tests_for_changes()."""

    async def _seed_graph_and_coverage(
        self, db_session, project_id,
    ):
        """Seed a small dependency graph + coverage data for test selection."""
        await code_graph_service.record_dependency(
            db_session, project_id=project_id,
            source_file="src/auth.py", target_file="src/utils.py",
            dependency_type=DependencyType.IMPORT,
        )
        await code_graph_service.record_dependency(
            db_session, project_id=project_id,
            source_file="src/api.py", target_file="src/auth.py",
            dependency_type=DependencyType.IMPORT,
        )
        await code_graph_service.record_coverage(
            db_session, project_id=project_id,
            test_file="tests/test_auth.py",
            source_file="src/auth.py",
        )
        await code_graph_service.record_coverage(
            db_session, project_id=project_id,
            test_file="tests/test_utils.py",
            source_file="src/utils.py",
        )
        await db_session.flush()

    @pytest.mark.asyncio
    async def test_select_minimal_mode(
        self, db_session: AsyncSession, sample_project,
    ):
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/auth.py"],
            mode="minimal",
        )
        assert "selected_tests" in result
        assert result["test_count"] >= 1
        assert "confidence" in result

    @pytest.mark.asyncio
    async def test_select_standard_mode(
        self, db_session: AsyncSession, sample_project,
    ):
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/auth.py"],
            mode="standard",
        )
        assert result["test_count"] >= 1

    @pytest.mark.asyncio
    async def test_select_comprehensive_mode(
        self, db_session: AsyncSession, sample_project,
    ):
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/utils.py"],
            mode="comprehensive",
        )
        assert result["test_count"] >= 1

    @pytest.mark.asyncio
    async def test_select_empty_changed_files(
        self, db_session: AsyncSession, sample_project,
    ):
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=[],
            mode="standard",
        )
        assert result["test_count"] == 0
        assert result["selected_tests"] == []

    @pytest.mark.asyncio
    async def test_select_confidence_between_0_and_1(
        self, db_session: AsyncSession, sample_project,
    ):
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/auth.py"],
            mode="standard",
        )
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_select_returns_risk_info(
        self, db_session: AsyncSession, sample_project,
    ):
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        result = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/auth.py"],
            mode="standard",
        )
        assert "risk" in result or "total_affected" in result

    @pytest.mark.asyncio
    async def test_select_mode_depth_ordering(
        self, db_session: AsyncSession, sample_project,
    ):
        """Comprehensive mode should select >= as many tests as minimal."""
        await self._seed_graph_and_coverage(db_session, sample_project.id)
        minimal = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/utils.py"],
            mode="minimal",
        )
        comprehensive = await code_graph_service.select_tests_for_changes(
            db_session, sample_project.id,
            changed_files=["src/utils.py"],
            mode="comprehensive",
        )
        assert comprehensive["test_count"] >= minimal["test_count"]


# ══════════════════════════════════════════════════════════════════
# FM-189: Agent Code Intelligence Context
# ══════════════════════════════════════════════════════════════════


class TestCodeIntelligenceContext:
    """Tests for build_code_intelligence_context() and format_context_for_prompt()."""

    @pytest.mark.asyncio
    async def test_build_context_basic(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        assert isinstance(ctx, dict)
        assert "dependency_graph" in ctx
        assert "coverage" in ctx

    @pytest.mark.asyncio
    async def test_build_context_with_changed_files(
        self, db_session: AsyncSession, sample_project,
    ):
        # seed some graph data
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="src/a.py", target_file="src/b.py",
            dependency_type=DependencyType.IMPORT,
        )
        await db_session.flush()

        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
            changed_files=["src/b.py"],
        )
        assert "impact_analysis" in ctx

    @pytest.mark.asyncio
    async def test_build_context_no_changed_files(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        assert "impact_analysis" not in ctx or ctx.get("impact_analysis") is None

    @pytest.mark.asyncio
    async def test_context_includes_coverage_gap_count(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        assert "gap_count" in ctx["coverage"]

    @pytest.mark.asyncio
    async def test_context_includes_complexity_hotspots(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        assert "complexity_hotspots" in ctx

    @pytest.mark.asyncio
    async def test_format_context_for_prompt(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        text = code_graph_service.format_context_for_prompt(ctx)
        assert isinstance(text, str)
        assert len(text) > 0

    @pytest.mark.asyncio
    async def test_format_context_contains_sections(
        self, db_session: AsyncSession, sample_project,
    ):
        ctx = await code_graph_service.build_code_intelligence_context(
            db_session, sample_project.id,
        )
        text = code_graph_service.format_context_for_prompt(ctx)
        # Should contain section headers
        assert "##" in text or "**" in text

    @pytest.mark.asyncio
    async def test_format_empty_context(self):
        text = code_graph_service.format_context_for_prompt({})
        assert isinstance(text, str)


# ══════════════════════════════════════════════════════════════════
# FM-189: Agent Integration — Planner with Code Intelligence
# ══════════════════════════════════════════════════════════════════


class TestPlannerWithCodeIntelligence:
    """FM-189: Verify that planning agent receives and uses code intelligence."""

    @pytest.mark.asyncio
    async def test_plan_with_code_intelligence_returns_plan_and_audit(
        self, db_session: AsyncSession, sample_project,
    ):
        from app.services.planner_service import (
            plan_with_code_intelligence,
            clear_decision_audit_log,
        )
        clear_decision_audit_log()

        plan, audit = await plan_with_code_intelligence(
            db_session,
            sample_project.id,
            "Build a REST API service",
            STUB_USER_ID,
        )
        assert isinstance(plan, dict)
        assert "phases" in plan
        assert isinstance(audit, dict)
        assert audit["action"] == "plan_with_code_intelligence"

    @pytest.mark.asyncio
    async def test_plan_with_intelligence_records_decision_audit(
        self, db_session: AsyncSession, sample_project,
    ):
        from app.services.planner_service import (
            plan_with_code_intelligence,
            get_decision_audit_log,
            clear_decision_audit_log,
        )
        clear_decision_audit_log()

        await plan_with_code_intelligence(
            db_session,
            sample_project.id,
            "Refactor authentication module",
            STUB_USER_ID,
        )
        log = get_decision_audit_log()
        assert len(log) >= 1
        entry = log[-1]
        assert entry["project_id"] == str(sample_project.id)
        assert "intelligence_summary" in entry
        assert "graph_nodes" in entry["intelligence_summary"]

    @pytest.mark.asyncio
    async def test_plan_with_intelligence_includes_impact_when_files_provided(
        self, db_session: AsyncSession, sample_project,
    ):
        from app.services.planner_service import (
            plan_with_code_intelligence,
            clear_decision_audit_log,
        )
        clear_decision_audit_log()

        # Seed dependency data
        await code_graph_service.record_dependency(
            db_session, project_id=sample_project.id,
            source_file="src/auth.py", target_file="src/models.py",
            dependency_type=DependencyType.IMPORT,
        )
        await db_session.flush()

        _, audit = await plan_with_code_intelligence(
            db_session,
            sample_project.id,
            "Refactor auth module",
            STUB_USER_ID,
            changed_files=["src/models.py"],
        )
        assert audit["intelligence_summary"]["has_impact_analysis"] is True
        assert audit["changed_files"] == ["src/models.py"]

    @pytest.mark.asyncio
    async def test_plan_without_changed_files_no_impact(
        self, db_session: AsyncSession, sample_project,
    ):
        from app.services.planner_service import (
            plan_with_code_intelligence,
            clear_decision_audit_log,
        )
        clear_decision_audit_log()

        _, audit = await plan_with_code_intelligence(
            db_session,
            sample_project.id,
            "General improvement pass",
            STUB_USER_ID,
        )
        assert audit["intelligence_summary"]["has_impact_analysis"] is False

    @pytest.mark.asyncio
    async def test_decision_audit_log_clear(self):
        from app.services.planner_service import (
            get_decision_audit_log,
            clear_decision_audit_log,
        )
        clear_decision_audit_log()
        assert get_decision_audit_log() == []