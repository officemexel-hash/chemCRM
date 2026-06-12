# Chemical Sourcing RFQ CRM

Production-oriented MVP for legal B2B chemical sourcing, supplier CRM, RFQ campaigns, quote comparison, and communication governance.

This project is intentionally built as a procurement/CRM system, not as a scraping, spam, marketplace-bypass, or regulatory-evasion tool.

## What Is Implemented

- FastAPI backend with PostgreSQL-compatible SQLAlchemy models and Alembic migration (23 tables).
- React/Next.js 16 dashboard with 12+ views (Dashboard, Bulk Import, Substances, Discovery, Suppliers, Campaigns, Inbox, Quotes, Tariff, Reports, Documents, Settings).
- CAS validation with checksum.
- PubChem PUG REST enrichment provider + Mock provider.
- Search query generator and legal SearchProvider abstraction.
- Supplier classification and scoring.
- RFQ draft generation with controlled questions from enterprise settings.
- Policy engine for outbound messages with safety bypass mode (`bypass_all`) for scientific/testing/internal use.
- Autonomous campaign orchestrator with real SMTP send capability.
- Production hardening: request IDs, security headers, optional global auth gate, CORS/TrustedHost middleware.
- Enterprise settings: company identity, sender persona, controlled RFQ questions, response playbooks, training scenarios.
- Conversation simulator + ConversationEngine for multi-round auto-followups.
- Batch CAS sourcing workflow: CSV/Excel import, campaign creation, search queries, channel task planning, reports.
- Substance Intelligence API: supplier consolidation, contact history, quote terms, packaging, Incoterms by transport, production cost analysis.
- Substance Research Database: per-substance dossier with supplier interactions, production analysis (equipment, sub-products, cost breakdown), Incoterms comparison.
- Document generation: company letterhead, Letter of Intent (LOI), Purchase Order (PO) with transport-mode Incoterms responsibility matrix.
- Customs duty lookup: HS code suggestion, duty rates, VAT, legal use descriptions for customs clearance.
- Substance analog suggestions: cheaper structural/functional alternatives with price comparison.
- MSDS/COA document rebranding service (pypdf + weasyprint for PDF generation).
- Real OpenAI and Anthropic LLM providers (API key required).
- Playwright browser automation framework for marketplace/form/messenger automation (optional).
- 44 pytest tests with full campaign integration flow coverage.
- Docker Compose for 5-container deployment (postgres, redis, backend, worker, frontend).

## Safety Boundaries

The system deliberately does not implement:

- CAPTCHA bypass.
- Rate-limit bypass.
- Login bypass.
- Google scraping without an API.
- Marketplace terms bypass.
- Mass spam or cold outreach to unknown private accounts.
- Private messenger automation.
- Personal data harvesting without a business contact basis.
- Forged documents, customs declarations, transport descriptions, or invoices.
- Supplier COA/SDS/MSDS rebranding as your own document.
- Chemical synthesis recipes, process parameters, or production instructions.
- Regulatory evasion for restricted, controlled, hazardous, precursor, or prohibited substances.
- Automatic ordering, payment, or transaction finalization.

Default outbound posture is conservative:

- Every outbound message is a draft or requires approval unless policy conditions are low risk.
- Auto-send is allowed only for low-risk public business email/form contacts with `source_url`, `evidence_text`, no regulatory flags, supplier website, and `campaign.auto_send_enabled=true`.
- Messenger contacts require `consent_evidence`; Signal and Wickr are manual-task only in MVP.
- Fraud/evasion language blocks outbound workflow.
- Every policy decision is persisted on the outbound message and important actions are written to `audit_log`.
- Email and messenger APIs are intentionally not wired in the current production path; the app generates drafts, simulations, approvals, manual tasks, and audit evidence.
- Safety override exists only for authorized local/testing workflows and never enables hard-blocked behavior or real external sends.

## Requirements

- Docker Compose for deployment.
- Python 3.12+ for local backend work.
- Node.js 22+ for local frontend work.
- PostgreSQL 16 and Redis 7 when not using Docker.

## Local Setup

Copy environment defaults if you want to customize values:

```bash
cp .env.example .env
```

The Compose file has safe defaults, so `docker compose up` can run without a local `.env`.

## Docker Compose

