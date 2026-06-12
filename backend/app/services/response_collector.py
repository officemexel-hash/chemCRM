"""Response Collector — collects inbound replies from email, Telegram, and manual entry."""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import new_uuid
from app.db.models.message import InboundMessage
from app.db.models.supplier import SupplierCompany
from app.messaging.email.receiver import IMAPEmailReceiver
from app.messaging.messengers.telegram_bot import TelegramBotConnector
from app.services.audit_log import AuditLogService

logger = logging.getLogger(__name__)


class ResponseCollectorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditLogService(db)

    def collect_email_replies(self) -> list[InboundMessage]:
        """Poll IMAP for new emails and create InboundMessage records."""
        receiver = IMAPEmailReceiver()
        received = receiver.fetch_unseen()
        messages: list[InboundMessage] = []

        for email_msg in received:
            # Try to match to a supplier by from_address
            supplier = self._match_supplier_by_email(email_msg.from_address)
            inbound = InboundMessage(
                id=new_uuid(),
                company_id=supplier.id if supplier else None,
                channel="email",
                from_address=email_msg.from_address,
                subject=email_msg.subject,
                body=email_msg.body,
                external_message_id=email_msg.external_message_id,
                thread_id=email_msg.headers.get("In-Reply-To") or email_msg.headers.get("References"),
                received_at=datetime.now(timezone.utc),
                parsed=False,
            )
            self.db.add(inbound)
            messages.append(inbound)

        if messages:
            self.db.flush()
            self.audit.log("email_replies_collected", None, None, {"count": len(messages)})
        return messages

    def collect_telegram_replies(self) -> list[InboundMessage]:
        """Poll Telegram Bot API for new messages and create InboundMessage records."""
        connector = TelegramBotConnector()
        updates = connector.get_updates()
        messages: list[InboundMessage] = []

        for update in updates:
            msg = update.get("message") or update.get("edited_message")
            if not msg:
                continue
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text", "")
            if not text:
                continue

            # Try to match supplier by chat_id stored in contact value
            supplier = self._match_supplier_by_contact_value(chat_id, "telegram")
            inbound = InboundMessage(
                id=new_uuid(),
                company_id=supplier.id if supplier else None,
                channel="telegram",
                from_address=chat_id,
                subject=None,
                body=text,
                external_message_id=str(update.get("update_id", "")),
                received_at=datetime.now(timezone.utc),
                parsed=False,
            )
            self.db.add(inbound)
            messages.append(inbound)

        if messages:
            self.db.flush()
            self.audit.log("telegram_replies_collected", None, None, {"count": len(messages)})
        return messages

    def manual_entry(
        self,
        company_id: str,
        body: str,
        channel: str = "manual",
        campaign_id: str | None = None,
        from_address: str | None = None,
        subject: str | None = None,
    ) -> InboundMessage:
        """Create a manual inbound message entry."""
        inbound = InboundMessage(
            id=new_uuid(),
            company_id=company_id,
            campaign_id=campaign_id,
            channel=channel,
            from_address=from_address,
            subject=subject,
            body=body,
            received_at=datetime.now(timezone.utc),
            parsed=False,
        )
        self.db.add(inbound)
        self.db.flush()
        self.audit.log("manual_reply_entry", "inbound_message", inbound.id, {"channel": channel})
        self.db.commit()
        return inbound

    def _match_supplier_by_email(self, email_address: str) -> SupplierCompany | None:
        """Try to find a supplier matching the email address domain."""
        if not email_address or "@" not in email_address:
            return None
        domain = email_address.rsplit("@", 1)[-1].lower()
        # First try exact match on contact value
        from app.db.models.supplier import SupplierContact
        contact = self.db.scalar(
            select(SupplierContact).where(SupplierContact.value.ilike(f"%{domain}%")).limit(1)
        )
        if contact:
            return self.db.get(SupplierCompany, contact.company_id)
        return None

    def _match_supplier_by_contact_value(self, value: str, channel: str) -> SupplierCompany | None:
        """Try to find a supplier by contact value and channel."""
        from app.db.models.supplier import SupplierContact
        contact = self.db.scalar(
            select(SupplierContact).where(
                SupplierContact.value == value,
                SupplierContact.channel == channel,
            ).limit(1)
        )
        if contact:
            return self.db.get(SupplierCompany, contact.company_id)
        return None
