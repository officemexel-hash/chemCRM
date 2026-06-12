from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str
    from_address: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EmailSendResult:
    sent: bool
    external_message_id: str | None = None
    error: str | None = None
