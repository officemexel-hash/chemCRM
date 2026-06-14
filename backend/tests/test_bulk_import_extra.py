"""Additional tests for services that don't need DB."""
import pytest
from unittest.mock import MagicMock, patch

from app.services.cas_validator import is_valid_cas, validate_cas_or_raise
from app.services.audit_log import AuditLogService
from app.services.search_query_generator import generate_search_queries
from app.services.substance_enrichment import MockSubstanceProvider, PubChemPugRestProvider


class TestCasValidatorExtra:
    def test_valid_cas_with_dashes(self):
        assert is_valid_cas("64-17-5")

    def test_valid_cas_without_dashes(self):
        assert is_valid_cas("64175")

    def test_valid_cas_single_digit_first(self):
        assert is_valid_cas("50-00-0")

    def test_invalid_checksum(self):
        assert not is_valid_cas("64-17-4")

    def test_empty_string(self):
        assert not is_valid_cas("")

    def test_non_numeric(self):
        assert not is_valid_cas("abc-def-ghi")


class TestMockSubstanceProvider:
    def test_ethanol_enrichment(self):
        provider = MockSubstanceProvider()
        result = provider.enrich_by_cas("64-17-5")
        assert result.cas == "64-17-5"
        assert result.primary_name == "Ethanol"
        assert result.pubchem_cid == "702"
        assert result.molecular_formula == "C2H6O"
        assert "mock" in result.data_sources

    def test_water_enrichment(self):
        provider = MockSubstanceProvider()
        result = provider.enrich_by_cas("7732-18-5")
        assert result.cas == "7732-18-5"
        assert result.primary_name == "Water"

    def test_unknown_cas(self):
        provider = MockSubstanceProvider()
        result = provider.enrich_by_cas("50-00-0")
        assert result.requires_manual_review
        assert result.confidence == 0.0


class TestPubChemProvider:
    def test_provider_instantiates(self):
        provider = PubChemPugRestProvider()
        assert provider.base_url == "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class TestSearchQueryGenerator:
    def test_generates_queries(self):
        queries = generate_search_queries("64-17-5", "Ethanol", ["ethyl alcohol"])
        assert len(queries) > 0
        assert any("64-17-5" in q.query for q in queries)

    def test_generates_supplier_queries(self):
        queries = generate_search_queries("50-00-0", "Formaldehyde", [])
        assert len(queries) > 0
        assert any("supplier" in q.query.lower() for q in queries)

    def test_generates_with_synonyms(self):
        queries = generate_search_queries("64-17-5", "Ethanol", ["ethyl alcohol", "ethanol absolute"])
        assert any("ethyl alcohol" in q.query for q in queries)
