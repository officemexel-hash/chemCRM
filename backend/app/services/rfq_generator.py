from dataclasses import dataclass

from app.schemas.app_settings import AppSettings
from app.services.app_settings import default_app_settings


@dataclass(frozen=True)
class RFQDraft:
    subject: str
    body: str


class RFQGenerator:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self.app_settings = app_settings or default_app_settings()

    def generate(self, substance, campaign, supplier=None) -> RFQDraft:
        cas = getattr(substance, "cas", "unknown")
        name = getattr(substance, "primary_name", None) or "the referenced product"
        supplier_name = getattr(supplier, "name", None) or "Sales Team"
        quantity = getattr(campaign, "quantity", None) or "to be confirmed"
        grade = getattr(campaign, "required_grade", None) or "please specify available grades"
        destination = (
            getattr(campaign, "destination_country", None)
            or self.app_settings.default_destination_country
            or "our destination country"
        )
        intended_use = (
            getattr(campaign, "intended_use", None)
            or self.app_settings.default_intended_use
            or "lawful industrial evaluation"
        )
        company_name = (
            self.app_settings.company.trading_name
            or self.app_settings.company.legal_name
            or "our company"
        )
        sender_name = self.app_settings.sender.name or "Procurement Team"
        sender_title = self.app_settings.sender.title or self.app_settings.sender.department or "Procurement"
        signature = self._signature(sender_name, sender_title)
        controlled_questions = self._controlled_questions(destination)

        subject = f"RFQ: {name} / CAS {cas} / {quantity}"
        body = f"""Dear {supplier_name},

I am contacting you on behalf of {company_name}. We are evaluating qualified business suppliers for a lawful B2B procurement project and would like to request a quotation for the product below.

Product identity:
- CAS number: {cas}
- Product name: {name}
- Required grade: {grade}
- Intended use: {intended_use}
- Quantity: {quantity}
- Delivery destination: {destination}

Please confirm the following controlled questions in your reply:
{controlled_questions}

Please also let us know if any regulatory limitation prevents supply for the stated lawful use or destination. We do not request or accept false declarations, missing safety documentation, or any workaround of applicable rules.

Kind regards,
{signature}
"""
        return RFQDraft(subject=subject, body=body)

    def _controlled_questions(self, destination: str) -> str:
        questions = self.app_settings.controlled_questions or default_app_settings().controlled_questions
        lines = []
        for index, question in enumerate(questions, 1):
            text = question.text.replace("{destination}", destination)
            required = "required" if question.required else "optional"
            lines.append(f"{index}. [{question.category} / {required}] {text}")
        return "\n".join(lines)

    def _signature(self, sender_name: str, sender_title: str) -> str:
        if self.app_settings.sender.signature:
            return self.app_settings.sender.signature
        lines = [sender_name, sender_title]
        company_name = self.app_settings.company.trading_name or self.app_settings.company.legal_name
        if company_name:
            lines.append(company_name)
        if self.app_settings.sender.email:
            lines.append(str(self.app_settings.sender.email))
        if self.app_settings.company.website:
            lines.append(self.app_settings.company.website)
        return "\n".join(line for line in lines if line)
