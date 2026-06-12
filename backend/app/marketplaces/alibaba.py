from app.marketplaces.base import MarketplaceCompliance, MarketplaceInquiryDraft


class AlibabaConnector:
    marketplace_name = "Alibaba"
    compliance = MarketplaceCompliance(
        compliance_notes=[
            "Alibaba has internal marketplace inquiry/messaging flows for supplier contact.",
            "Use official Alibaba UI/API or manually reviewed browser workflow only.",
            "Do not bypass login, CAPTCHA, marketplace terms, or rate limits.",
            "Do not create accounts, accept terms, solve CAPTCHA, or send inquiries without human approval.",
        ],
        rate_limit_config={"mode": "manual_or_api", "max_requests_per_minute": 10},
        allowed_actions=["create_inquiry_draft", "create_internal_message_draft", "manual_review"],
        disallowed_actions=[
            "captcha_bypass",
            "login_bypass",
            "mass_messaging",
            "private_data_harvesting",
            "automatic_account_registration",
        ],
        requires_manual_review=True,
        supports_internal_messenger=True,
        internal_messenger_channel="alibaba_internal",
    )

    def search_products(self, cas: str, names: list[str], limit: int = 20) -> list[dict]:
        return []

    def get_supplier_profile(self, url: str) -> dict:
        return {"url": url, "requires_manual_review": True}

    def create_inquiry_draft(self, *args, **kwargs) -> dict:
        return {"status": "draft_only", "requires_manual_review": True}

    def create_internal_message_draft(
        self,
        supplier_profile_url: str,
        subject: str,
        body: str,
    ) -> MarketplaceInquiryDraft:
        return MarketplaceInquiryDraft(
            marketplace=self.marketplace_name,
            channel=self.compliance.internal_messenger_channel or "marketplace_internal",
            supplier_profile_url=supplier_profile_url,
            subject=subject,
            body=body,
            status="draft_only",
            requires_manual_review=True,
            required_actions=[
                "human must log in with an authorized business account",
                "human must review portal terms and supplier profile evidence",
                "human must handle CAPTCHA/2FA if presented",
                "policy_engine must evaluate the outbound draft before any send",
            ],
        )

    def send_inquiry(self, *args, **kwargs) -> dict:
        return {
            "status": "blocked",
            "reason": "Direct Alibaba internal messenger send is not implemented in MVP; use draft/manual task or an approved official API.",
        }

    def fetch_messages(self, *args, **kwargs) -> list[dict]:
        return []
