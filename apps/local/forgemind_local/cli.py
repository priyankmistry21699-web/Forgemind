"""ForgeMind Local CLI — main entry-point.

Usage:
    forgemind init          # initialise local workspace
    forgemind status        # show local health/status
    forgemind repo attach   # attach & index current repo
    forgemind ask "..."     # ask about local codebase
    forgemind exec "..."    # bounded local execution
    forgemind patch ...     # patch workflow commands
    forgemind pr prepare    # generate PR materials
    forgemind snapshot ...  # export / import handoff
    forgemind ide setup     # generate editor config
"""

from __future__ import annotations

import datetime as _dt
import json
import os

import click
from rich.console import Console
from rich.table import Table

from forgemind_local.config import (
    LocalConfig,
    detect_repo_root,
    ensure_directories,
    load_config,
    save_config,
)

console = Console()

# ════════════════════════════════════════════════════════════════════
# Root group
# ════════════════════════════════════════════════════════════════════


@click.group()
@click.version_option(package_name="forgemind-local")
def main() -> None:
    """ForgeMind Local — developer workstation companion."""


# ════════════════════════════════════════════════════════════════════
# FM-091  init / status
# ════════════════════════════════════════════════════════════════════


@main.command()
@click.option("--path", default=None, help="Repo root (default: auto-detect).")
def init(path: str | None) -> None:
    """Initialise a local ForgeMind workspace in the current repo."""
    repo_root = path or detect_repo_root()
    if repo_root is None:
        console.print(
            "[red]Could not detect a git repository.[/red] Pass --path or run from inside a repo."
        )
        raise SystemExit(1)

    existing = load_config(repo_root)
    if existing is not None:
        console.print(f"[yellow]Already initialised[/yellow] at {repo_root}")
        raise SystemExit(0)

    cfg = LocalConfig.default(repo_root)
    cfg.created_at = _dt.datetime.now(_dt.timezone.utc).isoformat()
    dirs = ensure_directories(cfg)
    config_path = save_config(cfg)

    console.print(
        f"[green]✓[/green] Initialised ForgeMind Local in [bold]{repo_root}[/bold]"
    )
    console.print(f"  config  → {config_path}")
    for d in dirs:
        console.print(f"  dir     → {d}")


@main.command()
@click.option("--path", default=None, help="Repo root.")
def status(path: str | None) -> None:
    """Show local ForgeMind health/status."""
    repo_root = path or detect_repo_root()
    if repo_root is None:
        console.print("[red]Not inside a git repository.[/red]")
        raise SystemExit(1)

    cfg = load_config(repo_root)
    if cfg is None:
        console.print("[yellow]Not initialised.[/yellow] Run `forgemind init` first.")
        raise SystemExit(1)

    table = Table(title="ForgeMind Local Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value")

    table.add_row("repo_root", cfg.repo_root)
    table.add_row("workspace_slug", cfg.workspace_slug)
    table.add_row("project_slug", cfg.project_slug)
    table.add_row("mode", cfg.mode)
    table.add_row("execution_policy", cfg.execution_policy)
    table.add_row("sync_enabled", str(cfg.sync_enabled))
    table.add_row("editor_integration", str(cfg.editor_integration))
    table.add_row("created_at", cfg.created_at or "—")

    # FM-119: Template & phase-routing awareness
    table.add_row("template_slug", cfg.template_slug or "—")
    if cfg.phase_profiles:
        profiles_str = ", ".join(f"{p}→{a}" for p, a in cfg.phase_profiles.items())
        table.add_row("phase_profiles", profiles_str)
    else:
        table.add_row("phase_profiles", "— (capability-based)")

    # Index status
    idx_dir = os.path.join(cfg.repo_root, ".forgemind", "index")
    idx_file = os.path.join(idx_dir, "repo_manifest.json")
    if os.path.isfile(idx_file):
        table.add_row("index", "[green]indexed[/green]")
    else:
        table.add_row("index", "[yellow]not indexed[/yellow]")

    console.print(table)


# ════════════════════════════════════════════════════════════════════
# FM-092  repo attach / index
# ════════════════════════════════════════════════════════════════════


