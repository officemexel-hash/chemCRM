from app.marketplaces.alibaba import AlibabaConnector
from app.marketplaces.indiamart import IndiaMartConnector
from app.marketplaces.made_in_china import MadeInChinaConnector
from app.marketplaces.molbase import MolbaseConnector


def test_alibaba_internal_message_draft_is_manual_only() -> None:
    draft = AlibabaConnector().create_internal_message_draft(
        supplier_profile_url="https://supplier.en.alibaba.com",
        subject="RFQ: demo",
        body="Please quote CAS 64-17-5.",
    )
    assert draft.marketplace == "Alibaba"
    assert draft.channel == "alibaba_internal"
    assert draft.status == "draft_only"
    assert draft.requires_manual_review is True
    assert "policy_engine must evaluate the outbound draft before any send" in draft.required_actions


def test_made_in_china_internal_message_channel() -> None:
    draft = MadeInChinaConnector().create_internal_message_draft(
        supplier_profile_url="https://supplier.made-in-china.com",
        subject="RFQ: demo",
        body="Please quote CAS 7732-18-5.",
    )
    assert draft.marketplace == "Made-in-China"
    assert draft.channel == "made_in_china_internal"


def test_molbase_internal_message_channel() -> None:
    draft = MolbaseConnector().create_internal_message_draft(
        supplier_profile_url="https://supplier.molbase.com",
        subject="RFQ: demo",
        body="Please quote CAS 7732-18-5.",
    )
    assert draft.marketplace == "Molbase"
    assert draft.channel == "molbase_internal"


def test_indiamart_internal_message_channel() -> None:
    draft = IndiaMartConnector().create_internal_message_draft(
        supplier_profile_url="https://www.indiamart.com/demo-supplier",
        subject="RFQ: demo",
        body="Please quote CAS 64-17-5.",
    )
    assert draft.marketplace == "IndiaMART"
    assert draft.channel == "indiamart_internal"
    assert draft.requires_manual_review is True
