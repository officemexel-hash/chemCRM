from dataclasses import dataclass


@dataclass(frozen=True)
class FormSubmissionResult:
    status: str
    reason: str | None = None
    screenshot_before: str | None = None
    screenshot_after: str | None = None


class ContactFormSubmitter:
    async def submit(self, url: str, fields: dict[str, str]) -> FormSubmissionResult:
        return FormSubmissionResult(
            status="manual_task",
            reason=(
                "Playwright form submission skeleton only. CAPTCHA/login/terms checks must be reviewed "
                "before enabling real submission."
            ),
        )
