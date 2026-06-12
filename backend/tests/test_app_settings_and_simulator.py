from types import SimpleNamespace

from app.schemas.app_settings import AppSettings, CompanyProfile, ControlledQuestion, SenderProfile
from app.services.rfq_generator import RFQGenerator


def test_settings_api_saves_company_sender_and_questions(client) -> None:
    payload = {
        "company": {
            "legal_name": "Example Procurement Sp. z o.o.",
            "trading_name": "Example Procurement",
            "website": "https://example.test",
            "country": "PL",
        },
        "sender": {
            "name": "Anna Kowalska",
            "title": "Senior Procurement Manager",
            "email": "anna@procurement-crm.com",
            "signature": "Anna Kowalska\nSenior Procurement Manager\nExample Procurement",
        },
        "default_destination_country": "Poland",
        "default_intended_use": "lawful industrial validation",
        "controlled_questions": [
            {
                "key": "documents",
                "text": "Confirm COA and SDS availability.",
                "required": True,
                "category": "documents",
            }
        ],
        "response_playbook": [],
        "training_scenarios": [],
        "require_human_approval_for_simulated_responses": True,
    }

    response = client.put("/settings/app", json=payload)

    assert response.status_code == 200
    saved = response.json()
    assert saved["company"]["legal_name"] == "Example Procurement Sp. z o.o."
    assert saved["sender"]["name"] == "Anna Kowalska"
    assert saved["controlled_questions"][0]["key"] == "documents"


def test_rfq_generator_uses_company_sender_and_controlled_questions() -> None:
    settings = AppSettings(
        company=CompanyProfile(legal_name="Example Procurement Sp. z o.o.", trading_name="Example Procurement"),
        sender=SenderProfile(
            name="Anna Kowalska",
            title="Senior Procurement Manager",
            email="anna@procurement-crm.com",
        ),
        controlled_questions=[
            ControlledQuestion(
                key="documents",
                category="documents",
                text="Confirm COA and SDS availability.",
                required=True,
            )
        ],
    )

    draft = RFQGenerator(settings).generate(
        SimpleNamespace(cas="64-17-5", primary_name="Ethanol"),
        SimpleNamespace(
            quantity="100 kg",
            required_grade="technical grade",
            destination_country="Poland",
            intended_use="lawful industrial validation",
        ),
        SimpleNamespace(name="Acme Chemicals"),
    )

    assert "on behalf of Example Procurement" in draft.body
    assert "Confirm COA and SDS availability." in draft.body
    assert "Anna Kowalska" in draft.body
    assert "anna@procurement-crm.com" in draft.body


def test_conversation_simulator_blocks_fraud_evasion(client) -> None:
    response = client.post(
        "/conversation-simulator/simulate",
        json={
            "supplier_name": "Risky Supplier",
            "supplier_message": "We can ship as gift with no invoice to avoid customs.",
            "channel": "marketplace_internal",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["recommended_action"] == "block"
    assert result["block"] is True
    assert result["red_flags"]


def test_conversation_simulator_identifies_missing_controlled_questions(client) -> None:
    response = client.post(
        "/conversation-simulator/simulate",
        json={
            "supplier_name": "Acme Supplier",
            "supplier_message": "Price is USD 12/kg and MOQ is 25 kg.",
            "channel": "manual",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["recommended_action"] == "request_missing_information"
    assert "documents" in result["missing_controlled_questions"]
    assert result["approval_required"] is True
