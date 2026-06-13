# Chemical Sourcing RFQ CRM Roadmap

Last cross-check: 2026-06-13  
Planning source of truth: this file.  
Status source documents: `README.md`, `CHEMCRM_CAPABILITIES.md`, `AGENTS.md`, backend tests, API routes, frontend views.

## How To Use This Roadmap

- Before planning a new task, check this file first.
- Cross-check task status against `README.md` and `CHEMCRM_CAPABILITIES.md`.
- Do not use `README.md` as the backlog. README is the product/status summary and historical change notes.
- After code changes, append new capability/change notes to `README.md` as bold bullets. Keep older entries unbolded and do not replace existing historical notes just to rewrite them.
- For full app smoke checks, use Docker Compose from `C:\Users\razor\OneDrive\Desktop\chemCRM`.
- For pytest, run locally from `backend/` for now. Do not run pytest through Compose yet.

## Status Legend

- `done` - implemented and documented.
- `verify` - likely implemented, but needs a targeted smoke/manual test or cleanup pass.
- `planned` - should be built next or soon.
- `future` - useful, but depends on earlier stabilization, external APIs, accounts, or legal review.
- `blocked` - cannot be implemented safely without external authorization, API terms, credentials, or policy decision.

## Documentation Cross-Check

| Area | Documentation status | Code/test signal | Roadmap status |
| --- | --- | --- | --- |
| Docker Compose deployment | `README.md` says 6-container Compose: postgres, redis, backend, worker, scheduler, frontend. `AGENTS.md` says Compose is preferred for full app smoke checks. | `docker-compose.yml`, backend/frontend Dockerfiles, `.dockerignore` files. Recent smoke check passed. | done |
| Pytest workflow | `README.md` documents `cd backend && pytest`. `AGENTS.md` says pytest is local for now, not Compose. | `backend/tests/*` has 44-test suite per README. | done |
| README update rule | `AGENTS.md` says append new README notes as bold bullets and never replace historical notes. | `README.md` has recent bold change bullets. | done |
| Core backend/API | `README.md` and `CHEMCRM_CAPABILITIES.md` describe substances, suppliers, campaigns, messages, quotes, tasks, audit, reports, sourcing, documents, tariff, settings. | `backend/app/api/routes/*`, `backend/app/services/*`. | done |
| Frontend operational dashboard | `README.md` says Next.js dashboard has 12+ views and recent CRUD/dialog work. | `frontend/src/components/views/*`, `DashboardApp.tsx`, `Dialogs.tsx`. | done / verify |
| CAS import and batch sourcing | Capabilities doc describes CSV/TSV/XLSX import and batch sourcing. | `bulk_import.py`, `sourcing_batch.py`, `BulkImportView.tsx`, `SourcingView.tsx`, tests. | done / verify |
| Substance Intelligence | Capabilities doc describes intelligence profile and manufacturing analysis. | `substance_intelligence.py`, `production_analyzer.py`, `SubstanceIntelligenceView.tsx`, tests. | done / verify |
| Documents / LOI / PO / customs / analogs | README says document generation, customs duty lookup, legal-use drafts, analog suggestions. | `documents.py`, `document_generator.py`, `customs_service.py`, `substance_analogs.py`, `DocumentsView.tsx`, tests. | done / planned enhancements |
| Quote extraction and comparison | README and capabilities doc describe quote extraction and comparison. | `quote_extractor.py`, `quotes.py`, `QuotesView.tsx`, tests. | done / planned CSV export |
| Marketplace connectors | README says Alibaba, Made-in-China, Molbase, IndiaMART are skeleton/draft/manual/API-only. | `backend/app/marketplaces/*`, marketplace tests. | future / blocked for real send |
| Messenger connectors | README says WhatsApp/Telegram/Threema/WeChat skeletons; Signal/Wickr manual-only. | `backend/app/messaging/messengers/*`. | future / blocked for real send |
| Email integration | README says mock send path is active; SMTP sender exists but is not wired as default. | `messaging/email/*`, `campaign_orchestrator.py`. | planned |
| Contact form automation | README says safe Playwright skeleton; CAPTCHA/login become manual tasks. | `messaging/forms/*`, `browser/playwright_manager.py`. | future |
| Safety override | README says local/test-only only; never production or portal bypass. | `safety_override.py`, tests. | done |
| Security hardening | README says request IDs, security headers, optional auth gate, production validation. | `core/middleware.py`, `core/config.py`, tests. | done / ongoing |
| npm audit advisory | README says moderate advisory remains in Next nested `postcss`; unsafe downgrade not applied. | Frontend lockfile. | monitor |

