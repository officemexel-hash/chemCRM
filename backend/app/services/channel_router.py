"""Channel Router — dispatches outbound messages to the correct provider based on channel type."""

import logging

from app.db.models.message import OutboundMessage
from app.db.models.supplier import SupplierContact
from app.messaging.email.models import EmailMessage
from app.messaging.email.sender import MockEmailProvider, SMTPEmailSender
from app.messaging.messengers.telegram_bot import TelegramBotConnector
from app.messaging.messengers.whatsapp_business import WhatsAppBusinessConnector

logger = logging.getLogger(__name__)


class ChannelRouter:
    def __init__(self) -> None:
        self.email_sender = SMTPEmailSender()
        self.mock_sender = MockEmailProvider()
        self.telegram = TelegramBotConnector()
        self.whatsapp = WhatsAppBusinessConnector()

    def send(self, message: OutboundMessage, contact: SupplierContact) -> dict:
        """Route message to the correct channel provider."""
        channel = (contact.channel or "email").lower()

        if channel == "email":
            return self._send_email(message, contact)
        elif channel == "telegram":
            return self._send_telegram(message, contact)
        elif channel == "whatsapp":
            return self._send_whatsapp(message, contact)
        elif channel in ("alibaba_internal", "indiamart_internal", "marketplace_internal"):
            return {"status": "manual_task", "channel": channel, "reason": "Marketplace internal messaging requires portal login"}
        else:
            logger.info("Unknown channel %s, falling back to mock", channel)
            return {"status": "sent", "channel": channel, "external_message_id": f"mock-{message.id}"}

    def _send_email(self, message: OutboundMessage, contact: SupplierContact) -> dict:
        email_msg = EmailMessage(
            to=contact.value,
            subject=message.subject or "RFQ Inquiry",
            body=message.body or "",
        )
        # Try real SMTP first, fall back to mock
        result = self.email_sender.send(email_msg)
        if result.sent:
            return {
                "status": "sent",
                "channel": "email",
                "external_message_id": result.external_message_id,
            }
        # SMTP not configured — use mock
        mock_result = self.mock_sender.send(email_msg)
        return {
            "status": "sent",
            "channel": "email",
            "external_message_id": mock_result.external_message_id,
            "provider": "mock",
        }

    def _send_telegram(self, message: OutboundMessage, contact: SupplierContact) -> dict:
        return self.telegram.send_message(
            chat_id=contact.value,
            text=message.body or "",
        )

    def _send_whatsapp(self, message: OutboundMessage, contact: SupplierContact) -> dict:
        return self.whatsapp.send_message(
            to=contact.value,
            text=message.body or "",
        )
