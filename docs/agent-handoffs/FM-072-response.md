# FM-072 — Advanced Frontend Parity II: Response Document

**Title**: Frontend pages for Costs, Audit, Knowledge, and Credential Vault  
**Status**: ✅ Complete  
**Completed**: 2026-04-02

---

## Deliverables

### TypeScript type files (4)
- `apps/web/types/cost.ts` — CostRecord, CostRecordList, CostSummary
- `apps/web/types/audit.ts` — EventType (10 values), AuditSummary, AuditExport, AuditEvent
- `apps/web/types/knowledge.ts` — KnowledgeType (7 values), ProjectKnowledge, ProjectKnowledgeList
- `apps/web/types/vault.ts` — SecretStatus (4 values), CredentialVault, CredentialVaultList

### API client lib files (4)
- `apps/web/lib/costs.ts` — fetchCostRecords, fetchRunCostSummary, fetchProjectCostSummary, fetchCostBreakdown
- `apps/web/lib/audit.ts` — fetchAuditSummary, exportAuditJson, exportAuditCsv (with query param builders)
- `apps/web/lib/knowledge.ts` — fetchProjectKnowledge, fetchKnowledgeEntry
- `apps/web/lib/vault.ts` — fetchCredentials, fetchCredential

### Dashboard pages (4)
- `apps/web/app/dashboard/costs/page.tsx` — Cost breakdown summary (3 stat cards + model breakdown) + paginated record list with token stats
- `apps/web/app/dashboard/audit/page.tsx` — Audit summary event breakdown badges + full event list with colored event types, payload display
- `apps/web/app/dashboard/knowledge/page.tsx` — Project ID input → knowledge list with type badges, relevance scores, tags, content preview
- `apps/web/app/dashboard/vault/page.tsx` — Credential list with status badges, masked preview, env key, scopes, expiry info

### Sidebar update
- `apps/web/components/layout/sidebar.tsx` — 4 new nav items added (Costs/dollar-sign, Audit/file-text, Knowledge/info, Vault/lock)

---

## Verification

- **TypeScript errors**: 0 across all 13 files (4 types + 4 lib + 4 pages + sidebar)
- **Backend tests**: 34/34 passed in 2.37s
- **Pattern compliance**: All pages follow the established `useCallback+useEffect+useState`, Breadcrumb→Header→Error→Loading→Empty→Data pattern with CSS variables

---

## Evidence chain

All type definitions derived from reading backend Pydantic schemas:
- `apps/api/schemas/cost.py` → CostRecordRead, CostRecordList
- `apps/api/schemas/credential_vault.py` → CredentialVaultRead, CredentialVaultList
- `apps/api/schemas/knowledge.py` → ProjectKnowledgeRead, ProjectKnowledgeList
- `apps/api/models/execution_event.py` → EventType enum (10 values)
- `apps/api/models/project_knowledge.py` → KnowledgeType enum (7 values)
- `apps/api/models/credential_vault.py` → SecretStatus enum (4 values)

All API routes derived from reading backend route files:
- `apps/api/routes/costs.py` → 4 endpoints under `/costs`
- `apps/api/routes/audit.py` → 3 endpoints under `/audit`
- `apps/api/routes/knowledge.py` → 6 endpoints (projects + knowledge)
- `apps/api/routes/credential_vault.py` → 6 endpoints under `/vault/credentials`
