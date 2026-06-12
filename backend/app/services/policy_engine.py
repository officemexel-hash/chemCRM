from app.schemas.policy import PolicyDecision, PolicyDecisionValue
from app.schemas.safety import SafetyOverrideRead
from app.services.cas_validator import is_valid_cas
from app.services.supplier_classifier import FREE_EMAIL_DOMAINS


MESSENGER_CHANNELS = {"whatsapp", "telegram", "wechat", "threema", "signal", "wickr"}
MANUAL_ONLY_MESSENGERS = {"signal", "wickr"}
MARKETPLACE_INTERNAL_CHANNELS = {
    "marketplace_internal",
    "alibaba_internal",
    "made_in_china_internal",
    "molbase_internal",
    "indiamart_internal",
}
FRAUD_TERMS = {
    "misdeclare",
    "false declaration",
    "fake invoice",
    "avoid customs",
    "bypass regulation",
    "no invoice",
    "ship as gift",
}


class PolicyEngine:
    def __init__(self, safety_override: SafetyOverrideRead | None = None, strictness: str = "standard") -> None:
        self.safety_override = safety_override
        self.strictness = strictness

    def evaluate_outbound_message(self, message, supplier, substance, contact, campaign) -> PolicyDecision:
        reasons: list[str] = []
        required_actions: list[str] = []
        block = False

        cas = _value(substance, "cas")
        if not cas or not is_valid_cas(str(cas)):
            reasons.append("invalid CAS")
            block = True

        channel = str(_value(contact, "channel", _value(message, "channel", "")) or "").lower()
        contact_value = str(_value(contact, "value", "") or "")
        if channel in MANUAL_ONLY_MESSENGERS:
            reasons.append(f"{channel} automation is manual-task only in MVP")
            required_actions.append("create_manual_task")
            block = True
        if channel in MESSENGER_CHANNELS and not _value(contact, "consent_evidence_id"):
            reasons.append("messenger channel without consent_evidence")
            required_actions.append("collect_consent_evidence")
            block = True
        if channel in MARKETPLACE_INTERNAL_CHANNELS:
            reasons.append("marketplace internal messenger requires portal account and terms review")
            required_actions.append("create_marketplace_manual_task")

        combined_text = " ".join(
            str(item or "")
            for item in [
                _value(message, "body"),
                _value(supplier, "notes"),
                _value(supplier, "name"),
                _value(contact, "evidence_text"),
            ]
        ).lower()
        if _contains_fraud_evasion(combined_text):
            reasons.append("supplier or message contains fraud/evasion language")
            block = True

        regulatory_status = str(_value(substance, "regulatory_status", "unknown") or "unknown").lower()
        if regulatory_status in {"blocked", "restricted"}:
            reasons.append(f"substance regulatory_status={regulatory_status}")
            required_actions.append("manual_regulatory_review")
            block = True
        elif regulatory_status in {"unknown", "regulated"} or bool(
            _value(substance, "requires_manual_review", False)
        ):
            reasons.append("unknown or regulated substance requires approval")
            required_actions.append("manual_regulatory_review")

        regulatory_flags = list(_value(substance, "regulatory_flags", []) or [])
        if regulatory_flags:
            reasons.append("substance has regulatory flags")
            required_actions.append("review_regulatory_flags")
            if any(str(_value(flag, "severity", "")).lower() == "critical" for flag in regulatory_flags):
                block = True

        if not _value(contact, "source_url"):
            reasons.append("contact missing source_url")
            required_actions.append("add_contact_source_url")
        if not _value(contact, "evidence_text"):
            reasons.append("contact missing evidence_text")
            required_actions.append("add_contact_evidence_text")

        supplier_risk_level = str(_value(supplier, "risk_level", "") or "").lower()
        supplier_risk_score = float(_value(supplier, "risk_score", 0) or 0)
        if supplier_risk_level == "high" or supplier_risk_score >= 80:
            reasons.append("high risk supplier")
            required_actions.append("supplier_risk_review")
        if supplier_risk_score >= 120:
            block = True

        if _is_free_email(contact_value) and _is_only_contact(supplier):
            reasons.append("free email as only contact")
            required_actions.append("verify_business_contact")

        # LOG_ONLY mode: never hard-block, always allow with logged warnings
        if self.strictness == "log_only" and block:
            return PolicyDecision(
                decision=PolicyDecisionValue.LOG_ONLY,
                reasons=[f"[LOG_ONLY] would have blocked: {r}" for r in reasons],
                required_actions=required_actions,
            )

        if block:
            return PolicyDecision(
                decision=PolicyDecisionValue.BLOCK,
                reasons=reasons,
                required_actions=required_actions,
            )

        if self._can_auto_send(channel, contact_value, supplier, substance, contact, campaign, reasons):
            return PolicyDecision(
                decision=PolicyDecisionValue.ALLOW_AUTO_SEND,
                reasons=["low risk business contact and auto_send_enabled=true"],
                required_actions=[],
            )

        if self._can_test_override(reasons, channel):
            return PolicyDecision(
                decision=PolicyDecisionValue.TEST_OVERRIDE_ALLOW,
                reasons=[
                    "test-only safety override active; message may be simulated but not sent through real external providers",
                    *reasons,
                ],
                required_actions=["mock_or_simulated_send_only", *required_actions],
            )

        if not reasons:
            reasons.append("default outbound safety posture requires human approval")
        return PolicyDecision(
            decision=PolicyDecisionValue.REQUIRES_APPROVAL,
            reasons=reasons,
            required_actions=required_actions,
        )

    def evaluate_campaign_batch(self, messages, suppliers_map, substances_map, contacts_map, campaign) -> list[PolicyDecision]:
        """Evaluate all messages for a campaign at once. Returns one decision per message."""
        decisions: list[PolicyDecision] = []
        for msg in messages:
            supplier = suppliers_map.get(_value(msg, "company_id"))
            substance = substances_map.get(_value(campaign, "substance_id"))
            contact = contacts_map.get(_value(msg, "contact_id"))
            decision = self.evaluate_outbound_message(msg, supplier, substance, contact, campaign)
            decisions.append(decision)
        return decisions

    def _can_auto_send(
        self, channel: str, contact_value: str, supplier, substance, contact, campaign, reasons: list[str]
    ) -> bool:
        if reasons:
            return False
        if not bool(_value(campaign, "auto_send_enabled", False)):
            return False
        if channel not in {"email", "form"}:
            return False
        if channel == "email" and not _is_business_email(contact_value):
            return False
        if not _value(supplier, "website"):
            return False
        if str(_value(supplier, "risk_level", "low") or "low").lower() not in {"low", "unknown", ""}:
            return False
        if float(_value(supplier, "risk_score", 0) or 0) > 20:
            return False
        if bool(_value(substance, "requires_manual_review", False)):
            return False
        if str(_value(substance, "regulatory_status", "unreviewed") or "").lower() in {
            "unknown",
            "regulated",
            "restricted",
            "blocked",
        }:
            return False
        return bool(_value(contact, "source_url", None)) and bool(_value(contact, "evidence_text", None))

    def _can_test_override(self, reasons: list[str], channel: str) -> bool:
        override = self.safety_override
        if override is None or not override.active:
            return False
        if channel in MANUAL_ONLY_MESSENGERS:
            return False
        allowed = set(override.allowed_overrides)
        categories = {_reason_category(reason) for reason in reasons} or {"default_approval"}
        if "hard_block" in categories:
            return False
        return categories.issubset(allowed)


