import re
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ExtractedPrice(BaseModel):
    quantity: str | None = None
    price: float | None = None
    currency: str | None = None
    unit: str | None = "kg"
    incoterms: str | None = None


class ExtractedQuote(BaseModel):
    supplier_type: str | None = "unknown"
    substance_confirmed: bool | None = None
    cas_confirmed: str | None = None
    grade: str | None = None
    purity: str | None = None
    moq: str | None = None
    prices: list[ExtractedPrice] = Field(default_factory=list)
    lead_time: str | None = None
    payment_terms: str | None = None
    sample_available: bool | None = None
    sample_price: str | None = None
    packaging: str | None = None
    coa_available: bool | None = None
    sds_available: bool | None = None
    reach_status: str | None = None
    adr_class: str | None = None
    un_number: str | None = None
    hs_code: str | None = None
    shelf_life: str | None = None
    certificates: list[str] = Field(default_factory=list)
    production_capacity: str | None = None
    red_flags: list[str] = Field(default_factory=list)
    missing_questions: list[str] = Field(default_factory=list)
    recommended_next_action: str | None = "manual_review"
    confidence: float = 0.0

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, value: float) -> float:
        return min(1.0, max(0.0, value))


class QuoteExtractor:
    price_pattern = re.compile(
        r"(?:(USD|EUR|GBP|CNY|RMB)\s*)?(\d+(?:[.,]\d+)?)\s*(?:/|\s+per\s+)?(kg|g|mt|ton|lb)?",
        re.IGNORECASE,
    )

    def extract(self, body: str, attachment_text: str | None = None, **_) -> ExtractedQuote:
        text = "\n".join([body or "", attachment_text or ""])
        lowered = text.lower()
        prices = self._extract_prices(text)
        missing = []
        for field_name, token in [
            ("COA", "coa"),
            ("SDS", "sds"),
            ("MOQ", "moq"),
            ("lead time", "lead time"),
            ("Incoterms", "exw"),
        ]:
            if token not in lowered:
                missing.append(field_name)
        red_flags = [
            term
            for term in ["no invoice", "misdeclare", "false declaration", "no sds", "bypass"]
            if term in lowered
        ]
        confidence = 0.25 + (0.2 if prices else 0) + (0.15 if "coa" in lowered else 0)
        confidence += 0.15 if "sds" in lowered else 0
        confidence += 0.1 if "lead time" in lowered else 0
        confidence -= 0.2 if red_flags else 0

        return ExtractedQuote(
            supplier_type=_match_supplier_type(lowered),
            substance_confirmed="cas" in lowered or bool(re.search(r"\d{2,7}-\d{2}-\d", text)),
            cas_confirmed=_first_match(r"\d{2,7}-\d{2}-\d", text),
            grade=_first_match(r"(technical|reagent|usp|food|pharma)\s+grade", text, flags=re.I),
            purity=_first_match(r"(\d{2,3}(?:[.,]\d+)?\s*%)", text),
            moq=_line_value(text, "moq"),
            prices=prices,
            lead_time=_line_value(text, "lead time"),
            payment_terms=_line_value(text, "payment"),
            sample_available=True if "sample available" in lowered else None,
            sample_price=_line_value(text, "sample price"),
            packaging=_line_value(text, "packaging"),
            coa_available=True if "coa" in lowered else None,
            sds_available=True if "sds" in lowered or "msds" in lowered else None,
            reach_status=_line_value(text, "reach"),
            adr_class=_line_value(text, "adr"),
            un_number=_first_match(r"\bUN\s?(\d{4})\b", text, flags=re.I),
            hs_code=_line_value(text, "hs code"),
            shelf_life=_line_value(text, "shelf life"),
            certificates=_extract_certificates(lowered),
            production_capacity=_line_value(text, "capacity"),
            red_flags=red_flags,
            missing_questions=missing,
            recommended_next_action="send_follow_up" if missing else "review_quote",
            confidence=round(confidence, 2),
        )

    def _extract_prices(self, text: str) -> list[ExtractedPrice]:
        prices: list[ExtractedPrice] = []
        for match in self.price_pattern.finditer(text):
            if _inside_cas_number(text, match.start(), match.end()):
                continue
            currency, amount, unit = match.groups()
            if not currency and not re.search(r"\b(price|usd|eur|kg)\b", text[max(0, match.start() - 20) : match.end() + 20], re.I):
                continue
            try:
                price = float(amount.replace(",", "."))
            except ValueError:
                continue
            prices.append(
                ExtractedPrice(
                    quantity=_nearby_quantity(text, match.start()),
                    price=price,
                    currency=(currency or _first_match(r"\b(USD|EUR|GBP|CNY|RMB)\b", text, re.I)),
                    unit=(unit or "kg").lower(),
                    incoterms=_first_match(r"\b(EXW|FOB|CIF|DAP|DDP)\b", text, re.I),
                )
            )
        return prices[:5]


def _first_match(pattern: str, text: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    if not match:
        return None
    return match.group(1) if match.groups() else match.group(0)


def _line_value(text: str, label: str) -> str | None:
    pattern = re.compile(rf"{re.escape(label)}\s*[:\-]\s*(.+)", re.IGNORECASE)
    match = pattern.search(text)
    return match.group(1).strip()[:200] if match else None


def _nearby_quantity(text: str, index: int) -> str | None:
    window = text[max(0, index - 80) : index + 80]
    return _first_match(r"(\d+(?:[.,]\d+)?\s*(?:kg|g|mt|ton|lb))", window, re.I)


def _match_supplier_type(text: str) -> str:
    for supplier_type in ["manufacturer", "authorized distributor", "trading company", "broker"]:
        if supplier_type in text:
            return supplier_type
    return "unknown"


def _extract_certificates(text: str) -> list[str]:
    return [cert.upper() for cert in ["iso", "gmp", "halal", "kosher"] if cert in text]


def _inside_cas_number(text: str, start: int, end: int) -> bool:
    left = max(0, start - 8)
    right = min(len(text), end + 8)
    window = text[left:right]
    for match in re.finditer(r"\d{2,7}-\d{2}-\d", window):
        absolute_start = left + match.start()
        absolute_end = left + match.end()
        if absolute_start <= start < absolute_end:
            return True
    return False
