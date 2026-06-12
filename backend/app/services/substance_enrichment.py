from dataclasses import dataclass, field
from decimal import Decimal
from typing import Protocol

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.cas_validator import validate_cas_or_raise


@dataclass(frozen=True)
class SubstanceEnrichmentResult:
    cas: str
    primary_name: str | None = None
    iupac_name: str | None = None
    molecular_formula: str | None = None
    molecular_weight: float | None = None
    pubchem_cid: str | None = None
    synonyms: list[str] = field(default_factory=list)
    ec_number: str | None = None
    data_sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_manual_review: bool = False
    warnings: list[str] = field(default_factory=list)


class SubstanceDataProvider(Protocol):
    def enrich_by_cas(self, cas: str) -> SubstanceEnrichmentResult:
        ...


class MockSubstanceProvider:
    fixtures = {
        "64-17-5": SubstanceEnrichmentResult(
            cas="64-17-5",
            primary_name="Ethanol",
            iupac_name="ethanol",
            molecular_formula="C2H6O",
            molecular_weight=46.07,
            pubchem_cid="702",
            synonyms=["ethyl alcohol", "alcohol"],
            ec_number="200-578-6",
            data_sources=["mock"],
            confidence=0.95,
            requires_manual_review=False,
        ),
        "7732-18-5": SubstanceEnrichmentResult(
            cas="7732-18-5",
            primary_name="Water",
            iupac_name="oxidane",
            molecular_formula="H2O",
            molecular_weight=18.015,
            pubchem_cid="962",
            synonyms=["distilled water", "purified water"],
            ec_number="231-791-2",
            data_sources=["mock"],
            confidence=0.95,
            requires_manual_review=False,
        ),
    }

    def enrich_by_cas(self, cas: str) -> SubstanceEnrichmentResult:
        normalized = validate_cas_or_raise(cas)
        return self.fixtures.get(
            normalized,
            SubstanceEnrichmentResult(
                cas=normalized,
                data_sources=["mock"],
                confidence=0.0,
                requires_manual_review=True,
                warnings=["No mock enrichment data found; manual review required."],
            ),
        )


class PubChemPugRestProvider:
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

    def __init__(self, timeout_seconds: int = 15) -> None:
        self.timeout_seconds = timeout_seconds

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def _get_json(self, path: str) -> dict:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()

    def enrich_by_cas(self, cas: str) -> SubstanceEnrichmentResult:
        normalized = validate_cas_or_raise(cas)
        try:
            cid_payload = self._get_json(f"/compound/name/{normalized}/cids/JSON")
            cid = str(cid_payload["IdentifierList"]["CID"][0])
            property_payload = self._get_json(
                f"/compound/cid/{cid}/property/IUPACName,MolecularFormula,MolecularWeight,Title/JSON"
            )
            properties = property_payload["PropertyTable"]["Properties"][0]
            synonym_payload = self._get_json(f"/compound/cid/{cid}/synonyms/JSON")
            synonyms = synonym_payload.get("InformationList", {}).get("Information", [{}])[0].get(
                "Synonym", []
            )
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            return SubstanceEnrichmentResult(
                cas=normalized,
                data_sources=["pubchem"],
                confidence=0.0,
                requires_manual_review=True,
                warnings=[f"PubChem enrichment failed or returned no usable data: {type(exc).__name__}"],
            )

        ec_number = next((item for item in synonyms if _looks_like_ec_number(item)), None)
        return SubstanceEnrichmentResult(
            cas=normalized,
            primary_name=properties.get("Title"),
            iupac_name=properties.get("IUPACName"),
            molecular_formula=properties.get("MolecularFormula"),
            molecular_weight=float(properties["MolecularWeight"])
            if properties.get("MolecularWeight") is not None
            else None,
            pubchem_cid=cid,
            synonyms=list(dict.fromkeys(synonyms[:30])),
            ec_number=ec_number,
            data_sources=["pubchem"],
            confidence=0.9,
            requires_manual_review=False,
        )


class SubstanceEnrichmentService:
    def __init__(self, provider: SubstanceDataProvider | None = None) -> None:
        self.provider = provider or MockSubstanceProvider()

    def enrich_by_cas(self, cas: str) -> SubstanceEnrichmentResult:
        return self.provider.enrich_by_cas(cas)


def decimal_or_none(value: float | None) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def _looks_like_ec_number(value: str) -> bool:
    parts = value.split("-")
    return len(parts) == 3 and len(parts[0]) == 3 and len(parts[1]) == 3 and len(parts[2]) == 1
