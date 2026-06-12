Generate a short professional B2B follow-up email only for missing RFQ answers.

Return JSON only. Do not include prose outside JSON.

Rules:
- Ask only about missing_questions.
- Do not pressure the supplier.
- Do not suggest legal, transport, customs, or documentation workarounds.
- Do not request payment or order finalization.
- Include red_flags if the prior response suggests fraud or evasion.
- Final outbound communication is always evaluated by policy_engine before send.

JSON shape:
{
  "subject": null,
  "body": null,
  "red_flags": [],
  "confidence": 0.0
}
