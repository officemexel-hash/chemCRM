import logging

from app.core.config import get_settings
from app.messaging.messengers.base import MessengerCompliance

logger = logging.getLogger(__name__)


class WhatsAppBusinessConnector:
    compliance = MessengerCompliance(
        allowed_actions=["send_template_message", "send_text", "customer_care_window_reply"],
        disallowed_actions=["whatsapp_web_automation", "captcha_bypass"],
        requires_consent_evidence=True,
        manual_only=False,
    )

    def __init__(self) -> None:
        settings = get_settings()
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.from_number = settings.twilio_whatsapp_from

    def _is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def create_message_draft(self, to: str, text: str, **kwargs) -> dict:
        """Create a message draft (does not send)."""
        if not self._is_configured():
            return {"status": "draft", "channel": "whatsapp", "error": "Twilio credentials not configured"}
        return {
            "status": "draft",
            "channel": "whatsapp",
            "to": to,
            "text": text,
        }

    def send_message(self, to: str, text: str, **kwargs) -> dict:
        """Send a WhatsApp message via Twilio Business API."""
        if not self._is_configured():
            return {"status": "blocked", "channel": "whatsapp", "reason": "Twilio credentials not configured"}

        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)

            # Ensure numbers have whatsapp: prefix
            from_num = self.from_number if self.from_number.startswith("whatsapp:") else f"whatsapp:{self.from_number}"
            to_num = to if to.startswith("whatsapp:") else f"whatsapp:{to}"

            message = client.messages.create(
                body=text,
                from_=from_num,
                to=to_num,
            )

            if message.error_code:
                return {
                    "status": "send_failed",
                    "channel": "whatsapp",
                    "error": message.error_message or f"Error code: {message.error_code}",
                    "external_message_id": message.sid,
                }

            return {
                "status": "sent",
                "channel": "whatsapp",
                "external_message_id": message.sid,
                "to": to_num,
            }
        except ImportError:
            return {"status": "send_failed", "channel": "whatsapp", "error": "twilio package not installed"}
        except Exception as e:
            logger.error("WhatsApp send error: %s", e)
            return {"status": "send_failed", "channel": "whatsapp", "error": str(e)}
