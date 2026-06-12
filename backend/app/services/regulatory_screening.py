from dataclasses import dataclass, field


RISK_TERMS = {
    "restricted": "high",
    "controlled": "high",
    "precursor": "high",
    "explosive": "critical",
    "toxic gas": "high",
    "scheduled": "critical",
    "weapon": "critical",
}


@dataclass(frozen=True)
class RegulatoryScreeningResult:
    regulatory_status: str
    requires_manual_review: bool
    flags: list[dict] = field(default_factory=list)


class RegulatoryScreeningService:
    def screen(
        self,
        cas: str,
        primary_name: str | None = None,
        synonyms: list[str] | None = None,
        known_status: str | None = None,
    ) -> RegulatoryScreeningResult:
        if not primary_name and not synonyms:
            return RegulatoryScreeningResult(
                regulatory_status="unknown",
                requires_manual_review=True,
                flags=[
                    {
                        "flag_type": "unknown_substance",
                        "severity": "medium",
                        "source": "local_screening",
                        "description": "No enrichment data available; manual regulatory review required.",
                    }
                ],
            )

        text = " ".join([primary_name or "", *(synonyms or [])]).lower()
        flags: list[dict] = []
        for term, severity in RISK_TERMS.items():
            if term in text:
                flags.append(
                    {
                        "flag_type": "risk_keyword",
                        "severity": severity,
                        "source": "local_screening",
                        "description": f"Risk keyword matched: {term}. This is not a legal determination.",
                    }
                )

        status_value = (known_status or "unreviewed").lower()
        requires_review = bool(flags) or status_value in {"unknown", "regulated", "restricted"}
        if any(flag["severity"] == "critical" for flag in flags):
            status_value = "restricted"
        return RegulatoryScreeningResult(status_value, requires_review, flags)
