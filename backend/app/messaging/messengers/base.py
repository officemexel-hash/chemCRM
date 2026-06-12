from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class MessengerCompliance:
    allowed_actions: list[str] = field(default_factory=list)
    disallowed_actions: list[str] = field(default_factory=list)
    requires_consent_evidence: bool = True
    manual_only: bool = False


class MessengerConnector(Protocol):
    compliance: MessengerCompliance

    def create_message_draft(self, *args, **kwargs) -> dict:
        ...

    def send_message(self, *args, **kwargs) -> dict:
        ...
