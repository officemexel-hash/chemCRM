import logging

import httpx

from app.core.config import get_settings
from app.messaging.messengers.base import MessengerCompliance

logger = logging.getLogger(__name__)


class TelegramBotConnector:
    compliance = MessengerCompliance(
        allowed_actions=["send_text", "receive_text", "send_document"],
        disallowed_actions=["spam", "unsolicited_messaging"],
        requires_consent_evidence=True,
        manual_only=False,
    )

    def __init__(self, bot_token: str | None = None) -> None:
        settings = get_settings()
        self.bot_token = bot_token or settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else ""

    def _is_configured(self) -> bool:
        return bool(self.bot_token)

    def create_message_draft(self, chat_id: str, text: str, **kwargs) -> dict:
        """Create a message draft (does not send)."""
        if not self._is_configured():
            return {"status": "draft", "channel": "telegram", "error": "Bot token not configured"}
        return {
            "status": "draft",
            "channel": "telegram",
            "chat_id": chat_id,
            "text": text,
            "parse_mode": kwargs.get("parse_mode", "HTML"),
        }

    def send_message(self, chat_id: str, text: str, **kwargs) -> dict:
        """Send a message via Telegram Bot API."""
        if not self._is_configured():
            return {"status": "blocked", "channel": "telegram", "reason": "Bot token not configured"}

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": kwargs.get("parse_mode", "HTML"),
                    },
                )
                data = response.json()
                if data.get("ok"):
                    return {
                        "status": "sent",
                        "channel": "telegram",
                        "external_message_id": str(data["result"]["message_id"]),
                        "chat_id": chat_id,
                    }
                return {
                    "status": "send_failed",
                    "channel": "telegram",
                    "error": data.get("description", "Unknown error"),
                }
        except httpx.HTTPError as e:
            logger.error("Telegram send error: %s", e)
            return {"status": "send_failed", "channel": "telegram", "error": str(e)}

    def get_updates(self, offset: int | None = None, limit: int = 100) -> list[dict]:
        """Poll for new messages/updates from Telegram."""
        if not self._is_configured():
            return []

        try:
            with httpx.Client(timeout=30) as client:
                response = client.get(
                    f"{self.base_url}/getUpdates",
                    params={"offset": offset, "limit": limit, "timeout": 10},
                )
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
                return []
        except httpx.HTTPError as e:
            logger.error("Telegram getUpdates error: %s", e)
            return []
