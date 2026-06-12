def _seed_profile(client) -> tuple[str, str]:
    substance_response = client.post("/substances", json={"cas": "64-17-5"})
    assert substance_response.status_code == 201
    substance_id = substance_response.json()["id"]
    assert client.post(f"/substances/{substance_id}/enrich").status_code == 200

    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Profile Supplier Ltd",
            "website": "https://profile-supplier.example",
            "country": "DE",
            "address": "Industrial Park 1",
            "registration_number": "DE-123",
            "verified_status": "audited",
            "notes": "manufacturer SDS COA MOQ lead time Incoterms packaging",
            "contacts": [
                {
                    "channel": "email",
                    "value": "sales@profile-supplier.example",
                    "source_url": "https://profile-supplier.example/contact",
                    "evidence_text": "Official sales email published on company contact page.",
                    "is_primary": True,
                }
            ],
        },
    )
    assert supplier_response.status_code == 201
    supplier = supplier_response.json()

    campaign_response = client.post(
        "/campaigns",
        json={
            "substance_id": substance_id,
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "requirements": {"documents": ["COA", "SDS"], "packaging": "UN drums"},
            "auto_send_enabled": True,
        },
    )
    assert campaign_response.status_code == 201
    campaign_id = campaign_response.json()["id"]

    rfq_response = client.post(
        f"/campaigns/{campaign_id}/generate-rfq",
        json={"supplier_id": supplier["id"], "contact_id": supplier["contacts"][0]["id"]},
    )
    assert rfq_response.status_code == 200

    inbound_response = client.post(
        "/messages/inbound",
        json={
            "company_id": supplier["id"],
            "campaign_id": campaign_id,
            "channel": "email",
            "from_address": "sales@profile-supplier.example",
            "subject": "Re: Ethanol RFQ",
            "body": (
                "CAS 64-17-5 confirmed. Price: USD 12.50/kg CIF. MOQ: 25 kg. "
                "Lead time: 14 days. Packaging: 160 kg UN steel drums. "
                "COA and SDS available. Payment: TT."
            ),
        },
    )
    assert inbound_response.status_code == 201
    assert client.post(f"/messages/inbound/{inbound_response.json()['id']}/parse").status_code == 200
    return substance_id, campaign_id


def test_substance_intelligence_profile_collects_supplier_history_and_terms(client) -> None:
    substance_id, _campaign_id = _seed_profile(client)

    response = client.get(f"/substances/{substance_id}/intelligence")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["supplier_count"] == 1
    assert payload["summary"]["quote_count"] == 1
    assert payload["summary"]["best_price"] == "12.5000000000" or payload["summary"]["best_price"] == "12.5"
    supplier = payload["suppliers"][0]
    assert supplier["contacts"][0]["source_url"]
    assert supplier["contact_history"]
    assert supplier["quotes"][0]["incoterms"] == "CIF"
    assert "sea" in supplier["quotes"][0]["transport_mode"]
    assert supplier["quoted_packaging"]
    assert any(item["transport_mode"] == "sea" for item in payload["incoterms_by_transport"])


def test_manufacturing_analysis_saves_cost_model_and_raw_material_tasks(client) -> None:
    substance_id, _campaign_id = _seed_profile(client)

    response = client.post(
        f"/substances/{substance_id}/manufacturing-analysis",
        json={
            "target_quantity": "1000 kg/month",
            "target_grade": "technical",
            "intended_use": "lawful industrial solvent validation",
            "destination_country": "PL",
            "include_raw_material_sourcing": True,
            "create_raw_material_tasks": True,
            "save_to_crm": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"]
    assert payload["status"] == "draft_feasibility"
    assert payload["required_equipment"]
    assert payload["input_materials"]
    assert payload["sourcing_queries"]
    assert payload["cost_model"]["method"] == "screening_only"
    assert any("No synthesis recipe" in note for note in payload["safety_notes"])

    list_response = client.get(f"/substances/{substance_id}/manufacturing-analyses")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    tasks_response = client.get("/manual-tasks")
    assert tasks_response.status_code == 200
    assert any(task["task_type"] == "raw_material_sourcing_review" for task in tasks_response.json())


def test_manufacturing_analysis_requires_review_for_unknown_substance(client) -> None:
    substance_response = client.post("/substances", json={"cas": "50-00-0"})
    assert substance_response.status_code == 201
    substance_id = substance_response.json()["id"]

    response = client.post(
        f"/substances/{substance_id}/manufacturing-analysis",
        json={"target_quantity": "10 kg", "save_to_crm": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "manual_review_required"
    assert payload["blocked_reasons"]
    assert payload["input_materials"] == []
