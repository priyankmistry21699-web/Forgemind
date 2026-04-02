# @forgemind/types

> Shared TypeScript type definitions mirroring backend Pydantic schemas.

## Contents

22 domain type modules re-exported from `src/index.ts`:

| Module          | Key Types                                                      |
| --------------- | -------------------------------------------------------------- |
| activity        | `ActivityFeedEntry`, `Presence`, `UserContext`                 |
| agent           | `Agent`, `AgentStatus`                                         |
| approval        | `Approval`, `ApprovalStatus`                                   |
| artifact        | `Artifact`, `ArtifactType`                                     |
| audit           | `AuditEvent`, `AuditSummary`, `AuditExport`                    |
| connector       | `Connector`, `ProjectConnectorLink`, `ProjectReadinessSummary` |
| cost            | `CostRecord`, `CostSummary`                                    |
| council         | `CouncilSession`, `CouncilVote`                                |
| escalation      | `EscalationRule`, `EscalationEvent`                            |
| execution-event | `ExecutionEvent`, `ExecutionEventType`                         |
| governance      | `GovernancePolicy`                                             |
| knowledge       | `ProjectKnowledge`                                             |
| notification    | `Notification`, `DeliveryConfig`                               |
| planner         | `PromptIntakeRequest`, `PromptIntakeResponse`, `PlannerResult` |
| project-member  | `ProjectMember`, `ProjectRole`                                 |
| project         | `Project`, `ProjectStatus`                                     |
| replay          | `ReplaySnapshot`, `ExecutionTrace`                             |
| run             | `Run`, `RunStatus`                                             |
| task            | `Task`, `TaskStatus`                                           |
| trust           | `TrustScore`, `RiskSummary`                                    |
| vault           | `CredentialVault`, `SecretStatus`                              |
| workspace       | `Workspace`, `WorkspaceMember`, `WorkspaceRole`                |

## Usage

```typescript
import type { Project, Run, Task } from "@forgemind/types";
```