## Current Baseline

The current project state is a production-oriented MVP, not a finished autonomous procurement platform.

Implemented baseline:

- CAS validation, substance storage, enrichment provider interface, PubChem/mock provider path.
- Supplier database, contact evidence, classification, supplier score and risk score.
- RFQ campaigns, generated RFQ drafts, outbound/inbound messages, policy decisions, approvals, mock send path.
- Quote extraction schema and campaign quote comparison.
- Batch CAS import and sourcing plan generation.
- Substance Intelligence and high-level manufacturing/cost scoping.
- Document generation for letterhead-style commercial docs, LOI, PO, customs/legal-use support and analog suggestions.
- Settings for company identity, sender persona, controlled RFQ questions, playbooks and test-only safety override.
- Marketplace and messenger connector skeletons with safe/manual/API-only boundaries.
- Docker Compose smoke path and local pytest workflow.

Current hard boundaries:

- No CAPTCHA bypass.
- No login bypass.
- No portal account registration automation.
- No mass spam.
- No private messenger cold outreach.
- No automatic purchasing, payment or transaction finalization.
- No real portal/messenger send without official API, terms review, consent evidence and policy approval.

## Priority Backlog

### P0 - Planning And Hygiene

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P0.1 | Keep this `ROADMAP.md` as the first planning reference. | done | Prevents planning from drifting across chat history. | New tasks are added or updated here before implementation. |
| P0.2 | Fix `HTTP_422_UNPROCESSABLE_ENTITY` deprecation warnings. | planned | Low-risk cleanup; keeps tests quieter. | Replace deprecated constant with current Starlette/FastAPI constant; pytest warnings reduced. |
| P0.3 | Review and clean duplicate/legacy frontend components such as `NewViews.tsx` versus `views/*`. | planned | Reduces confusion after DashboardApp refactor. | Remove or quarantine unused components without breaking build. |
| P0.4 | Add a lightweight frontend live smoke test plan. | planned | Current Docker smoke checks HTTP, but not UI interactions. | Document or implement Playwright click-through for main views. |

### P1 - Small User-Facing Finishes

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P1.1 | Quotes CSV export button. | planned | User can use quote comparison outside the app. | `QuotesView` downloads visible comparison rows as CSV; empty state handled; frontend build passes. |
| P1.2 | Manual task assignment dialog. | planned | Manual review workflow needs ownership. | `TasksView` can assign a task to a user/operator where backend supports it, or creates a clear placeholder if user model is not exposed. |
| P1.3 | Discovery Import URLs dialog. | planned | Manual/legal URL import is part of safe sourcing. | User can paste URLs, submit to discovery/manual import endpoint, and see result or manual task. |
| P1.4 | Verify all toolbar buttons are live or intentionally disabled. | verify | README says toolbar buttons are wired; this needs a UI pass after refactor. | Every button either calls an API/dialog or has a clear disabled state. |

### P2 - Documents And Commercial Workflow

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P2.1 | Add/verify Rebrand tab if `RebrandView` exists or is intended. | planned | User asked for document handling and rebranding workflows; docs mention MSDS/COA rebranding service. | Dashboard tab routes to the correct view or roadmap clarifies it is intentionally omitted. |
| P2.2 | Company logo upload for letterhead/LOI/PO. | planned | Commercial docs need real company identity. | Settings or Documents view accepts logo upload; generated docs can include stored logo path; no secrets or unsafe file handling. |
| P2.3 | PO form transport/incoterms guidance refinement. | planned | Road/rail/sea/air transport changes Incoterms responsibility. | PO generation UI exposes transport type and shows responsibility matrix preview. |
| P2.4 | Customs/legal-use explainability improvements. | planned | Customs text needs traceable caveats and confidence. | Legal-use and HS suggestions show source/status/confidence and "not legal advice" caveat. |

