import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import new_uuid
from app.db.models.substance import Substance
from app.db.models.tariff import HsCodeEntry, LegalUseDescription, TariffRate

logger = logging.getLogger(__name__)

# Incoterms responsibility matrix: who pays for what
INCOTERMS_MATRIX: dict[str, dict[str, str]] = {
    "EXW": {"export_clearance": "buyer", "freight": "buyer", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "FCA": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "FAS": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "FOB": {"export_clearance": "seller", "freight": "buyer", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "CFR": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "CIF": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "CPT": {"export_clearance": "seller", "freight": "seller", "insurance": "buyer", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "CIP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "buyer"},
    "DAP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "terminal_handling": "buyer", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "seller"},
    "DPU": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "terminal_handling": "seller", "import_duty": "buyer", "customs_clearance": "buyer", "delivery": "seller"},
    "DDP": {"export_clearance": "seller", "freight": "seller", "insurance": "seller", "terminal_handling": "seller", "import_duty": "seller", "customs_clearance": "seller", "delivery": "seller"},
}

# Recommended incoterms by transport type
TRANSPORT_INCOTERMS: dict[str, list[str]] = {
    "sea": ["FOB", "CFR", "CIF", "FAS"],
    "air": ["FCA", "CPT", "CIP"],
    "road": ["EXW", "FCA", "DAP", "DDP"],
    "rail": ["FCA", "CPT", "DAP"],
    "courier": ["DDP", "DAP", "DPU"],
}


class HsCodeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def lookup_by_cas(self, cas: str) -> list[HsCodeEntry]:
        """Look up HS codes by CAS number (checks cas_pattern field)."""
        return list(
            self.db.scalars(
                select(HsCodeEntry)
                .where(HsCodeEntry.cas_pattern == cas)
                .order_by(HsCodeEntry.confidence.desc())
            )
        )

    def lookup_by_name(self, name: str) -> list[HsCodeEntry]:
        """Look up HS codes by description text (case-insensitive partial match)."""
        pattern = f"%{name}%"
        return list(
            self.db.scalars(
                select(HsCodeEntry)
                .where(HsCodeEntry.description.ilike(pattern))
                .order_by(HsCodeEntry.confidence.desc())
                .limit(10)
            )
        )

    def suggest_for_substance(self, substance_id: str) -> list[HsCodeEntry]:
        """Suggest HS codes for a substance combining CAS + name lookups."""
        substance = self.db.get(Substance, substance_id)
        if substance is None:
            return []

        results: list[HsCodeEntry] = []
        seen_ids: set[str] = set()

        # Lookup by CAS
        if substance.cas:
            for entry in self.lookup_by_cas(substance.cas):
                if entry.id not in seen_ids:
                    results.append(entry)
                    seen_ids.add(entry.id)

        # Lookup by name
        for name in [substance.primary_name, substance.iupac_name]:
            if name:
                for entry in self.lookup_by_name(name):
                    if entry.id not in seen_ids:
                        results.append(entry)
                        seen_ids.add(entry.id)

        # Check direct link
        direct = list(
            self.db.scalars(
                select(HsCodeEntry)
                .where(HsCodeEntry.substance_id == substance_id)
                .order_by(HsCodeEntry.confidence.desc())
            )
        )
        for entry in direct:
            if entry.id not in seen_ids:
                results.insert(0, entry)
                seen_ids.add(entry.id)

        return results

    def auto_assign(self, substance_id: str) -> HsCodeEntry | None:
        """Assign the highest-confidence HS code to the substance."""
        suggestions = self.suggest_for_substance(substance_id)
        if not suggestions:
            return None

        best = suggestions[0]
        substance = self.db.get(Substance, substance_id)
        if substance:
            substance.hs_code_suggested = best.hs_code
            substance.hs_code_confidence = best.confidence
            best.substance_id = substance_id
            self.db.commit()
            self.db.refresh(best)
        return best

    def get_incoterms_for_transport(self, transport_type: str) -> list[str]:
        """Get recommended incoterms for a transport type."""
        return TRANSPORT_INCOTERMS.get(transport_type, ["FOB", "CIF", "EXW", "DDP"])


class TariffService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_rate(self, hs_code: str, origin_country: str, destination_country: str) -> TariffRate | None:
        """Get tariff rate for a specific HS code and country pair."""
        hs_entry = self.db.scalar(
            select(HsCodeEntry).where(HsCodeEntry.hs_code == hs_code)
        )
        if hs_entry is None:
            return None
        return self.db.scalar(
            select(TariffRate).where(
                TariffRate.hs_code_id == hs_entry.id,
                TariffRate.origin_country == origin_country.upper(),
                TariffRate.destination_country == destination_country.upper(),
            )
        )

    def get_rates_for_campaign(self, campaign_id: str) -> list[TariffRate]:
        """Get all tariff rates relevant to a campaign."""
        from app.db.models.campaign import RfqCampaign

        campaign = self.db.get(RfqCampaign, campaign_id)
        if campaign is None:
            return []

        substance = self.db.get(Substance, campaign.substance_id)
        if substance is None:
            return []

        hs_code = substance.hs_code_confirmed or substance.hs_code_suggested
        if not hs_code:
            return []

        hs_entry = self.db.scalar(select(HsCodeEntry).where(HsCodeEntry.hs_code == hs_code))
        if hs_entry is None:
            return []

        return list(self.db.scalars(select(TariffRate).where(TariffRate.hs_code_id == hs_entry.id)))

    @staticmethod
    def get_responsibility_matrix(incoterms: str) -> dict[str, str]:
        """Get who pays for what under a given Incoterms rule."""
        return INCOTERMS_MATRIX.get(incoterms.upper(), {})