@main.command("attach")
@click.option("--path", default=None, help="Repo root.")
def repo_attach(path: str | None) -> None:
    """Attach the current repo and build a local index."""
    repo_root = path or detect_repo_root()
    if repo_root is None:
        console.print("[red]Not inside a git repository.[/red]")
        raise SystemExit(1)

    cfg = load_config(repo_root)
    if cfg is None:
        console.print("[yellow]Not initialised.[/yellow] Run `forgemind init` first.")
        raise SystemExit(1)

    from forgemind_local.repo_index import build_repo_index

    console.print(f"[cyan]Scanning[/cyan] {repo_root} …")
    manifest = build_repo_index(repo_root)
    idx_dir = os.path.join(repo_root, ".forgemind", "index")
    os.makedirs(idx_dir, exist_ok=True)
    out_path = os.path.join(idx_dir, "repo_manifest.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, default=str)

    console.print(
        f"[green]✓[/green] Indexed {manifest['total_files']} files ({manifest['total_lines']} lines)"
    )
    console.print(f"  manifest → {out_path}")

    # Language breakdown
    if manifest.get("language_breakdown"):
        lang_tbl = Table(title="Languages")
        lang_tbl.add_column("Language")
        lang_tbl.add_column("Files", justify="right")
        lang_tbl.add_column("Lines", justify="right")
        for lang, info in sorted(
            manifest["language_breakdown"].items(), key=lambda kv: -kv[1]["lines"]
        ):
            lang_tbl.add_row(lang, str(info["files"]), str(info["lines"]))
        console.print(lang_tbl)


# ════════════════════════════════════════════════════════════════════
# FM-093  ask  (local chat)
# ════════════════════════════════════════════════════════════════════


@main.command()
@click.argument("question")
@click.option("--file", "target_file", default=None, help="Focus on a specific file.")
@click.option("--path", default=None, help="Repo root.")
def ask(question: str, target_file: str | None, path: str | None) -> None:
    """Ask a question about the local codebase."""
    repo_root = path or detect_repo_root()
    if repo_root is None:
        console.print("[red]Not inside a git repository.[/red]")
        raise SystemExit(1)

    cfg = load_config(repo_root)
    if cfg is None:
        console.print("[yellow]Not initialised.[/yellow] Run `forgemind init` first.")
        raise SystemExit(1)

    from forgemind_local.local_chat import answer_question

    result = answer_question(repo_root, question, target_file=target_file)
    console.print()
    console.print(result["answer"])
    if result.get("citations"):
        console.print()
        console.print("[dim]References:[/dim]")
        for c in result["citations"]:
            console.print(f"  • {c}")


# ════════════════════════════════════════════════════════════════════
# FM-094  exec  (bounded local execution)
# ════════════════════════════════════════════════════════════════════


@main.command("exec")
@click.argument("command")
@click.option("--timeout", default=60, help="Timeout in seconds.")
@click.option("--path", default=None, help="Repo root.")
def local_exec(command: str, timeout: int, path: str | None) -> None:
    """Run a bounded command locally (test, lint, build …)."""
    repo_root = path or detect_repo_root()
    if repo_root is None:
        console.print("[red]Not inside a git repository.[/red]")
        raise SystemExit(1)

    cfg = load_config(repo_root)
    if cfg is None:
        console.print("[yellow]Not initialised.[/yellow] Run `forgemind init` first.")
        raise SystemExit(1)

    from forgemind_local.local_exec import run_local_command

    result = run_local_command(
        repo_root,
        command,
        timeout_s=timeout,
        policy=cfg.execution_policy,
        template_slug=cfg.template_slug,
        phase_profiles=cfg.phase_profiles,
    )

    if result["blocked"]:
        console.print(f"[red]✗ Blocked[/red]: {result['reason']}")
        raise SystemExit(1)

    console.print(f"[cyan]$ {command}[/cyan]  (timeout={timeout}s)")
    if result["stdout"]:
        console.print(result["stdout"])
    if result["stderr"]:
        console.print(f"[yellow]{result['stderr']}[/yellow]")
    code = result["returncode"]
    colour = "green" if code == 0 else "red"
    console.print(f"[{colour}]exit {code}[/{colour}]  ({result['duration_s']:.1f}s)")


# ════════════════════════════════════════════════════════════════════
# FM-095  patch  (generate / preview / apply / reject)
# ════════════════════════════════════════════════════════════════════


@main.group()
def patch() -> None:
    """Local patch workflow commands."""


@patch.command("generate")
@click.argument("description")
@click.option("--file", "target_file", default=None, help="Target file for patch.")
@click.option("--path", default=None, help="Repo root.")
def patch_generate(description: str, target_file: str | None, path: str | None) -> None:
    """Generate a patch suggestion."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_patch import generate_patch

    result = generate_patch(repo_root, description, target_file=target_file)
    console.print(f"[green]✓[/green] Patch generated: {result['patch_id']}")
    console.print(f"  file → {result['patch_path']}")


@patch.command("list")
@click.option("--path", default=None)
def patch_list(path: str | None) -> None:
    """List pending patches."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_patch import list_patches

    patches = list_patches(repo_root)
    if not patches:
        console.print("[dim]No patches.[/dim]")
        return
    tbl = Table(title="Patches")
    tbl.add_column("ID")
    tbl.add_column("Status")
    tbl.add_column("Description")
    tbl.add_column("Created")
    for p in patches:
        tbl.add_row(
            p["patch_id"][:8], p["status"], p["description"][:50], p["created_at"][:19]
        )
    console.print(tbl)


@patch.command("preview")
@click.argument("patch_id")
@click.option("--path", default=None)
def patch_preview(patch_id: str, path: str | None) -> None:
    """Preview a patch diff."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_patch import preview_patch

    diff = preview_patch(repo_root, patch_id)
    if diff is None:
        console.print("[red]Patch not found.[/red]")
        raise SystemExit(1)
    console.print(diff)


@patch.command("apply")
@click.argument("patch_id")
@click.option("--path", default=None)
def patch_apply(patch_id: str, path: str | None) -> None:
    """Apply a patch to the working tree."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_patch import apply_patch

    ok = apply_patch(repo_root, patch_id)
    if ok:
        console.print(f"[green]✓[/green] Patch {patch_id[:8]} applied.")
    else:
        console.print("[red]✗ Failed to apply.[/red]")
        raise SystemExit(1)


@patch.command("reject")
@click.argument("patch_id")
@click.option("--path", default=None)
def patch_reject(patch_id: str, path: str | None) -> None:
    """Reject/discard a patch."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_patch import reject_patch

    reject_patch(repo_root, patch_id)
    console.print(f"[yellow]Patch {patch_id[:8]} rejected.[/yellow]")


# ════════════════════════════════════════════════════════════════════
# FM-096  pr prepare
# ════════════════════════════════════════════════════════════════════


@main.group()
def pr() -> None:
    """PR preparation commands."""


@pr.command("prepare")
@click.option("--base", default="main", help="Base branch to diff against.")
@click.option("--path", default=None)
def pr_prepare(base: str, path: str | None) -> None:
    """Generate PR summary, checklist, and risk analysis."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_pr import prepare_pr

    result = prepare_pr(repo_root, base_branch=base)
    console.print(result["markdown"])
    out = os.path.join(repo_root, ".forgemind", "state", "pr_summary.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(result["markdown"])
    console.print(f"\n[green]✓[/green] saved → {out}")


# ════════════════════════════════════════════════════════════════════
# FM-097  ide setup
# ════════════════════════════════════════════════════════════════════


@main.group()
def ide() -> None:
    """IDE / editor integration commands."""


@ide.command("setup")
@click.option("--editor", default="vscode", type=click.Choice(["vscode"]))
@click.option("--path", default=None)
def ide_setup(editor: str, path: str | None) -> None:
    """Generate editor task/config files."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.ide_integration import setup_editor

    files = setup_editor(repo_root, editor)
    for f in files:
        console.print(f"[green]✓[/green] {f}")


# ════════════════════════════════════════════════════════════════════
# FM-099  snapshot export / import
# ════════════════════════════════════════════════════════════════════


@main.group()
def snapshot() -> None:
    """Handoff / snapshot commands."""


@snapshot.command("export")
@click.option("--path", default=None)
@click.option("--output", default=None, help="Output path for the bundle.")
def snapshot_export(path: str | None, output: str | None) -> None:
    """Export a local handoff snapshot bundle."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_handoff import export_snapshot

    bundle_path = export_snapshot(repo_root, output_path=output)
    console.print(f"[green]✓[/green] Snapshot exported → {bundle_path}")


@snapshot.command("import")
@click.argument("bundle")
@click.option("--path", default=None)
def snapshot_import(bundle: str, path: str | None) -> None:
    """Import a handoff snapshot bundle."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    from forgemind_local.local_handoff import import_snapshot

    import_snapshot(bundle, repo_root)
    console.print(f"[green]✓[/green] Snapshot imported into {repo_root}")


# ════════════════════════════════════════════════════════════════════
# FM-129  checkpoint / confidence / review (local API wrappers)
# ════════════════════════════════════════════════════════════════════


@main.group()
def checkpoint() -> None:
    """Local checkpoint management commands."""


@checkpoint.command("list")
@click.argument("run_id")
@click.option("--path", default=None)
def checkpoint_list(run_id: str, path: str | None) -> None:
    """List checkpoints for a run (from local state)."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    cp_dir = os.path.join(repo_root, ".forgemind", "state", "checkpoints", run_id)
    if not os.path.isdir(cp_dir):
        console.print("[dim]No checkpoints recorded locally.[/dim]")
        return

    tbl = Table(title=f"Checkpoints — Run {run_id[:8]}")
    tbl.add_column("#", justify="right")
    tbl.add_column("Type")
    tbl.add_column("Summary")
    tbl.add_column("Created")

    for f in sorted(os.listdir(cp_dir)):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(cp_dir, f), encoding="utf-8") as fh:
            cp = json.load(fh)
        tbl.add_row(
            str(cp.get("sequence_number", "?")),
            cp.get("checkpoint_type", "?"),
            (cp.get("summary") or "")[:60],
            (cp.get("created_at") or "")[:19],
        )
    console.print(tbl)


@checkpoint.command("save")
@click.argument("run_id")
@click.option(
    "--summary", default="Manual local checkpoint", help="Checkpoint summary."
)
@click.option("--path", default=None)
def checkpoint_save(run_id: str, summary: str, path: str | None) -> None:
    """Save a manual checkpoint locally with real state capture."""
    import datetime as dt

    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    cp_dir = os.path.join(repo_root, ".forgemind", "state", "checkpoints", run_id)
    os.makedirs(cp_dir, exist_ok=True)
    existing = [f for f in os.listdir(cp_dir) if f.endswith(".json")]
    seq = len(existing) + 1

    # Capture real run state from cached data
    runs_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    run_file = os.path.join(runs_dir, f"{run_id}.json")
    status_snapshot: dict = {}
    artifact_refs: dict = {}
    approval_snapshot: dict = {}
    if os.path.isfile(run_file):
        with open(run_file, encoding="utf-8") as fh:
            run_data = json.load(fh)
        status_snapshot = {
            "run_status": run_data.get("status", "unknown"),
            "task_counts": run_data.get("tasks", {}),
            "total_tasks": run_data.get("tasks", {}).get("total", 0),
        }
        artifact_refs = {
            "has_spec": run_data.get("has_spec", False),
            "has_plan": run_data.get("has_plan", False),
            "artifact_count": run_data.get("artifact_count", 0),
        }
        approval_snapshot = run_data.get("approvals", {})

    cp_data = {
        "id": str(os.urandom(16).hex()),
        "run_id": run_id,
        "sequence_number": seq,
        "checkpoint_type": "manual",
        "summary": summary,
        "status_snapshot": status_snapshot,
        "artifact_refs": artifact_refs,
        "approval_snapshot": approval_snapshot,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    out = os.path.join(cp_dir, f"{seq:04d}.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(cp_data, fh, indent=2)
    console.print(f"[green]✓[/green] Checkpoint #{seq} saved → {out}")


@main.command("confidence")
@click.argument("run_id")
@click.option("--path", default=None)
def confidence(run_id: str, path: str | None) -> None:
    """Show local confidence assessment for a run (offline heuristic)."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    # Check for locally cached run data
    runs_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    run_file = os.path.join(runs_dir, f"{run_id}.json")
    if os.path.isfile(run_file):
        with open(run_file, encoding="utf-8") as fh:
            run_data = json.load(fh)
    else:
        run_data = {}

    cp_dir = os.path.join(repo_root, ".forgemind", "state", "checkpoints", run_id)
    cp_count = 0
    if os.path.isdir(cp_dir):
        cp_count = len([f for f in os.listdir(cp_dir) if f.endswith(".json")])

    # Simple local heuristic
    score = 0
    reasons: list[str] = []

    tasks = run_data.get("tasks", {})
    total = tasks.get("total", 0)
    completed = tasks.get("completed", 0)
    if total > 0:
        rate = completed / total
        pts = int(30 * rate)
        score += pts
        reasons.append(f"Task completion: {completed}/{total} → +{pts}")
    else:
        reasons.append("No task data available locally")

    if run_data.get("has_spec"):
        score += 10
        reasons.append("SPEC present → +10")
    if run_data.get("has_plan"):
        score += 10
        reasons.append("PLAN present → +10")

    if cp_count > 0:
        score += 5
        reasons.append(f"{cp_count} checkpoint(s) → +5")

    if run_data.get("status") == "completed":
        score += 15
        reasons.append("Run completed → +15")

    # Approval-aware signals (FM-129 strengthening)
    approvals = run_data.get("approvals", {})
    resolved = approvals.get("approved", 0) + approvals.get("rejected", 0)
    pending = approvals.get("pending", 0)
    if resolved > 0 and pending == 0:
        score += 10
        reasons.append(f"All approvals resolved ({resolved}) → +10")
    elif pending > 0:
        reasons.append(f"[yellow]{pending} approval(s) still pending → +0[/yellow]")

    rejected = approvals.get("rejected", 0)
    if rejected == 0 and resolved > 0:
        score += 5
        reasons.append("No rejections → +5")
    elif rejected > 0:
        score -= 10
        reasons.append(f"[red]{rejected} rejection(s) → −10[/red]")

    # Delivery artifact signal
    if run_data.get("has_delivery_artifact"):
        score += 10
        reasons.append("Delivery artifact present → +10")

    score = max(0, min(100, score))
    band = "high" if score >= 80 else "medium" if score >= 50 else "low"

    tbl = Table(title=f"Release Confidence — Run {run_id[:8]}")
    tbl.add_column("Signal")
    tbl.add_column("Detail")
    for r in reasons:
        parts = r.split(" → ")
        tbl.add_row(parts[0], parts[1] if len(parts) > 1 else "")

    console.print(tbl)
    colour = {"high": "green", "medium": "yellow", "low": "red"}[band]
    console.print(f"\n[{colour}]Score: {score}/100  Band: {band}[/{colour}]")


@main.command("review")
@click.argument("run_id")
@click.option("--path", default=None)
def review(run_id: str, path: str | None) -> None:
    """Show local review summary for a run."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    runs_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    run_file = os.path.join(runs_dir, f"{run_id}.json")
    if not os.path.isfile(run_file):
        console.print("[dim]No local run data cached. Sync first.[/dim]")
        return

    with open(run_file, encoding="utf-8") as fh:
        run_data = json.load(fh)

    console.print(f"[bold]Review Summary — Run {run_id[:8]}[/bold]\n")
    console.print(f"  Status: {run_data.get('status', '?')}")
    tasks = run_data.get("tasks", {})
    total_tasks = tasks.get("total", 0)
    completed_tasks = tasks.get("completed", 0)
    failed_tasks = tasks.get("failed", 0)
    console.print(f"  Tasks: {completed_tasks}/{total_tasks} completed")
    if failed_tasks:
        console.print(f"  [red]Failed: {failed_tasks}[/red]")
        # Show failure details if available
        for fail_info in tasks.get("failure_details", []):
            console.print(
                f"    • {fail_info.get('title', '?')}: {fail_info.get('error', 'unknown')}"
            )

    approvals = run_data.get("approvals", {})
    if approvals:
        approved = approvals.get("approved", 0)
        pending = approvals.get("pending", 0)
        rejected = approvals.get("rejected", 0)
        console.print(
            f"  Approvals: {approved} approved, {pending} pending, {rejected} rejected"
        )

    cp_dir = os.path.join(repo_root, ".forgemind", "state", "checkpoints", run_id)
    cp_count = 0
    if os.path.isdir(cp_dir):
        cp_count = len([f for f in os.listdir(cp_dir) if f.endswith(".json")])
        console.print(f"  Checkpoints: {cp_count}")

    # ── Risk analysis ──
    console.print("\n[bold]Risk Analysis[/bold]")
    risks: list[str] = []

    if failed_tasks > 0:
        risks.append(f"[red]HIGH[/red]: {failed_tasks} task(s) failed")
    if approvals.get("pending", 0) > 0:
        risks.append(
            f"[yellow]MEDIUM[/yellow]: {approvals['pending']} approval(s) pending"
        )
    if approvals.get("rejected", 0) > 0:
        risks.append(f"[red]HIGH[/red]: {approvals['rejected']} approval(s) rejected")
    if not run_data.get("has_spec"):
        risks.append("[yellow]MEDIUM[/yellow]: No SPEC artifact")
    if not run_data.get("has_plan"):
        risks.append("[yellow]MEDIUM[/yellow]: No PLAN artifact")
    if cp_count == 0:
        risks.append("[dim]LOW[/dim]: No checkpoints saved")
    if total_tasks > 0 and completed_tasks < total_tasks and failed_tasks == 0:
        pct = int(completed_tasks / total_tasks * 100)
        risks.append(f"[yellow]MEDIUM[/yellow]: Only {pct}% of tasks complete")

    if risks:
        for r in risks:
            console.print(f"  • {r}")
    else:
        console.print("  [green]No risks identified[/green]")

    # ── Recommendation ──
    console.print("\n[bold]Recommendation[/bold]")
    high_risks = sum(1 for r in risks if "HIGH" in r)
    if high_risks:
        console.print("  [red]⊘ NOT ready for release — resolve HIGH risks first[/red]")
    elif risks:
        console.print("  [yellow]⚠ Conditionally ready — review MEDIUM risks[/yellow]")
    else:
        console.print("  [green]✓ Ready for release[/green]")


# ════════════════════════════════════════════════════════════════════
# FM-139  release — local release awareness
# ════════════════════════════════════════════════════════════════════


@main.group()
def release() -> None:
    """Local release awareness commands."""


@release.command("list")
@click.argument("project_id")
@click.option("--path", default=None)
def release_list(project_id: str, path: str | None) -> None:
    """List locally cached release packages for a project."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    rel_dir = os.path.join(repo_root, ".forgemind", "state", "releases", project_id)
    if not os.path.isdir(rel_dir):
        console.print("[dim]No release packages cached locally.[/dim]")
        return

    tbl = Table(title=f"Releases — Project {project_id[:8]}")
    tbl.add_column("Version")
    tbl.add_column("Status")
    tbl.add_column("Run")
    tbl.add_column("Created")

    for f in sorted(os.listdir(rel_dir)):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(rel_dir, f), encoding="utf-8") as fh:
            rel = json.load(fh)
        tbl.add_row(
            rel.get("version", "?"),
            rel.get("status", "?"),
            (rel.get("run_id") or "?")[:8],
            (rel.get("created_at") or "")[:19],
        )
    console.print(tbl)


@release.command("status")
@click.argument("run_id")
@click.option("--path", default=None)
def release_status(run_id: str, path: str | None) -> None:
    """Show release readiness for a run based on local state."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    runs_dir = os.path.join(repo_root, ".forgemind", "state", "runs")
    run_file = os.path.join(runs_dir, f"{run_id}.json")
    if not os.path.isfile(run_file):
        console.print("[dim]No local run data. Sync first.[/dim]")
        return

    with open(run_file, encoding="utf-8") as fh:
        run_data = json.load(fh)

    console.print(f"[bold]Release Readiness — Run {run_id[:8]}[/bold]\n")

    checks: list[tuple[str, bool, str]] = []

    # Run completed
    run_status = run_data.get("status", "unknown")
    checks.append(("Run completed", run_status == "completed", f"Status: {run_status}"))

    # Tasks terminal
    tasks = run_data.get("tasks", {})
    total = tasks.get("total", 0)
    completed = tasks.get("completed", 0)
    failed = tasks.get("failed", 0)
    checks.append(
        (
            "Tasks terminal",
            total > 0 and completed + failed >= total,
            f"{completed}/{total} completed, {failed} failed",
        )
    )

    # No failed tasks
    checks.append(("No failed tasks", failed == 0, f"{failed} failed"))

    # Approvals clear
    approvals = run_data.get("approvals", {})
    pending = approvals.get("pending", 0)
    rejected = approvals.get("rejected", 0)
    checks.append(
        (
            "Approvals clear",
            pending == 0 and rejected == 0,
            f"{pending} pending, {rejected} rejected",
        )
    )

    # Has SPEC
    checks.append(("Has SPEC", run_data.get("has_spec", False), ""))

    # Has PLAN
    checks.append(("Has PLAN", run_data.get("has_plan", False), ""))

    # Has checkpoints
    cp_dir = os.path.join(repo_root, ".forgemind", "state", "checkpoints", run_id)
    cp_count = 0
    if os.path.isdir(cp_dir):
        cp_count = len([f for f in os.listdir(cp_dir) if f.endswith(".json")])
    checks.append(("Has checkpoints", cp_count > 0, f"{cp_count} checkpoints"))

    tbl = Table(title="Readiness Checks")
    tbl.add_column("Check")
    tbl.add_column("Result")
    tbl.add_column("Detail")

    blockers = 0
    for name, passed, detail in checks:
        if passed:
            tbl.add_row(name, "[green]✓ PASS[/green]", detail)
        else:
            tbl.add_row(name, "[red]✗ FAIL[/red]", detail)
            blockers += 1

    console.print(tbl)
    passed_ct = len(checks) - blockers
    console.print(f"\n  Passed: {passed_ct}/{len(checks)}")
    if blockers:
        console.print(f"  [red]Blocked: {blockers} checks failed[/red]")
    else:
        console.print("  [green]All checks passed — ready for release[/green]")


@release.command("environments")
@click.argument("project_id")
@click.option("--path", default=None)
def release_environments(project_id: str, path: str | None) -> None:
    """List locally cached deployment environments for a project."""
    repo_root = path or detect_repo_root()
    if not repo_root:
        console.print("[red]Not inside a git repo.[/red]")
        raise SystemExit(1)

    env_dir = os.path.join(repo_root, ".forgemind", "state", "environments", project_id)
    if not os.path.isdir(env_dir):
        console.print("[dim]No environments cached locally.[/dim]")
        return

    tbl = Table(title=f"Environments — Project {project_id[:8]}")
    tbl.add_column("Name")
    tbl.add_column("Tier")
    tbl.add_column("Active")
    tbl.add_column("Gates")

    for f in sorted(os.listdir(env_dir)):
        if not f.endswith(".json"):
            continue
        with open(os.path.join(env_dir, f), encoding="utf-8") as fh:
            env = json.load(fh)
        gates = env.get("required_gates", {}).get("gates", [])
        tbl.add_row(
            env.get("name", "?"),
            env.get("tier", "?"),
            "✓" if env.get("is_active") else "✗",
            ", ".join(gates) if gates else "—",
        )
    console.print(tbl)


# ── entrypoint ─────────────────────────────────────────────────────

if __name__ == "__main__":
    main()
