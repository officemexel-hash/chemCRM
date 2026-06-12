from dataclasses import dataclass, field
from enum import StrEnum


class SupplierType(StrEnum):
    MANUFACTURER = "MANUFACTURER"
    AUTHORIZED_DISTRIBUTOR = "AUTHORIZED_DISTRIBUTOR"
    TRADER_BROKER = "TRADER_BROKER"
    MARKETPLACE_STORE = "MARKETPLACE_STORE"
    LAB_SUPPLIER = "LAB_SUPPLIER"
    EXPORT_AGENT = "EXPORT_AGENT"
    UNKNOWN = "UNKNOWN"
    HIGH_RISK = "HIGH_RISK"


FREE_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "hotmail.com",
    "outlook.com",
    "proton.me",
    "protonmail.com",
    "qq.com",
    "163.com",
}

FRAUD_TERMS = {
    "misdeclare",
    "fake invoice",
    "false declaration",
    "avoid customs",
    "no sds",
    "no invoice",
    "bypass",
}


@dataclass(frozen=True)
class SupplierClassification:
    company_type: str
    supplier_score: int
    risk_score: int
    risk_level: str
    risk_flags: list[str] = field(default_factory=list)
    confidence: float = 0.5


class SupplierClassifier:
    def classify(self, supplier, contacts: list | None = None, evidence: dict | None = None) -> SupplierClassification:
        evidence = evidence or {}
        contacts = contacts if contacts is not None else list(getattr(supplier, "contacts", []) or [])
        text = " ".join(
            str(value or "")
            for value in [
                getattr(supplier, "name", ""),
                getattr(supplier, "website", ""),
                getattr(supplier, "notes", ""),
                evidence.get("page_text", ""),
            ]
        ).lower()

        supplier_score = 0
        risk_score = 0
        risk_flags: list[str] = []

        company_type = self._infer_type(text)
        if company_type == SupplierType.MANUFACTURER:
            supplier_score += 30
        if getattr(supplier, "website", None):
            supplier_score += 10
        if "audited" in text or "verified supplier" in text or getattr(supplier, "verified_status", None):
            supplier_score += 20
        if getattr(supplier, "address", None) or getattr(supplier, "registration_number", None):
            supplier_score += 20
        if any(_contact_channel(contact) == "phone" for contact in contacts):
            supplier_score += 5
        if "sds" in text or "coa" in text or "specification" in text:
            supplier_score += 15
        if "moq" in text or "lead time" in text or "incoterms" in text:
            supplier_score += 15
        if any(_is_business_email(_contact_value(contact)) for contact in contacts if _contact_channel(contact) == "email"):
            supplier_score += 10

        email_contacts = [contact for contact in contacts if _contact_channel(contact) == "email"]
        if email_contacts and all(not _is_business_email(_contact_value(contact)) for contact in email_contacts):
            risk_score += 20
            risk_flags.append("free_email_only")
        if not getattr(supplier, "address", None) and not getattr(supplier, "registration_number", None):
            risk_score += 30
            risk_flags.append("missing_company_registration_or_address")
        if _messenger_only(contacts):
            risk_score += 40
            risk_flags.append("messenger_only_no_documents")
        if "refuse sds" in text or "no coa" in text or "no invoice" in text:
            risk_score += 50
            risk_flags.append("refuses_documents")
        if any(term in text for term in FRAUD_TERMS):
            risk_score += 80
            risk_flags.append("fraud_or_evasion_language")
        if supplier_score < 20 and risk_score >= 40:
            company_type = SupplierType.HIGH_RISK

        risk_level = "low"
        if risk_score >= 80:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "elevated"
        elif supplier_score < 20:
            risk_level = "unknown"

        confidence = min(0.95, max(0.35, 0.35 + supplier_score / 120 - risk_score / 250))
        return SupplierClassification(
            company_type=str(company_type),
            supplier_score=max(0, supplier_score),
            risk_score=max(0, risk_score),
            risk_level=risk_level,
            risk_flags=risk_flags,
            confidence=round(confidence, 2),
        )

    def _infer_type(self, text: str) -> SupplierType:
        if "authorized distributor" in text or "official distributor" in text:
            return SupplierType.AUTHORIZED_DISTRIBUTOR
        if "manufacturer" in text or "factory" in text or "plant" in text:
            return SupplierType.MANUFACTURER
        if "laboratory" in text or "lab supplier" in text or "reagent" in text:
            return SupplierType.LAB_SUPPLIER
        if "marketplace" in text or "store" in text:
            return SupplierType.MARKETPLACE_STORE
        if "export agent" in text:
            return SupplierType.EXPORT_AGENT
        if "trader" in text or "broker" in text or "trading" in text:
            return SupplierType.TRADER_BROKER
        return SupplierType.UNKNOWN


def _contact_channel(contact) -> str:
    return str(getattr(contact, "channel", "") if not isinstance(contact, dict) else contact.get("channel", "")).lower()


def _contact_value(contact) -> str:
    return str(getattr(contact, "value", "") if not isinstance(contact, dict) else contact.get("value", "")).lower()


def _is_business_email(value: str) -> bool:
    if "@" not in value:
        return False
    domain = value.rsplit("@", 1)[-1].lower()
    return domain not in FREE_EMAIL_DOMAINS and "." in domain


def _messenger_only(contacts: list) -> bool:
    if not contacts:
        return False
    messenger_channels = {"whatsapp", "telegram", "wechat", "threema", "signal", "wickr"}
    return all(_contact_channel(contact) in messenger_channels for contact in contacts)
