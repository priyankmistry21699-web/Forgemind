# ForgeMind V5 — Product Roadmap (FM-211 → FM-250)

> **Version:** V5 Architecture Draft
> **Date:** 2026-04-13
> **Status:** FUTURE — Not yet implemented. Planning begins after FM-210 is complete.
> **Scope:** FM-211 through FM-250 (40 milestones across 4 strategic blocks)
> **Builds on:** ForgeMind V1–V4 (FM-001 through FM-210)

---

## 1. V5 Executive Summary

### What V5 Is

ForgeMind V5 transforms the platform from a **collaborative enterprise engineering platform** into a **dynamic multi-agent orchestration platform** with persistent reasoning, structured memory, and explainable decision-making.

V4 built the ecosystem: team collaboration, GitHub integration, enterprise governance, code intelligence, analytics, and API-first extensibility. V5 fundamentally reimagines how agents are created, deployed, communicate, and reason — making ForgeMind a self-organizing intelligence system rather than a static pipeline of fixed agents.

V5 adds 40 milestones (FM-211 → FM-250) across 4 strategic blocks:

| Block   | Range           | Theme                                       |
| ------- | --------------- | ------------------------------------------- |
| Wave 17 | FM-211 → FM-220 | Dynamic Multi-Agent Runtime Foundations     |
| Wave 18 | FM-221 → FM-230 | Council Collaboration & Deliberation Engine |
| Wave 19 | FM-231 → FM-240 | Graph Memory & Persistent Reasoning         |
| Wave 20 | FM-241 → FM-250 | Adaptive Workflow Selection & FAIR Engine   |

### Why V5 Matters

Through V4, ForgeMind agents are statically defined — the system picks from a fixed roster (planner, architect, coder, reviewer, tester) using capability scoring. This works well for structured engineering workflows but breaks down when:

- Tasks require **novel combinations of expertise** not covered by the fixed roster
- Complex decisions need **multi-perspective deliberation** rather than single-agent execution
- Long-running projects accumulate context that **exceeds prompt window limits** and needs structured storage
- Workflow selection is **opaque** — operators can't see why one execution path was chosen over another

V5 solves each of these by introducing:

1. **Dynamic agent spawning** — Sub-agents are created on-demand as microservice workers, specialized for the task at hand
2. **Council deliberation** — Multiple agents collaborate on complex decisions through structured debate, not just voting
3. **Graph-based memory** — Relationships, reasoning chains, and context are persisted in a graph structure that survives across runs
4. **Explainable workflow selection** — FAIR-style scoring with confidence and policy signals makes every routing decision transparent

### How V5 Differs from Earlier Versions

| Version             | Focus            | Result                                                         |
| ------------------- | ---------------- | -------------------------------------------------------------- |
| V1 (FM-001–050)     | Foundation       | Models, agents, execution engine, pre-release infra            |
| V2 (FM-051–100)     | Breadth          | Collaboration, code ops, frontend parity, local mode           |
| V3 (FM-101–140)     | Depth            | SPEC lifecycle, templates, checkpoints, release operations     |
| V4 (FM-141–210)     | Ecosystem        | Integration, intelligence, enterprise, and scale               |
| **V5 (FM-211–250)** | **Intelligence** | **Dynamic agents, graph memory, deliberation, explainability** |

### Strategic Position

After V5, ForgeMind is no longer just an AI engineering platform — it becomes an **adaptive reasoning system** that can decompose any complex task, spawn specialized intelligence, deliberate across perspectives, remember everything it has learned, and explain why it chose every path. This positions ForgeMind as infrastructure for autonomous engineering at any scale.

---

## 2. V5 Architecture Vision

### Core Architecture Shift

```
V4 Architecture (Current):
┌─────────────────────────────────────────────┐
│  Operator Request                            │
│       ↓                                      │
│  Orchestrator → Fixed Agent Pool             │
│       ↓          (5 agents, static roster)   │
│  Task Execution → Artifact Output            │
│       ↓                                      │
│  Approval Gates → Completion                 │
└─────────────────────────────────────────────┘

V5 Architecture (Target):
┌─────────────────────────────────────────────────────────┐
│  Operator Request                                        │
│       ↓                                                  │
│  Master Orchestration Service                            │
│       ↓ (interprets task, selects strategy)               │
│  ┌──────────────────────────────────────────────┐        │
│  │  Dynamic Agent Runtime                        │        │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │        │
│  │  │Agent │←→│Agent │←→│Agent │←→│Agent │  ...  │        │
│  │  │  A   │ │  B   │ │  C   │ │  D   │        │        │
│  │  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘        │        │
│  │     └────────┴────────┴────────┘              │        │
│  │           Redis Event Bus                     │        │
│  └──────────────────────────────────────────────┘        │
│       ↓                                                  │
│  Council Deliberation Layer                              │
│       ↓ (multi-agent reasoning & debate)                  │
│  Graph Memory Store                                      │
│       ↓ (persistent context, relationships, reasoning)    │
│  FAIR Workflow Engine                                     │
│       ↓ (explainable scoring + confidence signals)        │
│  Execution & Artifacts                                   │
└─────────────────────────────────────────────────────────┘
```