Verified working with Docker Desktop 29.x and Compose v5.x on Windows.

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:3000`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

For production, set:

```env
APP_ENV=production
SECRET_KEY=<strong random secret>
AUTH_REQUIRED=true
BACKEND_CORS_ORIGINS=https://your-crm.example
ALLOWED_HOSTS=your-api.example,localhost
```

## Backend

Install locally:

```bash
cd backend
python -m venv ../.venv
../.venv/bin/python -m pip install -e ".[dev]"
```

Windows PowerShell:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Run API:

```bash
uvicorn app.main:app --reload
```

Run tests:

```bash
pytest
```

Run demo seed:

```bash
python scripts/seed_demo.py
```

Demo login:

- Email: `demo@example.com`
- Password: `ChangeMe123!`

## Enterprise Settings

Endpoints:

```http
GET /settings/defaults
GET /settings/app
PUT /settings/app
```

Configured objects:

- `company`: legal name, trading name, registration/VAT/EORI, website, address, country.
- `sender`: name, title, email, phone, department, signature.
- `controlled_questions`: required RFQ questions grouped by category.
- `response_playbook`: trigger terms, supplier intent, recommended action, response template, manual-task/block flags.
- `training_scenarios`: sample supplier messages and expected actions for operator training.

RFQ and follow-up drafts use these settings so the system writes on behalf of a real company and named person.

## Conversation Simulator

Endpoint:

```http
POST /conversation-simulator/simulate
```

Request:

```json
{
  "supplier_name": "Demo Supplier",
  "supplier_message": "We can quote USD 12/kg, but COA and SDS are not available before payment.",
  "channel": "manual",
  "stage": "training"
}
```

The simulator returns:

- detected supplier intent,
- recommended action,
- response draft,
- matched playbook rules,
- missing controlled questions,
- red flags,
- whether manual task or block is required.

It is deterministic and policy-oriented; it does not train a private model or send messages.

## Batch CAS Sourcing

Endpoint:

```http
POST /sourcing/batches
GET /sourcing/batches/{batch_id}
GET /sourcing/batches/{batch_id}/report
```

Example request:

```json
{
  "name": "June sourcing run",
  "csv_text": "CAS,quantity\n64-17-5,100 kg\n7732-18-5,200 kg",
  "quantity": "100 kg",
  "destination_country": "Poland",
  "required_grade": "technical grade",
  "intended_use": "lawful industrial validation",
  "channels": [
    "legal_search",
    "contact_form",
    "alibaba_internal",
    "made_in_china_internal",
    "molbase_internal",
    "indiamart_internal",
    "whatsapp_business",
    "telegram_bot",
    "signal_manual",
    "threema_gateway",
    "wickr_manual"
  ],
  "create_campaigns": true
}
```

The service validates and deduplicates CAS numbers, creates missing substances, creates RFQ campaigns, generates supplier search queries, and creates manual/API-only tasks for each selected channel. Form submissions, Alibaba/Made-in-China/Molbase/IndiaMART internal chats, and messengers are represented as reviewed tasks or drafts unless a lawful official integration is configured. It does not bypass login, CAPTCHA, portal terms, consent requirements, or rate limits.

## Documents, Customs, And Analogs

Endpoints:

```http
POST /documents/letterhead
POST /documents/letter-of-intent
POST /documents/purchase-order
GET /documents/incoterms-guide?transport_mode=sea
POST /documents/customs-duty
POST /documents/substance-analogs
```

The document module generates letterhead-based HTML/text documents:

- Letter of Intent (LOI) for supplier qualification and non-binding procurement intent.
- Purchase Order (PO) with transport mode, suggested Incoterms, and responsibility matrix.
- Optional save to `generated_documents` with `audit_log` entry when `save_to_crm=true`.

PO generation supports transport modes `sea`, `air`, `road`, `rail`, `courier`, and `multimodal`. The selected transport mode narrows suggested Incoterms and shows which party handles transport, insurance, export customs, import customs, and unloading.

Customs duty lookup is a screening helper only. It suggests HS code, duty wording, VAT notes, lawful-use descriptions, regulatory notes, official-source handoff URL, confidence, and `manual_review_required=true`. Final HS/CN/TARIC/HTS classification and duty must be confirmed against official customs sources or a licensed customs broker before shipment.

Substance analog suggestions are curated screening leads for cheaper or functionally similar substitutes. Each analog includes CAS, name, structural similarity, functional similarity, price indication, advantages, disadvantages, similarity basis, and `requires_validation=true`.

## Test-Only Safety Override

Endpoint:

```http
GET /safety-override
PUT /safety-override
```

This endpoint always requires an authenticated admin bearer token. The first registered user becomes `admin`; later users are `user`.

Enable request:

```json
{
  "enabled": true,
  "reason": "Testing own local workflow behavior with mock-only sends.",
  "expires_in_minutes": 60,
  "confirm_test_only": true
}
```

Rules:

- Disabled in `APP_ENV=production`.
- Requires admin authorization.
- Requires a reason and explicit `confirm_test_only=true`.
- Has a TTL of 1-1440 minutes.
- Writes `audit_log`.
- Converts eligible soft policy stops into `TEST_OVERRIDE_ALLOW`.
- Orchestrator records `test_override_simulated_send`, not a real send.

Hard blocks remain hard blocks:

- invalid CAS,
- restricted/blocked substance,
- critical regulatory flag,
- fraud/evasion,
- private messenger without consent,
- Signal/Wickr automation,
- real external send,
- portal login/CAPTCHA/terms bypass,
- account registration.

## Alembic

The MVP can auto-create tables with `AUTO_CREATE_TABLES=true`. For normal database migration flow:

```bash
cd backend
alembic upgrade head
```

To create future migrations:

```bash
alembic revision --autogenerate -m "describe change"
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
npm run start
```

`NEXT_PUBLIC_API_BASE_URL` controls the backend URL.

## VPS Deployment

Linux VPS:

1. Install Docker Engine and Docker Compose plugin.
2. Clone/copy this repository.
3. Create `.env` from `.env.example`.
4. Set a strong `SECRET_KEY` and real PostgreSQL/SMTP/IMAP credentials.
5. Put Caddy/Nginx in front of ports `3000` and `8000`.
6. Run `docker compose up -d --build`.

Windows VPS / WSL2:

1. Install WSL2 with Ubuntu.
2. Install Docker Desktop with WSL integration or Docker Engine inside WSL.
3. Work from the Linux filesystem for better volume performance.
4. Run the same Compose commands from WSL.

Reverse proxy notes:

- Terminate TLS at Nginx/Caddy.
- Forward `/api` or API subdomain to backend `8000`.
- Forward app host to frontend `3000`.
- Set `BACKEND_CORS_ORIGINS` to the public frontend origin.

## SMTP, IMAP, SPF, DKIM, DMARC

Configure SMTP/IMAP only through `.env`:

- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`
- `IMAP_HOST`, `IMAP_PORT`, `IMAP_USERNAME`, `IMAP_PASSWORD`

