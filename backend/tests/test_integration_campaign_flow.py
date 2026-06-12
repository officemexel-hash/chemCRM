def test_integration_campaign_flow(client) -> None:
    substance_response = client.post("/substances", json={"cas": "64-17-5"})
    assert substance_response.status_code == 201
    substance_id = substance_response.json()["id"]

    enrich_response = client.post(f"/substances/{substance_id}/enrich")
    assert enrich_response.status_code == 200
    assert enrich_response.json()["primary_name"] == "Ethanol"

    supplier_response = client.post(
        "/suppliers",
        json={
            "name": "Acme Chemical Manufacturer",
            "website": "https://acme.example",
            "country": "PL",
            "address": "1 Industrial Road",
            "registration_number": "REG123",
            "verified_status": "audited",
            "notes": "manufacturer SDS COA MOQ lead time Incoterms",
            "contacts": [
                {
                    "channel": "email",
                    "value": "sales@acme.example",
                    "source_url": "https://acme.example/contact",
                    "evidence_text": "Official business inquiry email sales@acme.example.",
                    "is_primary": True,
                }
            ],
        },
    )
    assert supplier_response.status_code == 201
    supplier = supplier_response.json()
    supplier_id = supplier["id"]
    contact_id = supplier["contacts"][0]["id"]

    classify_response = client.post(f"/suppliers/{supplier_id}/classify")
    assert classify_response.status_code == 200
    assert classify_response.json()["supplier_score"] > 0

    campaign_response = client.post(
        "/campaigns",
        json={
            "substance_id": substance_id,
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "requirements": {"documents": ["COA", "SDS"]},
            "auto_send_enabled": True,
        },
    )
    assert campaign_response.status_code == 201
    campaign_id = campaign_response.json()["id"]

    rfq_response = client.post(
        f"/campaigns/{campaign_id}/generate-rfq",
        json={"supplier_id": supplier_id, "contact_id": contact_id},
    )
    assert rfq_response.status_code == 200
    outbound = rfq_response.json()
    assert outbound["policy_decision"] in {"ALLOW_AUTO_SEND", "REQUIRES_APPROVAL"}
    assert "COA" in outbound["body"]

    approve_response = client.post(f"/messages/outbound/{outbound['id']}/approve")
    assert approve_response.status_code == 200
    send_response = client.post(f"/messages/outbound/{outbound['id']}/send")
    assert send_response.status_code == 200
    assert send_response.json()["status"] == "sent"

    inbound_response = client.post(
        "/messages/inbound",
        json={
            "company_id": supplier_id,
            "campaign_id": campaign_id,
            "channel": "email",
            "from_address": "sales@acme.example",
            "subject": "Re: RFQ",
            "body": "CAS 64-17-5 confirmed. Price: USD 12.50/kg EXW. MOQ: 25 kg. Lead time: 14 days. COA and SDS available. Payment: TT.",
        },
    )
    assert inbound_response.status_code == 201

    parse_response = client.post(f"/messages/inbound/{inbound_response.json()['id']}/parse")
    assert parse_response.status_code == 200
    assert parse_response.json()["quote_id"]

    comparison_response = client.get(f"/campaigns/{campaign_id}/comparison")
    assert comparison_response.status_code == 200
    assert comparison_response.json()[0]["price"] == 12.5