### Key Technology Additions

| Component             | Technology                 | Purpose                                         |
| --------------------- | -------------------------- | ----------------------------------------------- |
| Agent Runtime         | Redis Streams + Workers    | Dynamic agent spawning and lifecycle management |
| Inter-Agent Messaging | Redis Pub/Sub + Streams    | Agent-to-agent communication bus                |
| Graph Memory          | Neo4j or Apache AGE        | Structured relationship and reasoning storage   |
| Deliberation Protocol | Custom protocol over Redis | Council debate, proposal, and resolution flow   |
| FAIR Scoring Engine   | Python service             | Weighted multi-signal workflow selection        |

---

## 3. V5 Theme by Block

### Wave 17 — FM-211 to FM-220: Dynamic Multi-Agent Runtime Foundations

**Purpose:** Replace the static agent roster with a dynamic runtime where specialized sub-agents are spawned as microservice workers on demand, communicate through Redis, and are managed by a master orchestration service.

**Why this comes first:** Everything in V5 depends on agents being dynamic. Council deliberation, graph memory injection, and adaptive workflow selection all require agents that can be created, configured, and destroyed based on task requirements — not a fixed pool.

**User value:** Tasks get purpose-built agents instead of forcing work into 5 generic roles.
**Engineering value:** Establishes the runtime, messaging, and lifecycle primitives that all subsequent V5 blocks build on.
**Differentiation:** No other AI engineering platform dynamically composes agent teams per-task.

#### Milestones

| FM     | Title                                    | Description                                                                                                           |
| ------ | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| FM-211 | Master Orchestration Service             | Central service that interprets incoming tasks, determines required capabilities, and plans agent deployment strategy |
| FM-212 | Agent Blueprint & Registry V2            | Declarative agent blueprint format (capabilities, resource needs, communication ports) replacing static agent configs |
| FM-213 | Dynamic Agent Spawning                   | Runtime creation of agent workers as isolated processes/containers from blueprints, with health monitoring            |
| FM-214 | Redis Event Bus — Core Messaging         | Redis Streams–based event bus for agent-to-agent and agent-to-orchestrator communication with delivery guarantees     |
| FM-215 | Agent-to-Agent Communication Protocol    | Structured message format, request/response patterns, and broadcast channels for inter-agent coordination             |
| FM-216 | Agent Lifecycle Management               | Start, pause, resume, terminate, and auto-scale agent workers with resource tracking and graceful shutdown            |
| FM-217 | Task Decomposition Engine                | Automatic breakdown of complex tasks into sub-tasks with dependency analysis, assigned to spawned sub-agents          |
| FM-218 | Agent Capability Discovery               | Runtime capability advertisement — agents register skills dynamically; orchestrator queries available capabilities    |
| FM-219 | Runtime Monitoring & Agent Observability | Health dashboards, message throughput, agent CPU/memory, inter-agent latency, execution trace per agent               |
| FM-220 | Dynamic Runtime Tests, Docs & Hardening  | Comprehensive test suite, failure injection testing, documentation, and production readiness validation               |

---

### Wave 18 — FM-221 to FM-230: Council Collaboration & Deliberation Engine

**Purpose:** Enable multiple agents to engage in structured deliberation on complex decisions — moving beyond V4's voting-based council to a full proposal-debate-resolution protocol that produces higher-quality outcomes.

**Why this sequence:** With dynamic agents from Wave 17, the system can now assemble purpose-built councils for specific decisions. This block defines how those agents reason together, not just vote.

**User value:** Complex architectural and design decisions get multi-perspective analysis with visible reasoning trails.
**Engineering value:** The deliberation protocol becomes reusable infrastructure for any multi-agent decision anywhere in the platform.
**Differentiation:** Council-style AI deliberation with explainable reasoning chains — not seen in current AI dev tools.

#### Milestones

