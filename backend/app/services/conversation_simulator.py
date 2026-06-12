from app.schemas.app_settings import AppSettings, ControlledQuestion
from app.schemas.conversation import ConversationSimulationRequest, ConversationSimulationResponse
from app.services.app_settings import default_app_settings


RED_FLAG_TERMS = {
    "misdeclare": "fraud/evasion language",
    "fake invoice": "fraud/evasion language",
    "false declaration": "fraud/evasion language",
    "avoid customs": "fraud/evasion language",
    "ship as gift": "fraud/evasion language",
    "no invoice": "invoice refusal/evasion language",
    "no sds": "safety document refusal",
    "no coa": "quality document refusal",
}


class ConversationSimulator:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self.app_settings = app_settings or default_app_settings()

    def simulate(self, payload: ConversationSimulationRequest) -> ConversationSimulationResponse:
        text = payload.supplier_message.lower()
        matched_rules = []
        red_flags = []
        block = False
        creates_manual_task = False
        detected_intent = "general_reply"
        recommended_action = "request_missing_information"
        response_template: str | None = None

        for term, label in RED_FLAG_TERMS.items():
            if term in text and label not in red_flags:
                red_flags.append(label)

        for rule in self.app_settings.response_playbook:
            if any(term.lower() in text for term in rule.trigger_terms):
                matched_rules.append(rule.name)
                detected_intent = rule.supplier_intent
                recommended_action = rule.recommended_action
                response_template = rule.response_template
                creates_manual_task = creates_manual_task or rule.creates_manual_task
                block = block or rule.block_if_matched

        missing_questions = self._missing_questions(text)
        if not response_template:
            response_template = self._default_response(missing_questions)

        if missing_questions and recommended_action == "request_missing_information":
            creates_manual_task = False
        if block:
            recommended_action = "block"
            creates_manual_task = True

        response_body = self._render_response(payload.supplier_name, response_template, missing_questions)
        training_notes = self._training_notes(matched_rules, missing_questions, red_flags, block)

        return ConversationSimulationResponse(
            detected_intent=detected_intent,
            recommended_action=recommended_action,
            response_subject=f"Re: RFQ follow-up - {recommended_action.replace('_', ' ')}",
            response_body=response_body,
            matched_rules=matched_rules,
            missing_controlled_questions=[question.key for question in missing_questions],
            red_flags=red_flags,
            creates_manual_task=creates_manual_task,
            block=block,
            approval_required=True,
            training_notes=training_notes,
        )

    def _missing_questions(self, text: str) -> list[ControlledQuestion]:
        missing: list[ControlledQuestion] = []
        for question in self.app_settings.controlled_questions:
            terms = _terms_for_question(question)
            if question.required and not any(term in text for term in terms):
                missing.append(question)
        return missing

    def _default_response(self, missing_questions: list[ControlledQuestion]) -> str:
        if not missing_questions:
            return (
                "Thank you for the information. We will review the details internally and come back with any approved next steps."
            )
        return (
            "Thank you for your reply. To complete our internal procurement review, please confirm the remaining controlled questions below."
        )

    def _render_response(
        self,
        supplier_name: str,
        response_template: str,
        missing_questions: list[ControlledQuestion],
    ) -> str:
        missing_block = ""
        if missing_questions:
            missing_block = "\n\nMissing controlled questions:\n" + "\n".join(
                f"- {question.text}" for question in missing_questions
            )
        signature = self._signature()
        return f"""Dear {supplier_name},

{response_template}{missing_block}

Please note that we require accurate product, safety, logistics, invoice, and compliance information. We cannot proceed with any false declaration, missing safety documentation, or workaround of applicable rules.

Kind regards,
{signature}
"""

    def _signature(self) -> str:
        if self.app_settings.sender.signature:
            return self.app_settings.sender.signature
        sender_name = self.app_settings.sender.name or "Procurement Team"
        sender_title = self.app_settings.sender.title or self.app_settings.sender.department or "Procurement"
        company_name = self.app_settings.company.trading_name or self.app_settings.company.legal_name
        return "\n".join(line for line in [sender_name, sender_title, company_name] if line)

    def _training_notes(
        self,
        matched_rules: list[str],
        missing_questions: list[ControlledQuestion],
        red_flags: list[str],
        block: bool,
    ) -> list[str]:
        notes = []
        if matched_rules:
            notes.append(f"Matched playbook rules: {', '.join(matched_rules)}.")
        if missing_questions:
            notes.append(f"Missing required controlled questions: {len(missing_questions)}.")
        if red_flags:
            notes.append(f"Red flags detected: {', '.join(red_flags)}.")
        if block:
            notes.append("Recommended action is BLOCK; do not continue without human compliance review.")
        if not notes:
            notes.append("No critical risk matched; response still requires approval before outbound use.")
        return notes


def _terms_for_question(question: ControlledQuestion) -> list[str]:
    terms_by_key = {
        "product_identity": ["cas", "purity", "assay", "grade", "product name"],
        "documents": ["coa", "sds", "msds", "specification", "tds"],
        "supplier_role": ["manufacturer", "distributor", "trading", "country of origin"],
        "commercial_terms": ["moq", "price", "lead time", "sample", "packaging"],
        "logistics_compliance": ["exw", "fob", "cif", "dap", "ddp", "adr", "un number", "hs code", "reach"],
        "payment_invoice": ["payment", "invoice", "tt", "lc", "escrow"],
    }
    return terms_by_key.get(question.key, [question.key.replace("_", " "), question.category.lower()])
