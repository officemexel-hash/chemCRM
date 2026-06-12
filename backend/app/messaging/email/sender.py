import smtplib
from email.message import EmailMessage as StdEmailMessage

from app.core.config import get_settings
from app.messaging.email.models import EmailMessage, EmailSendResult


class MockEmailProvider:
    def send(self, message: EmailMessage) -> EmailSendResult:
        return EmailSendResult(sent=True, external_message_id=f"mock-email-{abs(hash(message.body))}")


class SMTPEmailSender:
    def send(self, message: EmailMessage) -> EmailSendResult:
        settings = get_settings()
        if not settings.smtp_host or not settings.smtp_from:
            return EmailSendResult(sent=False, error="SMTP is not configured")
        msg = StdEmailMessage()
        msg["From"] = message.from_address or settings.smtp_from
        msg["To"] = message.to
        msg["Subject"] = message.subject
        for key, value in message.headers.items():
            msg[key] = value
        msg.set_content(message.body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
                if settings.smtp_use_tls:
                    smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(msg)
            return EmailSendResult(sent=True)
        except smtplib.SMTPException as exc:
            return EmailSendResult(sent=False, error=type(exc).__name__)
