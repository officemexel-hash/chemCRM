from dataclasses import dataclass

from app.schemas.app_settings import AppSettings
from app.services.app_settings import default_app_settings


@dataclass(frozen=True)
class FollowupDraft:
    subject: str
    body: str


class FollowupGenerator:
    def __init__(self, app_settings: AppSettings | None = None) -> None:
        self.app_settings = app_settings or default_app_settings()

    def generate(self, missing_questions: list[str], original_subject: str | None = None) -> FollowupDraft:
        missing = [item for item in missing_questions if item]
        if not missing:
            missing = ["any missing technical, logistics, or compliance details"]
        bullet_list = "\n".join(f"- {item}" for item in missing)
        return FollowupDraft(
            subject=f"Follow-up: {original_subject or 'RFQ details'}",
            body=f"""Dear Sales Team,

Thank you for your reply. To complete our internal procurement review, could you please confirm the remaining items below?

{bullet_list}

Please note that we require accurate product, safety, shipping, and invoice documentation and cannot proceed with any workaround of applicable rules.

Kind regards,
{self._signature()}
""",
        )

    def _signature(self) -> str:
        if self.app_settings.sender.signature:
            return self.app_settings.sender.signature
        sender_name = self.app_settings.sender.name or "Procurement Team"
        sender_title = self.app_settings.sender.title or self.app_settings.sender.department or "Procurement"
        company_name = self.app_settings.company.trading_name or self.app_settings.company.legal_name
        return "\n".join(line for line in [sender_name, sender_title, company_name] if line)