def _value(obj, key: str, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _is_business_email(value: str) -> bool:
    if "@" not in value:
        return False
    domain = value.rsplit("@", 1)[-1].lower()
    return domain not in FREE_EMAIL_DOMAINS and "." in domain


def _is_free_email(value: str) -> bool:
    if "@" not in value:
        return False
    return value.rsplit("@", 1)[-1].lower() in FREE_EMAIL_DOMAINS


def _is_only_contact(supplier) -> bool:
    contacts = list(_value(supplier, "contacts", []) or [])
    return len(contacts) <= 1


def _contains_fraud_evasion(text: str) -> bool:
    safe_disclaimers = [
        "do not request or accept false declarations",
        "cannot proceed with any workaround",
        "cannot proceed with any workaround of applicable rules",
        "we do not request or accept",
    ]
    normalized = text
    for phrase in safe_disclaimers:
        normalized = normalized.replace(phrase, "")
    return any(term in normalized for term in FRAUD_TERMS)


def _reason_category(reason: str) -> str:
    if "contact missing source_url" in reason or "contact missing evidence_text" in reason:
        return "missing_contact_evidence"
    if "unknown or regulated substance" in reason:
        return "unknown_substance_review"
    if "substance has regulatory flags" in reason:
        return "regulatory_review"
    if "high risk supplier" in reason:
        return "high_risk_manual_review"
    if "marketplace internal messenger" in reason:
        return "marketplace_manual_review"
    if "free email" in reason:
        return "free_email_review"
    if "default outbound safety posture" in reason:
        return "default_approval"
    return "hard_block"
