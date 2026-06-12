from app.marketplaces.alibaba import AlibabaConnector
from app.marketplaces.base import MarketplaceCompliance


class IndiaMartConnector(AlibabaConnector):
    marketplace_name = "IndiaMART"
    compliance = MarketplaceCompliance(
        compliance_notes=[
            "IndiaMART inquiry/contact workflows must use official UI/API access or manual review.",
            "Do not bypass login, OTP, CAPTCHA, marketplace terms, or rate limits.",
            "Do not create accounts, accept terms, or send inquiries without human approval.",
        ],
        rate_limit_config={"mode": "manual_or_api", "max_requests_per_minute": 10},
        allowed_actions=["create_inquiry_draft", "create_internal_message_draft", "manual_review"],
        disallowed_actions=[
            "captcha_bypass",
            "login_bypass",
            "otp_bypass",
            "mass_messaging",
            "private_data_harvesting",
            "automatic_account_registration",
        ],
        requires_manual_review=True,
        supports_internal_messenger=True,
        internal_messenger_channel="indiamart_internal",
    )
