Extract a supplier quote from an inbound B2B RFQ reply.

Return JSON only. Do not include prose outside JSON.

Rules:
- Do not guess missing fields. Use null or "not answered".
- Preserve numeric prices only when explicit.
- If multiple price breaks are present, return all of them in prices.
- Flag fraud, false declarations, evasion, refusal of SDS/COA/invoice, or pressure to use undocumented private channels.
- Include missing_questions for important RFQ questions not answered.
- Include confidence from 0.0 to 1.0.
- Final outbound follow-up or reply is always evaluated by policy_engine before send.

JSON shape:
{
  "supplier_type": "unknown",
  "substance_confirmed": null,
  "cas_confirmed": null,
  "grade": null,
  "purity": null,
  "moq": null,
  "prices": [],
  "lead_time": null,
  "payment_terms": null,
  "sample_available": null,
  "sample_price": null,
  "packaging": null,
  "coa_available": null,
  "sds_available": null,
  "reach_status": null,
  "adr_class": null,
  "un_number": null,
  "hs_code": null,
  "shelf_life": null,
  "certificates": [],
  "production_capacity": null,
  "red_flags": [],
  "missing_questions": [],
  "recommended_next_action": "manual_review",
  "confidence": 0.0
}
