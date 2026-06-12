from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class MarketplaceCompliance:
    compliance_notes: list[str] = field(default_factory=list)
    rate_limit_config: dict = field(default_factory=dict)
    allowed_actions: list[str] = field(default_factory=list)
    disallowed_actions: list[str] = field(default_factory=list)
    requires_manual_review: bool = True
    supports_internal_messenger: bool = False
    internal_messenger_channel: str | None = None


@dataclass(frozen=True)
class MarketplaceInquiryDraft:
    marketplace: str
    channel: str
    supplier_profile_url: str
    subject: str
    body: str
    status: str = "draft_only"
    requires_manual_review: bool = True
    required_actions: list[str] = field(default_factory=list)


class MarketplaceConnector(Protocol):
    compliance: MarketplaceCompliance

    def search_products(self, cas: str, names: list[str], limit: int = 20) -> list[dict]:
        ...

    def get_supplier_profile(self, url: str) -> dict:
        ...

    def create_inquiry_draft(self, *args, **kwargs) -> dict:
        ...

    def create_internal_message_draft(self, *args, **kwargs) -> MarketplaceInquiryDraft:
        ...

    def send_inquiry(self, *args, **kwargs) -> dict:
        ...

    def fetch_messages(self, *args, **kwargs) -> list[dict]:
        ...
