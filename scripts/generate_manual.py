"""Generate ForgeMind User Manual PDF using ReportLab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    PageBreak,
    ListFlowable,
    ListItem,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "..", "ForgeMind_User_Manual.pdf")

# ── Colour palette ────────────────────────────────────────────────────────────
ACCENT     = colors.HexColor("#6366f1")   # indigo-500
ACCENT_DK  = colors.HexColor("#4f46e5")   # indigo-600
BG_CARD    = colors.HexColor("#f8f8fc")
BORDER     = colors.HexColor("#e2e2f0")
SUCCESS    = colors.HexColor("#22c55e")
WARNING    = colors.HexColor("#f59e0b")
DANGER     = colors.HexColor("#ef4444")
TEXT       = colors.HexColor("#1e1e2e")
MUTED      = colors.HexColor("#6b7280")
WHITE      = colors.white
BLACK      = colors.black

# ── Styles ────────────────────────────────────────────────────────────────────
BASE = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

STYLES = {
    "cover_title": S("cover_title",
        fontName="Helvetica-Bold", fontSize=38, leading=46,
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8),
    "cover_sub": S("cover_sub",
        fontName="Helvetica", fontSize=16, leading=22,
        textColor=colors.HexColor("#c7d2fe"), alignment=TA_CENTER, spaceAfter=6),
    "cover_meta": S("cover_meta",
        fontName="Helvetica", fontSize=11, leading=16,
        textColor=colors.HexColor("#a5b4fc"), alignment=TA_CENTER),
    "h1": S("h1",
        fontName="Helvetica-Bold", fontSize=22, leading=28,
        textColor=ACCENT_DK, spaceBefore=18, spaceAfter=8,
        borderPad=4),
    "h2": S("h2",
        fontName="Helvetica-Bold", fontSize=15, leading=20,
        textColor=TEXT, spaceBefore=14, spaceAfter=6),
    "h3": S("h3",
        fontName="Helvetica-Bold", fontSize=12, leading=16,
        textColor=ACCENT, spaceBefore=10, spaceAfter=4),
    "body": S("body",
        fontName="Helvetica", fontSize=10.5, leading=16,
        textColor=TEXT, spaceAfter=6, alignment=TA_JUSTIFY),
    "body_bold": S("body_bold",
        fontName="Helvetica-Bold", fontSize=10.5, leading=16,
        textColor=TEXT, spaceAfter=4),
    "note": S("note",
        fontName="Helvetica-Oblique", fontSize=10, leading=14,
        textColor=MUTED, spaceAfter=6, leftIndent=10),
    "code": S("code",
        fontName="Courier", fontSize=9.5, leading=14,
        textColor=colors.HexColor("#3b3b6b"),
        backColor=colors.HexColor("#f0f0fa"),
        spaceAfter=6, leftIndent=12, rightIndent=12,
        borderColor=BORDER, borderWidth=0.5, borderPad=6),
    "toc_entry": S("toc_entry",
        fontName="Helvetica", fontSize=11, leading=18,
        textColor=TEXT, leftIndent=16),
    "toc_section": S("toc_section",
        fontName="Helvetica-Bold", fontSize=12, leading=18,
        textColor=ACCENT_DK, spaceBefore=4),
    "caption": S("caption",
        fontName="Helvetica-Oblique", fontSize=9, leading=12,
        textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
    "bullet": S("bullet",
        fontName="Helvetica", fontSize=10.5, leading=15,
        textColor=TEXT, leftIndent=16, spaceAfter=3),
    "step": S("step",
        fontName="Helvetica", fontSize=10.5, leading=15,
        textColor=TEXT, leftIndent=20, spaceAfter=4),
    "tag": S("tag",
        fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, backColor=ACCENT,
        borderPad=3, spaceAfter=2),
}

def P(text, style="body"):
    return Paragraph(text, STYLES[style])

def HR(color=BORDER, thickness=0.8):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=8, spaceBefore=4)

def SP(h=0.3):
    return Spacer(1, h * cm)

# ── Cover page ────────────────────────────────────────────────────────────────
def cover_page(story):
    # Dark background via a full-width table
    cover = Table(
        [[Paragraph(
            "<br/><br/><br/><br/>",
            ParagraphStyle("x", fontSize=1)
        )]],
        colWidths=[19 * cm], rowHeights=[7 * cm]
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), ACCENT_DK),
        ("ROUNDEDCORNERS", [8]),
        ("TOPPADDING", (0,0),(-1,-1), 28),
    ]))

    # Hero block
    hero = Table([[
        Paragraph(
            "<font color='#ffffff' size='42'><b>Forge</b></font>"
            "<font color='#c7d2fe' size='42'><b>Mind</b></font>",
            ParagraphStyle("hero", fontName="Helvetica-Bold", fontSize=42,
                           leading=52, alignment=TA_CENTER, textColor=WHITE)
        )
    ]], colWidths=[19 * cm], rowHeights=[3.2 * cm])
    hero.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), ACCENT_DK),
        ("ALIGN", (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))

    sub_tbl = Table([[
        Paragraph(
            "User Manual &amp; Getting-Started Guide",
            ParagraphStyle("sub", fontName="Helvetica", fontSize=16, leading=22,
                           alignment=TA_CENTER, textColor=colors.HexColor("#c7d2fe"))
        )
    ]], colWidths=[19 * cm], rowHeights=[1.4 * cm])
    sub_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), ACCENT_DK),
        ("ALIGN", (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))

    meta_tbl = Table([[
        Paragraph(
            "Version 5.0  ·  Platform FM-001 → FM-250  ·  2026",
            ParagraphStyle("meta", fontName="Helvetica", fontSize=11,
                           alignment=TA_CENTER, textColor=colors.HexColor("#a5b4fc"))
        )
    ]], colWidths=[19 * cm], rowHeights=[1.2 * cm])
    meta_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), ACCENT_DK),
        ("ALIGN", (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))

    footer_tbl = Table([[
        Paragraph(
            "Autonomous Engineering Platform  ·  FastAPI · Next.js · PostgreSQL · LiteLLM",
            ParagraphStyle("ft", fontName="Helvetica-Oblique", fontSize=10,
                           alignment=TA_CENTER, textColor=colors.HexColor("#818cf8"))
        )
    ]], colWidths=[19 * cm], rowHeights=[1.6 * cm])
    footer_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), colors.HexColor("#3730a3")),
        ("ALIGN", (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("ROUNDEDCORNERS", [8]),
    ]))

    story += [hero, sub_tbl, meta_tbl, SP(0.6), footer_tbl, PageBreak()]


# ── Table of Contents ─────────────────────────────────────────────────────────
def toc_page(story):
    story.append(P("Table of Contents", "h1"))
    story.append(HR(ACCENT, 1.5))
    story.append(SP(0.3))

    toc = [
        ("1", "What Is ForgeMind?", "3"),
        ("2", "Quick-Start in 5 Minutes", "4"),
        ("3", "Core Concepts", "5"),
        ("4", "Dashboard Walkthrough", "7"),
        ("5", "Creating Your First Project", "9"),
        ("6", "Running Agents", "10"),
        ("7", "Approvals & Governance", "11"),
        ("8", "Security & Vault", "12"),
        ("9", "API Reference (Summary)", "13"),
        ("10", "Troubleshooting", "14"),
        ("11", "Glossary", "15"),
    ]

    tbl_data = []
    for num, title, page in toc:
        row = [
            Paragraph(f"<b>{num}</b>",
                ParagraphStyle("tn", fontName="Helvetica-Bold", fontSize=11,
                               textColor=ACCENT, alignment=TA_CENTER)),
            Paragraph(title,
                ParagraphStyle("tt", fontName="Helvetica", fontSize=11,
                               textColor=TEXT, leading=16)),
            Paragraph(page,
                ParagraphStyle("tp", fontName="Helvetica", fontSize=11,
                               textColor=MUTED, alignment=TA_CENTER)),
        ]
        tbl_data.append(row)

    tbl = Table(tbl_data, colWidths=[1.2*cm, 13.8*cm, 1.8*cm])
    tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0,0),(-1,-1), [WHITE, BG_CARD]),
        ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ("TOPPADDING", (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING", (0,0),(0,-1), 6),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [tbl, PageBreak()]


# ── Helper: info box ──────────────────────────────────────────────────────────
def info_box(story, title, body_lines, bg=BG_CARD, border=ACCENT):
    rows = [[Paragraph(f"<b>{title}</b>",
        ParagraphStyle("ib_title", fontName="Helvetica-Bold", fontSize=10.5,
                       textColor=border))]]
    for line in body_lines:
        rows.append([Paragraph(line,
            ParagraphStyle("ib_body", fontName="Helvetica", fontSize=10,
                           leading=14, textColor=TEXT))])
    tbl = Table(rows, colWidths=[16.6*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), bg),
        ("LINERIGHT", (0,0),(0,-1), 3, border),
        ("LEFTPADDING", (0,0),(-1,-1), 10),
        ("RIGHTPADDING", (0,0),(-1,-1), 10),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("BOX", (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story += [tbl, SP(0.35)]


# ── Section 1 — What is ForgeMind ─────────────────────────────────────────────
def section_what(story):
    story.append(P("1. What Is ForgeMind?", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "ForgeMind is an <b>autonomous engineering platform</b>. "
        "You describe what software you want to build in plain language, "
        "and ForgeMind assembles a team of AI agents that plan, write, review, "
        "test, and govern every step — all under your control.",
        "body"))
    story.append(SP(0.3))

    info_box(story, "🎯  The Big Idea",
        ["Think of ForgeMind as a senior engineering team you can talk to.",
         "You say: <i>\"Build me a REST API for a todo app with auth.\"</i>",
         "ForgeMind breaks it into tasks, assigns agents, writes code,",
         "creates a PR, and asks for your approval before merging."],
        bg=colors.HexColor("#eef2ff"), border=ACCENT)

    story.append(P("Key things ForgeMind does for you:", "h2"))

    features = [
        ("Goal → System",
         "Describe an idea in English. ForgeMind generates an architecture, "
         "picks the right agents, and produces working code."),
        ("Multi-Agent Orchestration",
         "Different AI agents specialise in planning, coding, reviewing, "
         "security scanning, and documentation. They work together automatically."),
        ("Human-in-the-Loop Approvals",
         "Every risky action (merge, deploy, delete) requires your approval. "
         "Nothing destructive happens without a human sign-off."),
        ("Full Audit Trail",
         "Every agent action, token spend, and decision is logged. You can "
         "replay any run step-by-step."),
        ("Security First",
         "Credentials are encrypted in a vault. All endpoints require auth. "
         "PII scanning runs on every artifact."),
    ]

    for title, desc in features:
        row = Table([[
            Paragraph(f"<b>{title}</b>",
                ParagraphStyle("ft", fontName="Helvetica-Bold", fontSize=10.5,
                               textColor=ACCENT_DK, leading=14)),
            Paragraph(desc,
                ParagraphStyle("fd", fontName="Helvetica", fontSize=10,
                               leading=14, textColor=TEXT)),
        ]], colWidths=[4.5*cm, 12.1*cm])
        row.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("TOPPADDING", (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ]))
        story.append(row)

    story.append(SP(0.5))
    story.append(P("Who is this manual for?", "h2"))
    story.append(P(
        "This manual is written for <b>developers, tech leads, and product owners</b> "
        "who want to use ForgeMind to build software faster. No deep knowledge of "
        "AI or machine learning is required — just the ability to describe what you "
        "want to build.",
        "body"))
    story.append(PageBreak())


# ── Section 2 — Quick Start ───────────────────────────────────────────────────
def section_quickstart(story):
    story.append(P("2. Quick-Start in 5 Minutes", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "Follow these steps to get ForgeMind running on your machine. "
        "You only need <b>Docker Desktop</b> installed.",
        "body"))
    story.append(SP(0.2))

    steps = [
        ("Step 1 — Clone the repo",
         "git clone https://github.com/your-org/forgemind.git\ncd forgemind",
         "Download the project to your local machine."),
        ("Step 2 — Copy environment file",
         "cp .env.example .env",
         "The defaults work for local development. You do not need to change anything yet."),
        ("Step 3 — Start infrastructure",
         "docker compose up -d postgres redis minio",
         "Starts PostgreSQL (database), Redis (cache/queue), and MinIO (file storage)."),
        ("Step 4 — Apply database schema",
         "cd apps/api\nalembic upgrade head",
         "Creates all tables in the database. Run this once after a fresh install."),
        ("Step 5 — Start the backend",
         "uvicorn app.main:app --reload --port 8000",
         "The API server starts at http://localhost:8000"),
        ("Step 6 — Start the frontend",
         "cd apps/web\nnpm install\nnpm run dev",
         "The dashboard opens at http://localhost:3000"),
    ]

    for i, (title, cmd, note) in enumerate(steps, 1):
        num_cell = Table([[Paragraph(str(i),
            ParagraphStyle("sn", fontName="Helvetica-Bold", fontSize=14,
                           textColor=WHITE, alignment=TA_CENTER))]],
            colWidths=[0.8*cm], rowHeights=[0.8*cm])
        num_cell.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), ACCENT),
            ("ROUNDEDCORNERS", [4]),
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ]))

        content = [
            Paragraph(f"<b>{title}</b>",
                ParagraphStyle("st", fontName="Helvetica-Bold", fontSize=11,
                               textColor=TEXT, leading=16)),
            Paragraph(cmd.replace("\n", "<br/>"),
                ParagraphStyle("sc", fontName="Courier", fontSize=9.5,
                               leading=14, textColor=colors.HexColor("#3b3b6b"),
                               backColor=colors.HexColor("#f0f0fa"),
                               borderPad=5)),
            Paragraph(f"<i>{note}</i>",
                ParagraphStyle("sn2", fontName="Helvetica-Oblique", fontSize=10,
                               textColor=MUTED, leading=13)),
        ]

        step_tbl = Table([[num_cell, content]],
                         colWidths=[1.2*cm, 15.4*cm])
        step_tbl.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("TOPPADDING", (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ]))
        story.append(step_tbl)
        story.append(SP(0.1))

    story.append(SP(0.4))
    info_box(story, "✅  You're ready!",
        ["Open http://localhost:3000 in your browser.",
         "You will see the ForgeMind landing page.",
         "Click <b>Open Dashboard</b> to start working."],
        bg=colors.HexColor("#f0fdf4"), border=SUCCESS)
    story.append(PageBreak())


# ── Section 3 — Core Concepts ─────────────────────────────────────────────────
def section_concepts(story):
    story.append(P("3. Core Concepts", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "Before diving into the dashboard, these are the key building blocks "
        "you will see throughout ForgeMind.",
        "body"))
    story.append(SP(0.3))

    concepts = [
        ("Workspace", "#6366f1",
         "The top-level container. Like a company or team account. "
         "You can have multiple projects inside one workspace. "
         "Workspace members share access to all projects in it."),
        ("Project", "#8b5cf6",
         "A single software initiative — for example 'Payment Service' or "
         "'Mobile App Redesign'. Each project has its own runs, tasks, agents, "
         "and settings."),
        ("Run", "#ec4899",
         "One execution of an agent workflow. When you give ForgeMind a goal, "
         "it creates a Run. A run contains multiple Tasks, and each Task is "
         "handled by a specialised agent."),
        ("Task", "#f59e0b",
         "The smallest unit of work. Examples: 'Write the User model', "
         "'Write unit tests', 'Run security scan'. Each task is picked up "
         "by the most suitable agent."),
        ("Agent", "#22c55e",
         "An AI worker with a specific role: Planner, Coder, Reviewer, "
         "Security Scanner, Doc Writer. Agents are assembled per project "
         "based on what the run needs."),
        ("Approval", "#ef4444",
         "A checkpoint where a human must approve before work continues. "
         "Risky actions (like deploying code or merging a PR) always "
         "require approval. You see all pending approvals in the dashboard."),
        ("Artifact", "#0ea5e9",
         "Any output produced by an agent: source files, documentation, "
         "test results, PDFs, images. Artifacts are stored and linked to "
         "their run so you can always find what was produced."),
        ("Trust Score", "#64748b",
         "A confidence score (0–100) that shows how reliable an agent's "
         "output is, based on test results, security findings, and review "
         "comments. Higher is better."),
    ]

    for name, color, desc in concepts:
        c = colors.HexColor(color)
        badge = Table([[Paragraph(name,
            ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=10,
                           textColor=WHITE, alignment=TA_CENTER))]],
            colWidths=[3.2*cm], rowHeights=[0.65*cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), c),
            ("ROUNDEDCORNERS", [4]),
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ]))

        desc_cell = Paragraph(desc,
            ParagraphStyle("cdesc", fontName="Helvetica", fontSize=10.5,
                           leading=15, textColor=TEXT))

        row = Table([[badge, desc_cell]], colWidths=[3.6*cm, 13.0*cm])
        row.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("TOPPADDING", (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING", (1,0),(1,-1), 10),
            ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ]))
        story.append(row)

    story.append(SP(0.6))
    story.append(P("How they fit together", "h2"))
    story.append(P(
        "A <b>Workspace</b> contains <b>Projects</b>. "
        "Each project can have many <b>Runs</b>. "
        "Each run is broken into <b>Tasks</b>, each handled by an <b>Agent</b>. "
        "Agents produce <b>Artifacts</b>. "
        "High-risk actions generate <b>Approvals</b> for you to review. "
        "The whole history is recorded in the audit log.",
        "body"))

    # Diagram (simple table)
    flow = Table([[
        Paragraph("Workspace", ParagraphStyle("fw", fontName="Helvetica-Bold",
            fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("→", ParagraphStyle("arr", fontName="Helvetica", fontSize=14,
            textColor=MUTED, alignment=TA_CENTER)),
        Paragraph("Project", ParagraphStyle("fw", fontName="Helvetica-Bold",
            fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("→", ParagraphStyle("arr", fontName="Helvetica", fontSize=14,
            textColor=MUTED, alignment=TA_CENTER)),
        Paragraph("Run", ParagraphStyle("fw", fontName="Helvetica-Bold",
            fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("→", ParagraphStyle("arr", fontName="Helvetica", fontSize=14,
            textColor=MUTED, alignment=TA_CENTER)),
        Paragraph("Tasks & Agents", ParagraphStyle("fw", fontName="Helvetica-Bold",
            fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
        Paragraph("→", ParagraphStyle("arr", fontName="Helvetica", fontSize=14,
            textColor=MUTED, alignment=TA_CENTER)),
        Paragraph("Artifacts", ParagraphStyle("fw", fontName="Helvetica-Bold",
            fontSize=10, textColor=WHITE, alignment=TA_CENTER)),
    ]], colWidths=[2.4*cm,0.8*cm,2.4*cm,0.8*cm,2.0*cm,0.8*cm,3.4*cm,0.8*cm,2.4*cm])
    flow.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(0,0), colors.HexColor("#6366f1")),
        ("BACKGROUND", (2,0),(2,0), colors.HexColor("#8b5cf6")),
        ("BACKGROUND", (4,0),(4,0), colors.HexColor("#ec4899")),
        ("BACKGROUND", (6,0),(6,0), colors.HexColor("#f59e0b")),
        ("BACKGROUND", (8,0),(8,0), colors.HexColor("#0ea5e9")),
        ("ROUNDEDCORNERS", [4]),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))
    story += [SP(0.3), flow, PageBreak()]


# ── Section 4 — Dashboard ─────────────────────────────────────────────────────
def section_dashboard(story):
    story.append(P("4. Dashboard Walkthrough", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "The dashboard at <b>http://localhost:3000/dashboard</b> is your "
        "command centre. Here is what each part does.",
        "body"))
    story.append(SP(0.3))

    sections = [
        ("Top Stats Bar", [
            "Projects — total number of projects in your workspace.",
            "Running Agents — how many agents are currently active.",
            "Pending Approvals — tasks waiting for your decision (click to review).",
            "Health — overall system status.",
        ]),
        ("Projects Panel", [
            "Shows all your projects as cards.",
            "Each card shows the project name, status (draft / active / archived), "
            "and a link to its detail page.",
            "Click New Project to create one (see Section 5).",
        ]),
        ("Sidebar Navigation", [
            "Dashboard — home overview.",
            "Projects — full project list.",
            "Runs — all agent runs across projects.",
            "Approvals — pending decisions.",
            "Agents — agent registry and performance.",
            "Audit — full activity log.",
            "Costs — LLM token spend breakdown.",
            "Vault — encrypted credentials.",
            "Governance — policies and compliance.",
            "Architecture — live system diagrams.",
            "SLOs — service level objectives.",
            "Schedules — cron and event triggers.",
        ]),
        ("Quick Actions", [
            "New Project — jump straight to the project creation form.",
            "Plan from Prompt — describe what you want to build in plain English.",
            "Review Approvals — shortcut to the approvals queue.",
        ]),
    ]

    for section_title, bullets in sections:
        story.append(P(section_title, "h2"))
        for b in bullets:
            story.append(P(f"  • {b}", "bullet"))
        story.append(SP(0.2))

    story.append(SP(0.3))
    info_box(story, "💡  Tip — Keyboard shortcuts",
        ["Press <b>N</b> to open the New Project form from anywhere in the dashboard.",
         "Press <b>?</b> to see all available keyboard shortcuts.",
         "The sidebar can be collapsed with the <b>←</b> arrow icon at the bottom."],
        bg=colors.HexColor("#fefce8"), border=WARNING)

    story.append(P("Dashboard pages at a glance", "h2"))
    pages_data = [
        ["Page", "What you can do there"],
        ["/dashboard", "Overview — stats, recent projects, quick actions"],
        ["/dashboard/projects", "Browse and manage all projects"],
        ["/dashboard/runs", "See all agent runs (status, duration, cost)"],
        ["/dashboard/approvals", "Approve or reject pending agent actions"],
        ["/dashboard/agents", "View agent profiles and performance metrics"],
        ["/dashboard/costs", "Track LLM token spend per project/agent"],
        ["/dashboard/audit", "Full tamper-evident audit log (export CSV/JSONL)"],
        ["/dashboard/vault", "Store and retrieve encrypted API keys & secrets"],
        ["/dashboard/governance", "Define policies that agents must follow"],
        ["/dashboard/architecture", "Auto-generated system architecture diagrams"],
        ["/dashboard/slos", "Set and monitor Service Level Objectives"],
        ["/dashboard/schedules", "Create cron jobs and event-based triggers"],
        ["/dashboard/activity", "Real-time activity feed across the platform"],
    ]
    tbl = Table(pages_data, colWidths=[5.5*cm, 11.1*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), ACCENT_DK),
        ("TEXTCOLOR", (0,0),(-1,0), WHITE),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0),(-1,0), 10),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, BG_CARD]),
        ("FONTSIZE", (0,1),(-1,-1), 9.5),
        ("FONTNAME", (0,1),(0,-1), "Courier"),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("GRID", (0,0),(-1,-1), 0.4, BORDER),
    ]))
    story += [tbl, PageBreak()]


# ── Section 5 — Creating a Project ────────────────────────────────────────────
def section_project(story):
    story.append(P("5. Creating Your First Project", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "A project is the main unit of work in ForgeMind. "
        "Everything — agents, runs, artifacts — lives inside a project.",
        "body"))
    story.append(SP(0.3))

    story.append(P("Method A — Create manually", "h2"))
    manual_steps = [
        "Click <b>New Project</b> in the top-right of the dashboard.",
        "Fill in a <b>Project Name</b> (required) and an optional description.",
        "Choose a <b>workspace</b> to place it in.",
        "Click <b>Create Project</b>. You are taken to the project detail page.",
    ]
    for i, s in enumerate(manual_steps, 1):
        story.append(P(f"  {i}. {s}", "step"))

    story.append(SP(0.4))
    story.append(P("Method B — Plan from Prompt (Recommended)", "h2"))
    story.append(P(
        "This is the most powerful way. Describe what you want in plain English "
        "and ForgeMind creates the project, plans the work, and kicks off agents.",
        "body"))
    prompt_steps = [
        "Click <b>Plan from Prompt</b> on the dashboard.",
        "Type a description. Example: "
        "<i>\"Build a Python FastAPI service for managing customer orders "
        "with JWT auth and a PostgreSQL database.\"</i>",
        "Click <b>Generate Plan</b>.",
        "ForgeMind shows you a structured plan with tasks and agent assignments.",
        "Review the plan. If it looks right, click <b>Start Run</b>.",
        "Agents begin working. You can watch progress in real-time on the Runs page.",
    ]
    for i, s in enumerate(prompt_steps, 1):
        story.append(P(f"  {i}. {s}", "step"))

    story.append(SP(0.4))
    story.append(P("Project statuses", "h2"))
    status_data = [
        ["Status", "Meaning"],
        ["draft", "Just created. No runs yet."],
        ["active", "At least one run has been started."],
        ["archived", "Closed. Read-only. No new runs."],
    ]
    tbl = Table(status_data, colWidths=[3.0*cm, 13.6*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), ACCENT_DK),
        ("TEXTCOLOR", (0,0),(-1,0), WHITE),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, BG_CARD]),
        ("FONTNAME", (0,1),(0,-1), "Courier"),
        ("FONTSIZE", (0,0),(-1,-1), 10),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("GRID", (0,0),(-1,-1), 0.4, BORDER),
    ]))
    story.append(tbl)
    story.append(PageBreak())


# ── Section 6 — Running Agents ────────────────────────────────────────────────
def section_runs(story):
    story.append(P("6. Running Agents", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "A <b>Run</b> is when agents actually do work. "
        "Runs are triggered when you submit a prompt or start a project plan.",
        "body"))
    story.append(SP(0.3))

    story.append(P("Run lifecycle", "h2"))
    lifecycle = [
        ("PENDING",  "#94a3b8", "Waiting to start. The run has been created but agents haven't begun."),
        ("PLANNING",  "#8b5cf6", "The Planner agent is breaking the goal into tasks."),
        ("RUNNING",   "#f59e0b", "Agents are actively working on tasks."),
        ("AWAITING APPROVAL", "#ef4444", "A task needs human approval before continuing."),
        ("COMPLETED", "#22c55e", "All tasks finished successfully."),
        ("FAILED",    "#dc2626", "One or more tasks failed. Check the task log for details."),
    ]
    for status, color, desc in lifecycle:
        c = colors.HexColor(color)
        badge = Table([[Paragraph(status,
            ParagraphStyle("ls", fontName="Helvetica-Bold", fontSize=9,
                           textColor=WHITE, alignment=TA_CENTER))]],
            colWidths=[3.8*cm], rowHeights=[0.55*cm])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,-1), c),
            ("ROUNDEDCORNERS", [3]),
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ]))
        row = Table([[badge,
            Paragraph(desc, ParagraphStyle("ld", fontName="Helvetica",
                fontSize=10.5, leading=15, textColor=TEXT))]],
            colWidths=[4.2*cm, 12.4*cm])
        row.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
            ("LEFTPADDING", (1,0),(1,-1), 10),
            ("TOPPADDING", (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ]))
        story.append(row)

    story.append(SP(0.5))
    story.append(P("How to monitor a run", "h2"))
    monitor_steps = [
        "Go to <b>/dashboard/runs</b> or click the run ID from the project page.",
        "The Run Detail page shows all tasks, their agent, duration, and status.",
        "Click any task to see its full output, code written, and agent reasoning.",
        "The live stream view (click <b>Watch Live</b>) shows output as it is generated.",
        "If a task fails, the error reason is shown inline — you can retry failed tasks.",
    ]
    for i, s in enumerate(monitor_steps, 1):
        story.append(P(f"  {i}. {s}", "step"))

    story.append(SP(0.4))
    info_box(story, "💰  Cost tracking",
        ["Every run shows total LLM token cost in real-time.",
         "You can set a per-project budget limit in Governance settings.",
         "If a run is about to exceed the budget, it pauses and asks for approval."],
        bg=colors.HexColor("#fff7ed"), border=WARNING)
    story.append(PageBreak())


# ── Section 7 — Approvals ─────────────────────────────────────────────────────
def section_approvals(story):
    story.append(P("7. Approvals & Governance", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "ForgeMind never takes irreversible actions without asking you first. "
        "Approvals are the safety gate between AI work and the real world.",
        "body"))
    story.append(SP(0.3))

    story.append(P("What requires an approval?", "h2"))
    approval_items = [
        "Merging a pull request to main/master",
        "Deploying to a staging or production environment",
        "Deleting files or database records",
        "Spending above a configured budget threshold",
        "Running code in a production sandbox",
        "Publishing or sending any external communication",
    ]
    for item in approval_items:
        story.append(P(f"  • {item}", "bullet"))

    story.append(SP(0.4))
    story.append(P("How to handle an approval", "h2"))
    appr_steps = [
        "You receive a notification (badge on the Approvals menu item).",
        "Go to <b>/dashboard/approvals</b>.",
        "Read the <b>action description</b>, <b>risk level</b>, and <b>evidence</b> "
        "provided by the agent.",
        "Optionally click <b>View Diff</b> or <b>View Code</b> to inspect the changes.",
        "Click <b>Approve</b> to proceed or <b>Reject</b> with a comment explaining why.",
        "The agent receives your decision and continues (or revises its plan).",
    ]
    for i, s in enumerate(appr_steps, 1):
        story.append(P(f"  {i}. {s}", "step"))

    story.append(SP(0.4))
    story.append(P("Governance policies", "h2"))
    story.append(P(
        "In <b>/dashboard/governance</b> you can define rules that every agent must "
        "follow. Examples:",
        "body"))
    policy_examples = [
        "\"Never commit code with TODO comments.\"",
        "\"All database queries must use parameterised statements.\"",
        "\"Every new endpoint must have a corresponding test.\"",
        "\"Do not use deprecated libraries.\"",
    ]
    for ex in policy_examples:
        story.append(P(f"  • {ex}", "bullet"))
    story.append(P(
        "Policies are evaluated automatically at the end of every task. "
        "Violations are shown in the task output and can block completion.",
        "body"))
    story.append(PageBreak())


# ── Section 8 — Security & Vault ──────────────────────────────────────────────
def section_security(story):
    story.append(P("8. Security & Vault", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "ForgeMind is built with security as a first principle. "
        "Here is how it keeps your secrets and data safe.",
        "body"))
    story.append(SP(0.3))

    story.append(P("Credential Vault", "h2"))
    story.append(P(
        "All API keys, tokens, and passwords are stored <b>encrypted at rest</b> "
        "using Fernet symmetric encryption. You never see them in plain text after "
        "saving.",
        "body"))
    vault_steps = [
        "Go to <b>/dashboard/vault</b>.",
        "Click <b>Add Credential</b>.",
        "Enter a name (e.g. 'OpenAI Key') and paste your secret value.",
        "Click <b>Save</b>. The value is encrypted before storage.",
        "In your project, reference it by name: <code>vault://OpenAI Key</code>.",
        "Agents can use vault references — they never see the raw secret.",
    ]
    for i, s in enumerate(vault_steps, 1):
        story.append(P(f"  {i}. {s}", "step"))

    story.append(SP(0.4))
    story.append(P("PII Scanning", "h2"))
    story.append(P(
        "Every artifact produced by agents is automatically scanned for "
        "Personally Identifiable Information (PII) — emails, phone numbers, "
        "credit card numbers, SSNs, and more. "
        "Findings are shown in the artifact detail view.",
        "body"))

    story.append(SP(0.4))
    story.append(P("Security findings", "h2"))
    story.append(P(
        "The Security Scan agent runs <b>static analysis</b> on every code artifact "
        "and reports findings by severity:",
        "body"))
    findings_data = [
        ["Severity", "Colour", "Meaning"],
        ["CRITICAL", "🔴 Red", "Immediate security vulnerability. Fix before proceeding."],
        ["HIGH",     "🟠 Orange", "Serious issue. Should be fixed before any deploy."],
        ["MEDIUM",   "🟡 Yellow", "Worth addressing but not blocking."],
        ["LOW",      "🔵 Blue", "Informational. Fix when convenient."],
    ]
    tbl = Table(findings_data, colWidths=[2.8*cm, 2.8*cm, 11.0*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), ACCENT_DK),
        ("TEXTCOLOR", (0,0),(-1,0), WHITE),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, BG_CARD]),
        ("FONTSIZE", (0,0),(-1,-1), 10),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("GRID", (0,0),(-1,-1), 0.4, BORDER),
    ]))
    story.append(tbl)
    story.append(SP(0.4))

    info_box(story, "🔒  Auth in development mode",
        ["When running locally with the default SECRET_KEY and APP_ENV=development,",
         "ForgeMind uses a dev stub user automatically — no login required.",
         "In production, set a strong SECRET_KEY and APP_ENV=production.",
         "All endpoints then require a valid JWT Bearer token."],
        bg=colors.HexColor("#fef2f2"), border=DANGER)
    story.append(PageBreak())


# ── Section 9 — API Reference ─────────────────────────────────────────────────
def section_api(story):
    story.append(P("9. API Reference (Summary)", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(P(
        "ForgeMind exposes a full REST API. The interactive docs are always "
        "available at <b>http://localhost:8000/docs</b> (Swagger UI).",
        "body"))
    story.append(SP(0.3))

    story.append(P("Authentication", "h2"))
    story.append(P(
        "All API endpoints (except <code>/health</code> and <code>/auth/login</code>) "
        "require a JWT Bearer token in the Authorization header:",
        "body"))
    story.append(Paragraph(
        "Authorization: Bearer &lt;your-token&gt;",
        STYLES["code"]))

    story.append(P(
        "To get a token: POST <code>/auth/register</code> (first time) "
        "or <code>/auth/login</code> (subsequent times).",
        "body"))

    story.append(SP(0.3))
    story.append(P("Key endpoint groups", "h2"))

    endpoints = [
        ("/auth/*",         "Register, login, get current user"),
        ("/projects",       "CRUD for projects"),
        ("/projects/{id}/runs",   "Start, list, get runs for a project"),
        ("/runs/{id}/tasks",      "List tasks for a run"),
        ("/approvals",      "List and decide on approval requests"),
        ("/agents",         "Agent registry and performance stats"),
        ("/artifacts",      "Download and manage artifacts"),
        ("/vault",          "Encrypted credential storage"),
        ("/governance",     "Policy definitions and evaluations"),
        ("/audit",          "Audit log export (JSONL / CSV)"),
        ("/costs",          "LLM cost summaries"),
        ("/workspaces",     "Workspace and membership management"),
        ("/admin/*",        "Platform ops, query stats, job queue"),
        ("/schedules",      "Cron and event-driven triggers"),
        ("/slos",           "Service level objectives"),
        ("/health",         "Health check (no auth required)"),
    ]

    ep_data = [["Endpoint", "Description"]] + endpoints
    tbl = Table(ep_data, colWidths=[5.8*cm, 10.8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), ACCENT_DK),
        ("TEXTCOLOR", (0,0),(-1,0), WHITE),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTNAME", (0,1),(0,-1), "Courier"),
        ("FONTSIZE", (0,0),(-1,-1), 9.5),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, BG_CARD]),
        ("TOPPADDING", (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("GRID", (0,0),(-1,-1), 0.4, BORDER),
    ]))
    story.append(tbl)
    story.append(SP(0.4))

    info_box(story, "📖  Full interactive docs",
        ["Open http://localhost:8000/docs in your browser.",
         "Every endpoint is documented with request/response schemas.",
         "You can try any endpoint directly from the browser — no extra tools needed."],
        bg=colors.HexColor("#eef2ff"), border=ACCENT)
    story.append(PageBreak())


# ── Section 10 — Troubleshooting ──────────────────────────────────────────────
def section_troubleshooting(story):
    story.append(P("10. Troubleshooting", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(SP(0.2))

    issues = [
        ("Dashboard shows 'Failed to load projects'",
         [
             "Make sure the backend API is running: curl http://localhost:8000/health",
             "Check the browser console (F12 → Console) for the exact error.",
             "Ensure NEXT_PUBLIC_API_URL=http://localhost:8000 in apps/web/.env.local",
         ]),
        ("Cannot log in / redirected to login page",
         [
             "In dev mode (default), login is automatic — no username/password needed.",
             "If you see a login form, check that APP_ENV=development in your .env file.",
             "Clear your browser localStorage: DevTools → Application → Storage → Clear.",
         ]),
        ("alembic upgrade head fails",
         [
             "Make sure PostgreSQL is running: docker ps | grep postgres",
             "Check DATABASE_URL in your .env matches the running Postgres container.",
             "If you see 'table already exists', run: alembic stamp head",
         ]),
        ("API returns 401 Unauthorized",
         [
             "In production, all endpoints require a JWT token.",
             "In dev mode, ensure APP_ENV=development and SECRET_KEY is the default value.",
             "Use /auth/register to create an account, then /auth/login to get a token.",
         ]),
        ("Agents never start / run stays PENDING",
         [
             "Check the backend logs for worker errors (look for 'job_dispatcher').",
             "Make sure Redis is running: docker ps | grep redis",
             "Check that an LLM API key is set (OPENAI_API_KEY or ANTHROPIC_API_KEY).",
         ]),
        ("TypeScript / build errors in apps/web",
         [
             "Run: cd apps/web && npm install",
             "Then: npx tsc --noEmit to see type errors.",
             "If types are from @forgemind/types, check packages/schemas is up to date.",
         ]),
        ("Ruff lint errors in CI",
         [
             "Run locally: cd apps/api && ruff check . && ruff format .",
             "Both check AND format must pass — CI runs both steps.",
             "Use # noqa: F401 only as a last resort for legitimate unused imports.",
         ]),
    ]

    for title, bullets in issues:
        story.append(P(title, "h2"))
        for b in bullets:
            story.append(P(f"  • {b}", "bullet"))
        story.append(SP(0.1))

    story.append(SP(0.3))
    info_box(story, "🆘  Still stuck?",
        ["Check the docs folder: docs/DEVELOPMENT_WORKFLOW.md",
         "Open an issue at: https://github.com/your-org/forgemind/issues",
         "Include: error message, OS, Python version, Node version, Docker version."],
        bg=colors.HexColor("#fef2f2"), border=DANGER)
    story.append(PageBreak())


# ── Section 11 — Glossary ─────────────────────────────────────────────────────
def section_glossary(story):
    story.append(P("11. Glossary", "h1"))
    story.append(HR(ACCENT, 1.2))
    story.append(SP(0.2))

    terms = [
        ("Agent",           "An AI worker with a specific role (Planner, Coder, Reviewer, etc.)."),
        ("Alembic",         "Database migration tool for Python/SQLAlchemy. Manages schema changes."),
        ("Approval",        "A human decision gate. Agents pause and wait for your Yes/No."),
        ("Artifact",        "Any file or document produced by an agent during a run."),
        ("Audit Log",       "Tamper-evident record of every action taken in the platform."),
        ("bcrypt",          "Password hashing algorithm. ForgeMind stores passwords as bcrypt hashes."),
        ("Budget Forecast", "AI-predicted LLM spend for a project over the next billing period."),
        ("Cron Trigger",    "A scheduled event (e.g. 'every Monday at 9am') that starts a run."),
        ("FastAPI",         "Python web framework used for the ForgeMind backend API."),
        ("Fernet",          "Symmetric encryption used by the Credential Vault."),
        ("JWT",             "JSON Web Token — a secure way to carry authentication information."),
        ("LiteLLM",         "Library that routes AI calls to OpenAI, Anthropic, Google, etc."),
        ("MinIO",           "S3-compatible object storage. ForgeMind stores artifacts here."),
        ("Next.js",         "React framework used for the ForgeMind frontend dashboard."),
        ("PII",             "Personally Identifiable Information — data that can identify a person."),
        ("PostgreSQL",      "Relational database. Stores all ForgeMind data."),
        ("Project",         "A single software initiative managed inside ForgeMind."),
        ("RBAC",            "Role-Based Access Control — controls who can do what in the platform."),
        ("Redis",           "In-memory data store. Used for caching and background job queues."),
        ("Run",             "One execution of an agent workflow for a given goal."),
        ("SLO",             "Service Level Objective — a target metric like '99% run success rate'."),
        ("SQLAlchemy",      "Python ORM (Object-Relational Mapper) used to interact with PostgreSQL."),
        ("Task",            "The smallest unit of work inside a run. Handled by one agent."),
        ("Trust Score",     "A 0–100 confidence rating for an agent output based on quality signals."),
        ("Vault",           "Encrypted credential storage within ForgeMind."),
        ("Workspace",       "Top-level container. Like a team or organisation account."),
    ]

    term_data = [["Term", "Definition"]]
    for term, defn in terms:
        term_data.append([
            Paragraph(term, ParagraphStyle("gt", fontName="Helvetica-Bold",
                                           fontSize=10, textColor=ACCENT_DK)),
            Paragraph(defn, ParagraphStyle("gd", fontName="Helvetica",
                                           fontSize=10, leading=14, textColor=TEXT)),
        ])

    tbl = Table(term_data, colWidths=[3.8*cm, 12.8*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,0), ACCENT_DK),
        ("TEXTCOLOR", (0,0),(-1,0), WHITE),
        ("FONTNAME", (0,0),(-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [WHITE, BG_CARD]),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LINEBELOW", (0,0),(-1,-1), 0.4, BORDER),
        ("LEFTPADDING", (0,0),(-1,-1), 8),
        ("VALIGN", (0,0),(-1,-1), "TOP"),
    ]))
    story.append(tbl)


# ── Page header/footer ────────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header bar
    canvas.setFillColor(ACCENT_DK)
    canvas.rect(0, h - 1.0*cm, w, 1.0*cm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(1.8*cm, h - 0.65*cm, "ForgeMind")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(w - 1.8*cm, h - 0.65*cm, "User Manual · v5.0")

    # Footer bar
    canvas.setFillColor(BG_CARD)
    canvas.rect(0, 0, w, 0.9*cm, fill=1, stroke=0)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 0.9*cm, w, 0.9*cm)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8.5)
    canvas.drawCentredString(w / 2, 0.32*cm, f"Page {doc.page}")
    canvas.drawString(1.8*cm, 0.32*cm, "© 2026 ForgeMind")
    canvas.drawRightString(w - 1.8*cm, 0.32*cm, "Confidential")

    canvas.restoreState()


def on_first_page(canvas, doc):
    # No header/footer on cover page
    pass


# ── Build PDF ─────────────────────────────────────────────────────────────────
def build():
    doc = SimpleDocTemplate(
        OUTPUT,
        pagesize=A4,
        leftMargin=1.8*cm,
        rightMargin=1.8*cm,
        topMargin=1.6*cm,
        bottomMargin=1.6*cm,
        title="ForgeMind User Manual",
        author="ForgeMind",
        subject="User Manual and Getting-Started Guide",
    )

    story = []
    cover_page(story)
    toc_page(story)
    section_what(story)
    section_quickstart(story)
    section_concepts(story)
    section_dashboard(story)
    section_project(story)
    section_runs(story)
    section_approvals(story)
    section_security(story)
    section_api(story)
    section_troubleshooting(story)
    section_glossary(story)

    doc.build(
        story,
        onFirstPage=on_first_page,
        onLaterPages=on_page,
    )
    print(f"PDF written → {os.path.abspath(OUTPUT)}")


if __name__ == "__main__":
    build()
