from datetime import date

from app.schemas.documents import CustomsDutyRequest, CustomsDutyResponse


OFFICIAL_TARIC_URL = "https://ec.europa.eu/taxation_customs/dds2/taric/taric_consultation.jsp"
US_HTS_URL = "https://hts.usitc.gov/"

HS_CODE_DATABASE: dict[str, dict] = {
    "2207.10": {
        "description": "Undenatured ethyl alcohol of an alcoholic strength by volume of 80% vol or higher",
        "duty_rate": "Specific/excise dependent - verify in TARIC/HTS",
        "vat_rate": "Destination VAT applies",
    },
    "2836.20": {
        "description": "Disodium carbonate",
        "duty_rate": "Ad valorem duty may apply - verify in official tariff database",
        "vat_rate": "Destination VAT applies",
    },
    "2853.90": {
        "description": "Other inorganic compounds, liquid air, compressed air, amalgams other than precious-metal amalgams",
        "duty_rate": "Verify in official tariff database",
        "vat_rate": "Destination VAT applies",
    },
    "2905.11": {
        "description": "Methanol",
        "duty_rate": "Ad valorem duty may apply - verify in official tariff database",
        "vat_rate": "Destination VAT applies",
    },
    "2914.11": {
        "description": "Acetone",
        "duty_rate": "Ad valorem duty may apply - verify in official tariff database",
        "vat_rate": "Destination VAT applies",
    },
}

CAS_TO_HS_CODE: dict[str, str] = {
    "64-17-5": "2207.10",
    "67-56-1": "2905.11",
    "67-64-1": "2914.11",
    "497-19-8": "2836.20",
    "7732-18-5": "2853.90",
}

LEGAL_USES: dict[str, list[str]] = {
    "64-17-5": [
        "Industrial solvent for coatings, inks, adhesives, and cleaning processes",
        "Chemical intermediate for ester, ether, and acetate production",
        "Laboratory reagent or analytical standard where permitted",
        "Pharmaceutical/cosmetic excipient only where grade and regulations permit",
        "Fuel or denatured alcohol application only under applicable excise rules",
    ],
    "67-56-1": [
        "Industrial solvent or cleaning agent handled by qualified personnel",
        "Feedstock for formaldehyde, methyl esters, and other chemical synthesis",
        "Laboratory reagent or HPLC solvent where permitted",
    ],
    "67-64-1": [
        "Industrial solvent for paints, coatings, adhesives, and resin processing",
        "Chemical intermediate for downstream synthesis",
        "Laboratory solvent and cleaning agent where permitted",
    ],
    "7732-18-5": [
        "Process water or solvent medium",
        "Cleaning, rinsing, cooling, heating, and steam-generation use",
        "Laboratory reagent water where grade specifications are met",
    ],
}

DEFAULT_LEGAL_USES = [
    "Industrial chemical intermediate for lawful manufacturing processes",
    "Laboratory reagent for research, testing, or quality control by qualified personnel",
    "Raw material for chemical synthesis where permits and safety documentation are in place",
    "Commercial/industrial use subject to SDS, COA, transport classification, and import review",
]


class CustomsService:
    def lookup(self, request: CustomsDutyRequest) -> CustomsDutyResponse:
        hs_code = (request.hs_code or CAS_TO_HS_CODE.get(request.cas, "")).strip()
        hs_info = HS_CODE_DATABASE.get(hs_code, {})
        destination = (request.destination_country or "").upper()
        origin = (request.origin_country or "").upper()
        source_url = OFFICIAL_TARIC_URL if destination in {"PL", "DE", "FR", "NL", "ES", "IT", "EU"} else US_HTS_URL

        notes = [
            "Non-binding estimate for procurement screening only.",
            "Confirm HS/CN/TARIC classification, product grade, purity, origin, and end-use with a customs broker.",
            "Check anti-dumping, countervailing, excise, sanctions, dual-use, REACH/CLP, ADR/DG, and import-permit requirements before shipment.",
        ]
        if origin in {"CN", "IN"}:
            notes.append("Origin country may require anti-dumping/countervailing duty review for selected chemical categories.")
        if not hs_code:
            notes.append("No HS code was confirmed; duty cannot be estimated without classification.")

        assumptions = [
            "Duty depends on confirmed HS/CN/TARIC code and destination country.",
            "VAT and excise are not included unless explicitly confirmed by official source.",
            "Preferential origin requires valid proof of origin and applicable trade agreement.",
        ]

        return CustomsDutyResponse(
            hs_code=hs_code or "unknown",
            hs_code_description=hs_info.get("description", "Chemical product - HS code must be confirmed"),
            duty_rate=hs_info.get("duty_rate", "Unknown - verify in official tariff database"),
            vat_rate=hs_info.get("vat_rate", "Destination VAT applies"),
            additional_taxes=[
                "Possible VAT, excise, anti-dumping, countervailing, inspection, and customs clearance fees",
            ],
            legal_uses=LEGAL_USES.get(request.cas, DEFAULT_LEGAL_USES),
            regulatory_notes=notes,
            source="mock screening with official-source handoff",
            source_url=source_url,
            effective_date=date.today().isoformat(),
            confidence=0.35 if hs_code else 0.1,
            manual_review_required=True,
            assumptions=assumptions,
        )
