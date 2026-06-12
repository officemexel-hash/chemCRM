from types import SimpleNamespace

from app.services.supplier_classifier import SupplierClassifier


def test_supplier_classifier_scores_good_manufacturer() -> None:
    supplier = SimpleNamespace(
        name="Acme Chemical Manufacturer",
        website="https://acme.example",
        notes="manufacturer SDS COA MOQ lead time Incoterms",
        address="1 Industrial Road",
        registration_number="REG123",
        verified_status="audited",
        contacts=[
            SimpleNamespace(channel="email", value="sales@acme.example"),
            SimpleNamespace(channel="phone", value="+48 123 456 789"),
        ],
    )
    result = SupplierClassifier().classify(supplier)
    assert result.company_type == "MANUFACTURER"
    assert result.supplier_score >= 90
    assert result.risk_level == "low"


def test_supplier_classifier_flags_fraud_language() -> None:
    supplier = SimpleNamespace(
        name="Unknown Trading",
        website=None,
        notes="We can misdeclare shipment and no invoice.",
        address=None,
        registration_number=None,
        verified_status=None,
        contacts=[SimpleNamespace(channel="telegram", value="@unknown")],
    )
    result = SupplierClassifier().classify(supplier)
    assert result.risk_score >= 80
    assert "fraud_or_evasion_language" in result.risk_flags
    assert result.risk_level == "high"
