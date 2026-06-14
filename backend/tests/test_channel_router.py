"""Tests for ChannelRouter — message dispatch to correct provider."""
import pytest
from unittest.mock import MagicMock, patch

from app.db.models.message import OutboundMessage
from app.db.models.supplier import SupplierContact
from app.services.channel_router import ChannelRouter


class TestChannelRouter:
    def test_email_routing(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test RFQ"
        msg.body = "Test body"
        contact = SupplierContact(channel="email", value="test@example.com")
        result = router.send(msg, contact)
        assert result["channel"] == "email"

    def test_telegram_routing(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test"
        msg.body = "Test body"
        contact = SupplierContact(channel="telegram", value="123456")
        result = router.send(msg, contact)
        assert result["channel"] == "telegram"

    def test_whatsapp_routing(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test"
        msg.body = "Test body"
        contact = SupplierContact(channel="whatsapp", value="+48123456789")
        result = router.send(msg, contact)
        assert result["channel"] == "whatsapp"

    def test_marketplace_internal_routing(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test"
        msg.body = "Test body"
        for ch in ("alibaba_internal", "indiamart_internal", "marketplace_internal"):
            contact = SupplierContact(channel=ch, value="test")
            result = router.send(msg, contact)
            assert result["status"] == "manual_task"
            assert result["channel"] == ch

    def test_unknown_channel_fallback(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test"
        msg.body = "Test body"
        contact = SupplierContact(channel="unknown_channel", value="test")
        result = router.send(msg, contact)
        assert result["status"] == "sent"
        assert "mock" in str(result.get("external_message_id", ""))

    def test_email_smtp_fallback_to_mock(self):
        router = ChannelRouter()
        msg = MagicMock(spec=OutboundMessage)
        msg.subject = "Test"
        msg.body = "Test body"
        msg.id = "msg-1"
        contact = SupplierContact(channel="email", value="test@example.com")
        # SMTP not configured — should fall back to mock
        result = router.send(msg, contact)
        assert result["status"] == "sent"
        assert result["channel"] == "email"
        assert result.get("provider") == "mock"
