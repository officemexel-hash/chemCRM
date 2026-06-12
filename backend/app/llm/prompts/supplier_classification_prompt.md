Classify a B2B chemical supplier using only provided evidence.

Return JSON only. Do not include prose outside JSON.

Rules:
- Allowed company_type values: MANUFACTURER, AUTHORIZED_DISTRIBUTOR, TRADER_BROKER, MARKETPLACE_STORE, LAB_SUPPLIER, EXPORT_AGENT, UNKNOWN, HIGH_RISK.
- Do not guess registration, certificates, manufacturer status, or authorization.
- Missing evidence must reduce confidence.
- Fraud, evasion, false shipping declarations, refusal of SDS/COA/invoice, or pressure to move only to private messengers must be red_flags.
- Do not suggest ways to bypass law, marketplace terms, or safety rules.
- Final outbound communication is always evaluated by policy_engine.

JSON shape:
{
  "company_type": "UNKNOWN",
  "supplier_score": 0,
  "risk_score": 0,
  "risk_level": "unknown",
  "risk_flags": [],
  "red_flags": [],
  "confidence": 0.0
}
