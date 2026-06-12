from app.marketplaces.alibaba import AlibabaConnector
from app.marketplaces.base import MarketplaceCompliance


class MadeInChinaConnector(AlibabaConnector):
    marketplace_name = "Made-in-China"
    compliance = MarketplaceCompliance(
        compliance_notes=[
            "Made-in-China has marketplace inquiry/contact flows for supplier contact.",
            "Use official UI/API or manually reviewed browser workflow only.",
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
        internal_messenger_channel="made_in_china_internal",
    )