For production sending:

- Publish SPF for the sending host/provider.
- Enable DKIM signing at the mail provider.
- Publish DMARC policy, initially `p=none`, then tighten after monitoring.
- Do not log SMTP/IMAP passwords or tokens.
- Keep approval and audit logging enabled.

## SearchProvider

Implemented providers:

- `MockSearchProvider` for tests/demo.
- `ManualImportProvider` for user-supplied URLs.
- `GenericSearchProvider` skeleton for lawful Search API integration.

Do not add browser scraping of Google or other search engines without an allowed API and terms review.

## MarketplaceConnector

Skeletons exist for:

- Alibaba
- Made-in-China
- Molbase
- IndiaMART

Marketplaces are modeled as portals that can expose inquiry/messaging flows. The MVP supports `create_internal_message_draft(...)`, which returns a draft/manual-review object for the portal's internal channel:

- `alibaba_internal`
- `made_in_china_internal`
- `molbase_internal`
- `indiamart_internal`

Direct send is blocked in MVP unless a lawful official API or approved business integration is implemented. Human review must handle login, terms, CAPTCHA/2FA, account ownership, and final send.

Connectors expose compliance notes, rate limits, allowed actions, disallowed actions, internal messenger support, and manual review requirements.

## MessengerConnector

Skeletons exist for:

- WhatsApp Business API
- Telegram Bot API
- Threema Gateway
- WeChat Official Account
- Signal manual task
- Wickr manual task

Messenger automation requires `consent_evidence`. Signal and Wickr are blocked for automatic send in MVP.

## Policy Engine

`backend/app/services/policy_engine.py` evaluates:

- CAS validity.
- Substance regulatory status and flags.
- Supplier risk level and fraud/evasion indicators.
- Contact `source_url` and `evidence_text`.
- Messenger consent evidence.
- Auto-send campaign configuration.

Decisions:

- `DRAFT_ONLY`
- `REQUIRES_APPROVAL`
- `ALLOW_AUTO_SEND`
- `TEST_OVERRIDE_ALLOW` for mock-only simulated sends during admin-approved local testing
- `BLOCK`

## Autonomous Campaign Runs

Endpoint:

```http
POST /campaigns/{campaign_id}/run-autonomous
```

Request:

```json
{
  "supplier_ids": [],
  "dry_run": false,
  "allow_duplicates": false
}
```

Behavior:

- Generates RFQ drafts for selected suppliers, or all suppliers if `supplier_ids` is empty.
- Selects the primary supplier contact.
- Evaluates every draft with `policy_engine`.
- Sends only `ALLOW_AUTO_SEND` messages through the mock send path in MVP.
- Creates `manual_tasks` for `REQUIRES_APPROVAL` and `BLOCK`.
- Skips duplicates unless `allow_duplicates=true`.
- Writes audit entries for each evaluated outbound message and the overall run.

This is the safe autonomy boundary. Portal login, CAPTCHA, account registration, marketplace terms acceptance, private messenger outreach, and high-risk/regulatory cases remain human-controlled.

## Consent Evidence

`consent_evidence` stores:

- Company.
- Contact channel.
- Evidence type.
- Source URL.
- Source text.
- Screenshot path.
- Collection timestamp.

If a supplier replies by email asking to move to WhatsApp/Telegram/WeChat/Threema, store that reply as consent evidence before considering any official API-based automation.

## LLM Providers

Implemented:

- `LLMProvider` protocol.
- `MockLLMProvider`.
- OpenAI/Anthropic provider skeletons without hardcoded keys.

All LLM output must be JSON and validated with Pydantic. LLMs never send messages directly; policy engine always decides final outbound handling.

## Test Coverage

Current pytest coverage (44 tests) includes:

- CAS validator.
- Policy engine blocking/approval/auto-send paths (bypass_all support).
- Supplier classifier.
- RFQ generator.
- Search query generator.
- Quote extraction schema.
- Integration campaign flow from substance creation to quote comparison.
- Autonomous campaign run for low-risk auto-send and marketplace manual-review branches.
- Enterprise settings API and conversation simulator.
- Document generation (letterhead, LOI, PO, customs duty, substance analogs).
- Batch CAS sourcing import and report endpoints.
- Test-only safety override authorization, bypass_all full-bypass mode, and production lock.
- Marketplace connector compliance.
- Security hardening (headers, production validation).
- Substance intelligence and manufacturing analysis.

Run:

```bash
cd backend
pytest
```

## Repo-Local Agent Skills

The `skills/` directory contains lightweight `SKILL.md` runbooks for agents working on this repository:

- `skills/chemical-sourcing-rfq-crm/SKILL.md`
- `skills/chemical-sourcing-rfq-crm-testing/SKILL.md`

They are project documentation, not globally installed Codex skills.

## Current MVP Limitations

- PubChem real provider exists but routes use mock enrichment by default.
- Search and marketplace integrations are mock/skeleton unless a lawful API is configured.
- Alibaba/Made-in-China/Molbase/IndiaMART internal messenger support is draft/manual-task only; no automated portal login, registration, CAPTCHA, or send.
- Autonomous campaign run uses the mock send path; SMTP/marketplace real sends still require explicit provider wiring and approval.
- Email and communicator APIs are skipped for now by design; production work is focused on drafts, controls, simulation, approvals, and audit.
- Test-only safety override cannot be enabled in production and never enables real sends or portal bypass.
- Email sending uses mock workflow in API send path; SMTP sender class is present but not wired as default.
- Contact form automation is a safe skeleton and creates manual-task style results.
- Worker tasks log queued actions but most heavy workflows remain synchronous or skeleton.
- Regulatory screening is not legal advice; it is a local flagging/manual-review layer.
- Frontend has operational views and API-backed loading, but advanced forms/actions are not fully wired.
- `npm audit --omit=dev` reports a moderate advisory in Next's nested `postcss` dependency; latest published Next is used and the remaining fix path currently suggests an unsafe downgrade.