| FM     | Title                                  | Description                                                                                                            |
| ------ | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| FM-221 | Deliberation Protocol Specification    | Formal protocol: proposal → evidence gathering → debate rounds → synthesis → resolution, with timeouts and escalation  |
| FM-222 | Council Assembly & Role Assignment     | Dynamic council formation — select agents by expertise, assign roles (proposer, critic, synthesizer, mediator)         |
| FM-223 | Proposal & Counter-Proposal Engine     | Agents generate structured proposals with rationale; others generate counter-proposals with alternative evidence       |
| FM-224 | Evidence & Reasoning Chain Capture     | Every argument, counter-argument, and evidence citation is captured as a structured reasoning chain                    |
| FM-225 | Debate Orchestration & Turn Management | Managed debate rounds with turn limits, relevance scoring, and convergence detection                                   |
| FM-226 | Synthesis & Resolution Engine          | Automatic synthesis of debate outcomes into actionable decisions with confidence scores and dissent notes              |
| FM-227 | Human Escalation & Override Protocol   | When councils deadlock or confidence is below threshold, structured escalation to human operators with context         |
| FM-228 | Council Memory & Precedent System      | Past council decisions become searchable precedent — future councils can reference prior reasoning                     |
| FM-229 | Council Analytics & Quality Metrics    | Track deliberation quality: decision reversal rate, confidence accuracy, time-to-resolution, diversity of perspectives |
| FM-230 | Council Engine Tests, Docs & Hardening | End-to-end deliberation tests, edge cases (deadlocks, bad faith agents, timeout cascades), documentation               |

---

### Wave 19 — FM-231 to FM-240: Graph Memory & Persistent Reasoning

**Purpose:** Introduce a graph-based memory store where all context, reasoning, relationships, and outputs are persisted as connected nodes — enabling agents to reason over structured history rather than flat context windows.

**Why this sequence:** Dynamic agents (Wave 17) and council deliberation (Wave 18) both generate rich reasoning data. This block gives that data a permanent, queryable home with relationship semantics that flat databases can't provide.

**User value:** ForgeMind remembers everything — decisions, relationships between components, why things were built a certain way — and uses that knowledge to make better future decisions.
**Engineering value:** Graph memory replaces the linear execution memory from V2 with a proper knowledge graph that any service can query.
**Differentiation:** Graph-native AI memory with relationship-aware reasoning — a fundamental capability gap in existing AI platforms.

#### Milestones

| FM     | Title                                   | Description                                                                                                                               |
| ------ | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| FM-231 | Graph Memory Store Foundation           | Graph database integration (Neo4j/Apache AGE), connection pooling, schema design for ForgeMind's domain model                             |
| FM-232 | Entity & Relationship Schema            | Node types (Agent, Task, Decision, Artifact, Component, Pattern) and edge types (produced_by, depends_on, contradicts, supports, refines) |
| FM-233 | Automatic Context Ingestion             | Pipeline that automatically extracts entities and relationships from execution artifacts, decisions, and discussions                      |
| FM-234 | Reasoning Chain Persistence             | Store multi-step reasoning as connected graph paths — premises → inferences → conclusions with confidence at each step                    |
| FM-235 | Graph-Aware Context Retrieval           | Query engine that traverses the graph to assemble relevant context for agents — replaces flat prompt stuffing                             |
| FM-236 | Cross-Project Knowledge Transfer        | Graph queries that surface patterns, decisions, and lessons from other projects with relevance scoring                                    |
| FM-237 | Temporal Reasoning & Decision Evolution | Track how decisions and understanding evolve over time — see why something changed, not just what changed                                 |
| FM-238 | Memory Decay & Relevance Scoring        | Time-weighted relevance — recent, frequently-referenced, and high-impact nodes are prioritized in context assembly                        |
| FM-239 | Graph Visualization & Explorer          | Interactive frontend for browsing the knowledge graph — node expansion, relationship traversal, search                                    |
| FM-240 | Graph Memory Tests, Docs & Hardening    | Full test coverage, graph query performance benchmarks, migration tooling, documentation                                                  |

---

### Wave 20 — FM-241 to FM-250: Adaptive Workflow Selection & FAIR Engine

**Purpose:** Build an explainable workflow selection engine that uses FAIR-style scoring (Findability, Accessibility, Interoperability, Reusability) combined with confidence signals and policy constraints to choose the optimal execution strategy for every task.

**Why this comes last:** Workflow selection needs all preceding V5 infrastructure — dynamic agents to choose from, council deliberation for complex routing decisions, and graph memory to learn from past workflow outcomes. This is the capstone that ties everything together.

