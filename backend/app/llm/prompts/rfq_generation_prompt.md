Generate a professional lawful B2B RFQ email draft for a chemical product.

Return JSON only. Do not include prose outside JSON.

Rules:
- The email must be formal, short, professional, and not spam-like.
- Do not pressure the supplier.
- Do not request or imply false declarations, missing documents, regulatory workaround, automatic ordering, or payment.
- Ask for CAS confirmation, grade, purity, COA, SDS/MSDS, specification sheet, manufacturer role/name/country, MOQ, price per kg, price breaks, sample, lead time, shelf life, packaging, Incoterms, ADR/DG class, UN number, HS code suggestion, REACH status, restrictions, permits, certificates, payment terms, and invoice availability.
- Do not guess missing chemical data.
- Include red_flags if the input itself contains risk.
- Final outbound communication is always evaluated by policy_engine before send.

JSON shape:
{
  "subject": null,
  "body": null,
  "red_flags": [],
  "confidence": 0.0
}