### P3 - Provider Wiring

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P3.1 | PubChem real provider toggle in Settings. | planned | Provider exists, but routes use mock by default per README. | Settings can select mock/PubChem where backend supports it; failures degrade to manual review. |
| P3.2 | SMTP sender as explicit provider option, not default uncontrolled send. | planned | README says SMTP class exists but send path uses mock. | Admin can configure SMTP; send still passes policy engine; disabled by default; tests cover mock path. |
| P3.3 | IMAP polling configuration review. | future | Inbound automation needs secure credentials and operational policy. | Credentials from `.env` only; no secret logging; manual test path documented. |
| P3.4 | Legal SearchProvider integration adapter. | future | Real sourcing search needs lawful API provider. | Provider interface accepts configured API key; no Google scraping without API. |

### P4 - Marketplace, Forms And Messenger Flows

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P4.1 | Contact form draft/manual-assisted flow. | future | Useful but must handle CAPTCHA/login safely. | Detects simple form fields; CAPTCHA/login creates manual task; screenshots/audit supported. |
| P4.2 | Alibaba internal channel official/API workflow. | future / blocked | Real portal send requires account, terms review and official integration path. | Only draft/manual task until approved official API/business integration exists. |
| P4.3 | Made-in-China/Molbase/IndiaMART official/API workflows. | future / blocked | Same portal terms and account constraints. | Draft/manual/API-only; no automated login/CAPTCHA/registration. |
| P4.4 | WhatsApp/Telegram/Threema/WeChat official API connectors. | future / blocked | Requires credentials, consent evidence and official channel rules. | Each message passes policy engine; consent evidence required; Signal/Wickr stay manual-only. |

### P5 - Production Operations

| ID | Task | Status | Why | Acceptance |
| --- | --- | --- | --- | --- |
| P5.1 | Alembic-first production migration workflow. | planned | MVP can auto-create tables, but production should migrate. | README and deployment scripts prefer Alembic; `AUTO_CREATE_TABLES=false` path tested. |
| P5.2 | Backup/restore runbook for Postgres and storage. | planned | VPS operation needs recovery procedure. | Documented commands and restore test checklist. |
| P5.3 | Observability and audit export. | future | Enterprise use needs traceability. | Audit log filters/export; request IDs visible in logs. |
| P5.4 | Dependency/security review cadence. | future | README notes npm audit advisory. | Documented review policy; no unsafe force downgrades. |

## Suggested Next Order

Recommended next sequence:

1. `P0.2` Fix deprecation warnings.
2. `P1.1` Quotes CSV export.
3. `P1.3` Discovery Import URLs dialog.
4. `P1.2` Manual task assignment dialog.
5. `P0.3` Clean duplicate/legacy frontend components.
6. `P2.1` Rebrand tab decision/implementation.
7. `P2.2` Company logo upload for generated documents.
8. `P3.1` PubChem provider toggle.
9. `P3.2` SMTP sender provider option.
10. `P0.4` Frontend live smoke test.

Rationale:

- Start with low-risk cleanup and small UI features.
- Then improve document workflows because they are already documented as a core capability.
- Wire real external providers only after the UI and policy boundaries remain stable.
- Keep marketplace/messenger automation behind official/API/manual-review constraints.

## Task Template

Use this format when adding new roadmap work:

```md
### P?.? Task Name

Status: planned
Priority: small | medium | large
Depends on: ...
Docs cross-check:
- README.md: ...
- CHEMCRM_CAPABILITIES.md: ...

Goal:
...

Files likely touched:
- ...

Acceptance:
- ...

Verification:
- Local pytest from `backend/` if backend changes.
- `npm run build` from `frontend/` if frontend changes.
- Docker Compose smoke check for full app changes.
- README bold note after code changes.
```

