---
name: chemical-sourcing-rfq-crm-testing
description: Use when testing or validating this Chemical Sourcing RFQ CRM, including CAS validation, policy_engine safety cases, supplier scoring, RFQ generation, quote extraction, integration campaign flow, Docker/Compose smoke checks, and frontend build verification.
metadata:
  short-description: Test the RFQ CRM
---

# Chemical Sourcing RFQ CRM Testing

## Required Checks

- Run backend tests from `backend/` with `pytest`.
- Verify `/health` returns `{"status":"ok"}`.
- Run frontend build from `frontend/` with `npm run build`.
- For dependency audits, report unresolved advisories instead of applying breaking `--force` fixes blindly.
- Test autonomous campaign runs for both low-risk auto-send and marketplace/manual-review branches.

## Policy Engine Cases

Always cover:

- Messenger without `consent_evidence` -> `BLOCK`.
- Unknown/manual-review substance -> `REQUIRES_APPROVAL`.
- Invalid CAS -> `BLOCK`.
- High-risk supplier -> `REQUIRES_APPROVAL` or `BLOCK`.
- Low-risk business email + public evidence + `auto_send_enabled=true` -> `ALLOW_AUTO_SEND`.
- Fraud/evasion language -> `BLOCK`.

## Integration Flow

Validate:

1. Create substance by CAS.
2. Enrich with mock provider.
3. Create supplier with contact evidence.
4. Classify supplier.
5. Create RFQ campaign.
6. Generate RFQ draft.
7. Evaluate policy and approve/send via mock.
8. Add inbound response.
9. Parse quote.
10. Check quote comparison and audit log.