**User value:** Operators see exactly why ForgeMind chose a particular execution approach, with confidence scores, alternative options, and policy explanations.
**Engineering value:** Closes the loop — workflow outcomes feed back into the graph memory, improving future selections.
**Differentiation:** Explainable, auditable AI workflow selection with FAIR principles — enterprise-grade transparency that no competitor offers.

#### Milestones

| FM     | Title                               | Description                                                                                                                                                                                                         |
| ------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| FM-241 | FAIR Scoring Framework              | Core scoring engine: Findability (can we locate required capabilities?), Accessibility (are agents/resources available?), Interoperability (can components work together?), Reusability (have we done this before?) |
| FM-242 | Confidence Signal Aggregation       | Combine multiple confidence signals: historical success rate, agent self-reported confidence, council confidence, graph memory strength                                                                             |
| FM-243 | Policy Constraint Engine            | Organizational policies (cost limits, agent restrictions, approval requirements, compliance rules) as hard/soft constraints on workflow selection                                                                   |
| FM-244 | Workflow Candidate Generation       | Generate multiple candidate execution strategies for a task, each with estimated cost, time, risk, and quality predictions                                                                                          |
| FM-245 | Explainable Routing Decisions       | Every workflow selection produces a human-readable explanation: "Chose Strategy A because [reasons], over Strategy B because [tradeoffs]"                                                                           |
| FM-246 | Outcome Feedback Loop               | Execution outcomes (success, failure, quality, time, cost) feed back into FAIR scores and graph memory for continuous improvement                                                                                   |
| FM-247 | A/B Workflow Experimentation        | Run alternative strategies on similar tasks to empirically measure which approaches work best for different task types                                                                                              |
| FM-248 | Operator Workflow Preferences       | Operators can express preferences (prefer speed over quality, prefer familiar patterns, minimize cost) that influence scoring weights                                                                               |
| FM-249 | FAIR Dashboard & Audit Trail        | Frontend dashboard showing workflow selection history, score breakdowns, outcome trends, and model accuracy over time                                                                                               |
| FM-250 | FAIR Engine Tests, Docs & Hardening | Comprehensive test suite, scoring edge cases, bias detection tests, documentation, and production validation                                                                                                        |

---

## 4. V5 Dependencies & Prerequisites

### Required Before V5 Begins

| Prerequisite                    | Source  | Why Required                                                     |
| ------------------------------- | ------- | ---------------------------------------------------------------- |
| FM-210 complete                 | V4      | All V4 ecosystem features are the foundation V5 builds on        |
| Redis 7+ in production stack    | Infra   | Event bus, pub/sub, and streams are core V5 messaging layer      |
| Graph database provisioned      | Infra   | Wave 19 requires Neo4j or Apache AGE deployed and accessible     |
| Agent model refactored to async | V4      | Dynamic spawning requires agents that run as independent workers |
| V4 API v1 stable                | FM-201+ | V5 agents and services communicate through stable APIs           |

### Cross-Block Dependencies

```
Wave 17 (Dynamic Runtime) ──────► Wave 18 (Council Engine)
         │                                   │
         └──────────────────► Wave 19 (Graph Memory)
                                             │
Wave 18 ─────────────────────────────────────┤
                                             ▼
                                    Wave 20 (FAIR Engine)
```

- Wave 17 is a hard prerequisite for Waves 18, 19, and 20
- Wave 18 and Wave 19 can be developed in parallel after Wave 17
- Wave 20 requires Waves 17, 18, and 19 to be substantially complete

---

## 5. V5 Implementation Plan

### Phasing

| Phase   | Waves        | Milestones      | Duration (est.) |
| ------- | ------------ | --------------- | --------------- |
| Phase E | Wave 17      | FM-211 → FM-220 | Foundation      |
| Phase F | Wave 18 + 19 | FM-221 → FM-240 | Parallel tracks |
| Phase G | Wave 20      | FM-241 → FM-250 | Capstone        |

### Success Criteria

V5 is successful when:

- Agents are dynamically spawned per-task rather than drawn from a static pool
- Council deliberation produces measurably better decisions than single-agent execution on complex tasks
- The knowledge graph contains 10,000+ nodes after 50 completed projects with sub-second query latency
- Operators can inspect workflow selection reasoning for any execution and understand why that path was chosen
- FAIR scores correlate with actual execution outcomes (>0.7 predictive accuracy after training period)
- Redis event bus handles 1,000+ messages/second with <10ms p99 latency
- All graph memory queries return in <200ms at production scale
- Test coverage remains above 90% across all V5 modules

