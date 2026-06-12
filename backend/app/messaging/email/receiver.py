import email
import imaplib
import logging
from email.header import decode_header

from app.core.config import get_settings
from app.messaging.email.models import ReceivedEmail

logger = logging.getLogger(__name__)


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result_parts: list[str] = []
    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            result_parts.append(part.decode(encoding or "utf-8", errors="replace"))
        else:
            result_parts.append(part)
    return " ".join(result_parts)


def _extract_body(msg: email.message.Message) -> str:
    """Extract plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
                except Exception:
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        except Exception:
            pass
    return ""


class MockEmailReceiver:
    def fetch_unseen(self) -> list[ReceivedEmail]:
        return []


class IMAPEmailReceiver:
    def fetch_unseen(self) -> list[ReceivedEmail]:
        """Fetch unseen emails from IMAP inbox."""
        settings = get_settings()
        if not settings.imap_host or not settings.imap_username or not settings.imap_password:
            logger.info("IMAP not configured, skipping email fetch")
            return []

        emails: list[ReceivedEmail] = []
        try:
            with imaplib.IMAP4_SSL(settings.imap_host, settings.imap_port) as imap:
                imap.login(settings.imap_username, settings.imap_password)
                imap.select("INBOX")
                status, data = imap.search(None, "UNSEEN")
                if status != "OK" or not data[0]:
                    return []

                message_ids = data[0].split()
                for mid in message_ids[-50:]:  # Process up to 50 most recent
                    try:
                        fetch_status, fetch_data = imap.fetch(mid, "(RFC822)")
                        if fetch_status != "OK":
                            continue
                        raw_email = fetch_data[0][1]
                        msg = email.message_from_bytes(raw_email)

                        from_addr = _decode_header_value(msg.get("From", ""))
                        subject = _decode_header_value(msg.get("Subject", ""))
                        body = _extract_body(msg)
                        message_id_header = msg.get("Message-ID", "")

                        emails.append(
                            ReceivedEmail(
                                external_message_id=message_id_header or mid.decode(),
                                from_address=from_addr,
                                subject=subject,
                                body=body[:50000],  # Truncate very long bodies
                                headers={
                                    "Message-ID": message_id_header,
                                    "In-Reply-To": msg.get("In-Reply-To", ""),
                                    "References": msg.get("References", ""),
                                    "Date": msg.get("Date", ""),
                                },
                            )
                        )
                        # Mark as seen
                        imap.store(mid, "+FLAGS", "\\Seen")
                    except Exception as e:
                        logger.warning("Error fetching email %s: %s", mid, e)
                        continue

        except imaplib.IMAP4.error as e:
            logger.error("IMAP connection error: %s", e)
        return emails
