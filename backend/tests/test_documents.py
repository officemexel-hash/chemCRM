def test_letterhead_uses_company_settings(client) -> None:
    settings = {
        "company": {
            "legal_name": "Example Procurement Sp. z o.o.",
            "website": "https://example.com",
            "country": "PL",
            "address": "Warsaw, Poland",
            "eori_number": "PL1234567890",
        },
        "sender": {
            "name": "Anna Kowalska",
            "email": "anna@example.com",
            "phone": "+48 100 100 100",
        },
        "default_incoterms": ["EXW", "FCA", "DAP"],
        "controlled_questions": [],
        "response_playbook": [],
        "training_scenarios": [],
        "require_human_approval_for_simulated_responses": True,
    }
    assert client.put("/settings/app", json=settings).status_code == 200

    response = client.post("/documents/letterhead", json={"title": "Procurement Letter"})

    assert response.status_code == 200
    payload = response.json()
    assert "Example Procurement" in payload["html"]
    assert "EORI" in payload["html"]
    assert "Procurement Letter" in payload["text"]


def test_generate_loi_and_save_to_crm(client) -> None:
    response = client.post(
        "/documents/letter-of-intent",
        json={
            "recipient_name": "Sales Team",
            "recipient_company": "Supplier Ltd",
            "substance_name": "Ethanol",
            "substance_cas": "64-17-5",
            "quantity": "100 kg",
            "destination_country": "Poland",
            "intended_use": "lawful industrial validation",
            "save_to_crm": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated_document_id"]
    assert "Letter of Intent" in payload["html"]
    assert "non-binding" in payload["html"]

    download = client.get(f"/documents/{payload['generated_document_id']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith(("application/pdf", "text/html"))


def test_generate_po_transport_incoterms_and_customs_fields(client) -> None:
    response = client.post(
        "/documents/purchase-order",
        json={
            "supplier_name": "Supplier Ltd",
            "supplier_address": "Shanghai",
            "substance_name": "Ethanol",
            "substance_cas": "64-17-5",
            "quantity": "100",
            "unit": "kg",
            "price_per_unit": "12.50",
            "currency": "USD",
            "transport_mode": "sea",
            "incoterms": "CIF",
            "hs_code": "2207.10",
            "customs_duty_rate": "Verify in TARIC",
            "legal_use_description": "Industrial solvent for coatings validation.",
            "save_to_crm": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["po_number"].startswith("PO-")
    assert payload["generated_document_id"]
    assert payload["transport_mode"] == "sea"
    assert "CIF" in payload["suggested_incoterms"]
    assert payload["incoterms_responsibility"]["transport"] == "Seller"
    assert "HS code" in payload["html"]
    assert "Industrial solvent" in payload["html"]


def test_customs_duty_returns_reviewable_estimate_and_legal_uses(client) -> None:
    response = client.post(
        "/documents/customs-duty",
        json={
            "cas": "64-17-5",
            "origin_country": "CN",
            "destination_country": "PL",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["hs_code"] == "2207.10"
    assert payload["manual_review_required"] is True
    assert payload["source_url"]
    assert payload["confidence"] < 0.5
    assert any("Industrial solvent" in use for use in payload["legal_uses"])
    assert any("anti-dumping" in note.lower() for note in payload["regulatory_notes"])


def test_substance_analogs_include_similarity_basis(client) -> None:
    response = client.post(
        "/documents/substance-analogs",
        json={
            "cas": "64-17-5",
            "primary_name": "Ethanol",
            "target_application": "industrial solvent",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["analogs"]
    assert payload["analogs"][0]["requires_validation"] is True
    assert payload["analogs"][0]["similarity_basis"]
    assert "Validate" in payload["recommendation"] or "validation" in payload["recommendation"]


def test_supplier_document_rebranding_is_disabled(client) -> None:
    response = client.post(
        "/documents/rebrand-text",
        json={"text": "Supplier COA text", "doc_type": "coa", "substance_name": "Ethanol", "cas": "64-17-5"},
    )

    assert response.status_code == 410
    assert "disabled" in response.json()["detail"].lower()