### What V5 Does NOT Include

To keep scope bounded, the following are explicitly deferred to V6+:

- **Self-hosted deployment** — Still assumes managed platform model
- **Mobile app** — V5 focuses on agent intelligence, not new surfaces
- **Multi-language agent execution** — Agents remain Python-native; polyglot runtime is V6+
- **Federated multi-instance** — Single-cluster deployment; distributed federation is V6+
- **Autonomous goal setting** — V5 agents execute human-defined goals; self-directed agents are V6+

---

## 6. V5 Risk Assessment

| Risk                                              | Likelihood | Impact | Mitigation                                                             |
| ------------------------------------------------- | ---------- | ------ | ---------------------------------------------------------------------- |
| Graph DB adds operational complexity              | High       | Medium | Start with Apache AGE (PostgreSQL extension) to minimize new infra     |
| Redis as event bus has scaling limits             | Medium     | High   | Design for Redis Cluster from day one; Kafka migration path documented |
| Dynamic agent spawning increases security surface | High       | High   | Agent sandboxing, capability-based permissions, resource limits        |
| Council deliberation may not converge             | Medium     | Medium | Hard timeout + human escalation protocol in FM-227                     |
| FAIR scoring model needs training data            | High       | Medium | Bootstrap from V4 execution history; A/B testing in FM-247             |
| Over-engineering risk — complexity without ROI    | Medium     | High   | Each wave has its own hardening milestone; gate progression            |

---

## Appendix: V5 Milestone Index

| FM     | Title                                    | Wave |
| ------ | ---------------------------------------- | ---- |
| FM-211 | Master Orchestration Service             | 17   |
| FM-212 | Agent Blueprint & Registry V2            | 17   |
| FM-213 | Dynamic Agent Spawning                   | 17   |
| FM-214 | Redis Event Bus — Core Messaging         | 17   |
| FM-215 | Agent-to-Agent Communication Protocol    | 17   |
| FM-216 | Agent Lifecycle Management               | 17   |
| FM-217 | Task Decomposition Engine                | 17   |
| FM-218 | Agent Capability Discovery               | 17   |
| FM-219 | Runtime Monitoring & Agent Observability | 17   |
| FM-220 | Dynamic Runtime Tests, Docs & Hardening  | 17   |
| FM-221 | Deliberation Protocol Specification      | 18   |
| FM-222 | Council Assembly & Role Assignment       | 18   |
| FM-223 | Proposal & Counter-Proposal Engine       | 18   |
| FM-224 | Evidence & Reasoning Chain Capture       | 18   |
| FM-225 | Debate Orchestration & Turn Management   | 18   |
| FM-226 | Synthesis & Resolution Engine            | 18   |
| FM-227 | Human Escalation & Override Protocol     | 18   |
| FM-228 | Council Memory & Precedent System        | 18   |
| FM-229 | Council Analytics & Quality Metrics      | 18   |
| FM-230 | Council Engine Tests, Docs & Hardening   | 18   |
| FM-231 | Graph Memory Store Foundation            | 19   |
| FM-232 | Entity & Relationship Schema             | 19   |
| FM-233 | Automatic Context Ingestion              | 19   |
| FM-234 | Reasoning Chain Persistence              | 19   |
| FM-235 | Graph-Aware Context Retrieval            | 19   |
| FM-236 | Cross-Project Knowledge Transfer         | 19   |
| FM-237 | Temporal Reasoning & Decision Evolution  | 19   |
| FM-238 | Memory Decay & Relevance Scoring         | 19   |
| FM-239 | Graph Visualization & Explorer           | 19   |
| FM-240 | Graph Memory Tests, Docs & Hardening     | 19   |
| FM-241 | FAIR Scoring Framework                   | 20   |
| FM-242 | Confidence Signal Aggregation            | 20   |
| FM-243 | Policy Constraint Engine                 | 20   |
| FM-244 | Workflow Candidate Generation            | 20   |
| FM-245 | Explainable Routing Decisions            | 20   |
| FM-246 | Outcome Feedback Loop                    | 20   |
| FM-247 | A/B Workflow Experimentation             | 20   |
| FM-248 | Operator Workflow Preferences            | 20   |
| FM-249 | FAIR Dashboard & Audit Trail             | 20   |
| FM-250 | FAIR Engine Tests, Docs & Hardening      | 20   |

---

_End of ForgeMind V5 Roadmap — FM-211 through FM-250_
_Status: FUTURE — Not yet implemented. This is an architecture direction document._
