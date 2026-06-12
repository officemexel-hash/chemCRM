from app.messaging.messengers.base import MessengerCompliance


class SignalManualConnector:
    compliance = MessengerCompliance(
        allowed_actions=["manual_task"],
        disallowed_actions=["automatic_send", "private_cold_outreach"],
        requires_consent_evidence=True,
        manual_only=True,
    )

    def create_message_draft(self, *args, **kwargs) -> dict:
        return {"status": "manual_task", "channel": "signal"}

    def send_message(self, *args, **kwargs) -> dict:
        return {"status": "blocked", "reason": "Signal automation is manual-task only in MVP."}
