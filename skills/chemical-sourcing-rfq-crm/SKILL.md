---
name: chemical-sourcing-rfq-crm
description: Use when developing or reviewing this Chemical Sourcing RFQ CRM, especially backend domain logic, supplier/contact evidence, RFQ messaging, policy_engine decisions, marketplace/messenger connectors, and compliance-sensitive procurement workflows.
metadata:
  short-description: Build the RFQ CRM safely
---

# Chemical Sourcing RFQ CRM Development

## Core Rules

- Preserve the legal B2B procurement boundary: no CAPTCHA bypass, login bypass, rate-limit bypass, mass spam, private messenger cold outreach, regulatory evasion, automatic ordering, or payment.
- Every outbound path must call `policy_engine` before send.
- Every supplier contact must carry `source_url` and `evidence_text`.
- Messenger automation requires `consent_evidence`; Signal/Wickr stay manual-task only in MVP.
- Alibaba/Made-in-China internal marketplace messengers are official portal channels, not private messengers; model them as `*_internal` draft/manual workflows unless an approved official API exists.
- Do not hardcode secrets. Use `.env` and `app/core/config.py`.
- Do not let LLM output mutate state or send messages without Pydantic validation and policy evaluation.
- For "autonomous" features, implement orchestration that sends only `ALLOW_AUTO_SEND`; every other branch must create a manual task and audit log.

## Backend Workflow

1. Start with models/schemas/services before routes.
2. Keep SQLAlchemy models UUID-based and PostgreSQL-compatible.
3. Add audit log entries for campaign creation, enrichment, discovery, classification, policy decisions, approvals, sends, inbound parsing, quote extraction, and manual tasks.
4. Prefer mock/provider interfaces when real integrations require keys, accounts, or legal review.
5. Treat regulatory screening as flagging/manual review, not legal advice.

## Frontend Workflow

- Build operational screens first: dashboard, substances, suppliers, RFQ campaign, inbox, quote comparison, manual tasks, settings.
- Surface policy reasons and risk flags prominently.
- Keep forms explicit about CAS, quantity, grade, destination, intended lawful use, and document requirements.
