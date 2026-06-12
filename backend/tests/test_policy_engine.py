from types import SimpleNamespace

from app.schemas.policy import PolicyDecisionValue
from app.services.policy_engine import PolicyEngine


def _base_context(**overrides):
    message = SimpleNamespace(channel="email", body="Please quote.")
    supplier = SimpleNamespace(
        name="Acme Chemicals",
        website="https://acme.example",
        notes="",
        risk_level="low",
        risk_score=0,
        contacts=[],
    )
    substance = SimpleNamespace(
        cas="64-17-5",
        regulatory_status="unreviewed",
        requires_manual_review=False,
        regulatory_flags=[],
    )
    contact = SimpleNamespace(
        channel="email",
        value="sales@acme.example",
        source_url="https://acme.example/contact",
        evidence_text="Contact sales@acme.example for business inquiries.",
        consent_evidence_id=None,
    )
    supplier.contacts = [contact]
    campaign = SimpleNamespace(auto_send_enabled=True)
    values = {
        "message": message,
        "supplier": supplier,
        "substance": substance,
        "contact": contact,
        "campaign": campaign,
    }
    values.update(overrides)
    return values


def test_messenger_without_consent_blocks() -> None:
    ctx = _base_context()
    ctx["contact"].channel = "telegram"
    ctx["contact"].value = "@supplier"
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.BLOCK


def test_unknown_substance_requires_approval() -> None:
    ctx = _base_context()
    ctx["substance"].regulatory_status = "unknown"
    ctx["substance"].requires_manual_review = True
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.REQUIRES_APPROVAL


def test_invalid_cas_blocks() -> None:
    ctx = _base_context()
    ctx["substance"].cas = "64-17-4"
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.BLOCK


def test_high_risk_supplier_requires_approval() -> None:
    ctx = _base_context()
    ctx["supplier"].risk_level = "high"
    ctx["supplier"].risk_score = 90
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.REQUIRES_APPROVAL


def test_low_risk_business_email_auto_send_allowed() -> None:
    decision = PolicyEngine().evaluate_outbound_message(**_base_context())
    assert decision.decision == PolicyDecisionValue.ALLOW_AUTO_SEND


def test_supplier_fraud_evasion_flag_blocks() -> None:
    ctx = _base_context()
    ctx["supplier"].notes = "We can use false declaration to avoid customs."
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.BLOCK


def test_marketplace_internal_channel_requires_manual_review_not_consent_block() -> None:
    ctx = _base_context()
    ctx["contact"].channel = "alibaba_internal"
    ctx["contact"].value = "https://supplier.en.alibaba.com"
    ctx["contact"].source_url = "https://supplier.en.alibaba.com/product"
    ctx["contact"].evidence_text = "Supplier profile includes Contact Supplier marketplace action."
    decision = PolicyEngine().evaluate_outbound_message(**ctx)
    assert decision.decision == PolicyDecisionValue.REQUIRES_APPROVAL
    assert "create_marketplace_manual_task" in decision.required_actions
    assert not any("messenger channel without consent_evidence" in reason for reason in decision.reasons)
