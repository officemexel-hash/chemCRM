def _create_substance(client, cas: str = "64-17-5") -> str:
    response = client.post("/substances", json={"cas": cas, "primary_name": "Demo Product"})
    assert response.status_code == 201
    return response.json()["id"]


def _create_supplier(client, channel: str = "email", value: str = "sales@acme.example") -> tuple[str, str]:
    response = client.post(
        "/suppliers",
        json={
            "name": "Acme Chemical Manufacturer",
            "website": "https://acme.example",
            "country": "PL",
            "address": "1 Industrial Road",
            "registration_number": "REG123",
            "risk_level": "low",
            "risk_score": 0,
            "notes": "manufacturer SDS COA MOQ lead time Incoterms",
            "contacts": [
                {
                    "channel": channel,
                    "value": value,
                    "source_url": value if value.startswith("https://") else "https://acme.example/contact",
                    "evidence_text": "Official public business contact for supplier inquiries.",
                    "is_primary": True,
                }
            ],
        },
    )
    assert response.status_code == 201
    supplier = response.json()
    return supplier["id"], supplier["contacts"][0]["id"]


def _create_campaign(client, substance_id: str, auto_send_enabled: bool = True) -> str:
    response = client.post(
        "/campaigns",
        json={
            "substance_id": substance_id,
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "requirements": {"documents": ["COA", "SDS"]},
            "auto_send_enabled": auto_send_enabled,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_autonomous_campaign_sends_low_risk_business_email(client) -> None:
    substance_id = _create_substance(client)
    supplier_id, _ = _create_supplier(client)
    campaign_id = _create_campaign(client, substance_id)

    response = client.post(
        f"/campaigns/{campaign_id}/run-autonomous",
        json={"supplier_ids": [supplier_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated"] == 1
    assert payload["sent"] == 1
    assert payload["items"][0]["policy_decision"] == "ALLOW_AUTO_SEND"
    assert payload["items"][0]["status"] == "sent"


def test_autonomous_campaign_creates_manual_task_for_alibaba_internal(client) -> None:
    substance_id = _create_substance(client)
    supplier_id, _ = _create_supplier(
        client,
        channel="alibaba_internal",
        value="https://supplier.en.alibaba.com",
    )
    campaign_id = _create_campaign(client, substance_id)

    response = client.post(
        f"/campaigns/{campaign_id}/run-autonomous",
        json={"supplier_ids": [supplier_id]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generated"] == 1
    assert payload["sent"] == 0
    assert payload["requires_approval"] == 1
    assert payload["items"][0]["policy_decision"] == "REQUIRES_APPROVAL"
    assert "create_marketplace_manual_task" in payload["items"][0]["actions"]

    tasks_response = client.get("/manual-tasks")
    assert tasks_response.status_code == 200
    assert any(task["task_type"] == "approval_needed" for task in tasks_response.json())
