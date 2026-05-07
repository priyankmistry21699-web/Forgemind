"""FM-230: Security scan agent.

Runs static analysis (bandit for Python, npm audit for JS) in the sandbox,
persists SecurityFinding records, and auto-creates approval gates for HIGH/CRITICAL.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.task import Task
    from app.models.agent import Agent

logger = logging.getLogger("forgemind.worker.agents.security_scan")


async def handle(db: "AsyncSession", task: "Task", agent: "Agent") -> dict:
    from worker.tools.builtin_tools import RunCommandTool

    runner = RunCommandTool()
    findings: list[dict] = []

    # --- bandit (Python SAST) ---
    bandit_result = await runner.execute(
        command="bandit -r . -f json -q", timeout=60
    )
    if bandit_result.get("success") or bandit_result.get("output"):
        findings += _parse_bandit(bandit_result.get("output", ""))

    # --- npm audit (JS dependency scan) ---
    npm_result = await runner.execute(
        command="npm audit --json --audit-level=moderate", timeout=60
    )
    if npm_result.get("output"):
        findings += _parse_npm_audit(npm_result.get("output", ""))

    # Persist findings and create approval gates for HIGH/CRITICAL
    created, approval_count = await _persist_findings(db, task, findings)

    return {
        "artifact_title": f"Security Scan: {task.title}",
        "artifact_content": _findings_summary(findings),
        "artifact_type": "security_report",
        "findings_count": created,
        "approval_gates_created": approval_count,
    }


def _parse_bandit(output: str) -> list[dict]:
    findings = []
    try:
        data = json.loads(output)
        for r in data.get("results", []):
            sev = r.get("issue_severity", "LOW").upper()
            findings.append(
                {
                    "source": "bandit",
                    "severity": sev.lower() if sev in ("LOW", "MEDIUM", "HIGH") else "medium",
                    "title": r.get("test_name", "Unknown"),
                    "description": r.get("issue_text", ""),
                    "file_path": r.get("filename"),
                    "line_number": r.get("line_number"),
                    "cwe_id": r.get("issue_cwe", {}).get("id") if isinstance(r.get("issue_cwe"), dict) else None,
                }
            )
    except (json.JSONDecodeError, ValueError):
        pass
    return findings[:100]


def _parse_npm_audit(output: str) -> list[dict]:
    findings = []
    try:
        data = json.loads(output)
        vulns = data.get("vulnerabilities", {})
        for pkg_name, info in vulns.items():
            sev = info.get("severity", "moderate")
            severity_map = {
                "critical": "critical",
                "high": "high",
                "moderate": "medium",
                "low": "low",
            }
            findings.append(
                {
                    "source": "npm_audit",
                    "severity": severity_map.get(sev, "medium"),
                    "title": f"{pkg_name}: {sev} vulnerability",
                    "description": "; ".join(
                        v.get("title", "") for v in info.get("via", []) if isinstance(v, dict)
                    )[:500],
                    "file_path": "package.json",
                    "line_number": None,
                    "cve_id": _extract_cve(info),
                }
            )
    except (json.JSONDecodeError, ValueError):
        pass
    return findings[:100]


def _extract_cve(info: dict) -> str | None:
    for via in info.get("via", []):
        if isinstance(via, dict):
            cve = via.get("cve")
            if cve:
                return cve[0] if isinstance(cve, list) else str(cve)
    return None


def _findings_summary(findings: list[dict]) -> str:
    if not findings:
        return "No security findings detected."
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.get("severity", "unknown")] = counts.get(f.get("severity", "unknown"), 0) + 1
    lines = ["## Security Scan Summary\n"]
    for sev in ("critical", "high", "medium", "low"):
        if counts.get(sev):
            lines.append(f"- **{sev.upper()}**: {counts[sev]}")
    lines.append(f"\nTotal: {len(findings)} findings")
    return "\n".join(lines)


async def _persist_findings(
    db: "AsyncSession", task: "Task", findings: list[dict]
) -> tuple[int, int]:
    from app.models.agent_intelligence import FindingSeverity, FindingSource, SecurityFinding
    from app.models.approval_request import ApprovalRequest, ApprovalStatus

    project_id = task.run.project_id if hasattr(task, "run") and task.run else None
    created = 0
    approval_count = 0

    for f in findings:
        try:
            sev = FindingSeverity(f.get("severity", "medium"))
        except ValueError:
            sev = FindingSeverity.MEDIUM

        try:
            src = FindingSource(f.get("source", "manual"))
        except ValueError:
            src = FindingSource.MANUAL

        finding = SecurityFinding(
            project_id=project_id,
            run_id=task.run_id,
            severity=sev,
            source=src,
            title=str(f.get("title", "Unknown"))[:500],
            description=str(f.get("description", ""))[:2000] or None,
            file_path=f.get("file_path"),
            line_number=f.get("line_number"),
            cwe_id=str(f.get("cwe_id", ""))[:50] or None,
            cve_id=str(f.get("cve_id", ""))[:50] or None,
            raw_output=f,
        )
        db.add(finding)

        # Auto-gate HIGH and CRITICAL findings
        if sev in (FindingSeverity.HIGH, FindingSeverity.CRITICAL) and project_id:
            approval = ApprovalRequest(
                project_id=project_id,
                run_id=task.run_id,
                task_id=task.id,
                title=f"[{sev.value.upper()}] Security: {str(f.get('title', ''))[:200]}",
                description=str(f.get("description", ""))[:500] or None,
                status=ApprovalStatus.PENDING,
            )
            db.add(approval)
            approval_count += 1

        created += 1

    if created:
        try:
            await db.flush()
        except Exception as exc:
            logger.warning("security_scan: could not persist findings (%s)", exc)
            return 0, 0

    return created, approval_count
