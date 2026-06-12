from app.core.config import get_settings


def _register_and_login(client, email: str) -> tuple[str, dict]:
    register = client.post("/auth/register", json={"email": email, "password": "ChangeMe123!"})
    assert register.status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": "ChangeMe123!"})
    assert login.status_code == 200
    return login.json()["access_token"], register.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_safety_override_requires_admin(client) -> None:
    admin_token, _ = _register_and_login(client, "admin@procurement-crm.com")
    user_token, user = _register_and_login(client, "user@procurement-crm.com")
    assert user["role"] == "user"

    response = client.put(
        "/safety-override",
        headers=_auth(user_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": True,
        },
    )
    assert response.status_code == 403

    admin_response = client.put(
        "/safety-override",
        headers=_auth(admin_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": True,
        },
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["active"] is True


def test_safety_override_rejects_missing_test_confirmation(client) -> None:
    admin_token, _ = _register_and_login(client, "admin2@procurement-crm.com")
    response = client.put(
        "/safety-override",
        headers=_auth(admin_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": False,
        },
    )
    assert response.status_code == 422


def test_safety_override_simulates_in_autonomous_campaign(client) -> None:
    admin_token, _ = _register_and_login(client, "admin3@procurement-crm.com")
    override = client.put(
        "/safety-override",
        headers=_auth(admin_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": True,
            "allowed_overrides": ["missing_contact_evidence", "high_risk_manual_review"],
        },
    )
    assert override.status_code == 200

    substance = client.post("/substances", json={"cas": "64-17-5", "primary_name": "Ethanol"})
    assert substance.status_code == 201
    supplier = client.post(
        "/suppliers",
        json={
            "name": "Test Supplier",
            "website": "https://supplier.example.com",
            "country": "PL",
            "risk_level": "high",
            "risk_score": 90,
            "contacts": [
                {
                    "channel": "email",
                    "value": "sales@supplier.example.com",
                    "source_url": "https://supplier.example.com/contact",
                    "evidence_text": "Official business contact listed on supplier website.",
                    "is_primary": True,
                }
            ],
        },
    )
    assert supplier.status_code == 201
    risk_update = client.patch(
        f"/suppliers/{supplier.json()['id']}",
        json={"risk_level": "high", "risk_score": 90},
    )
    assert risk_update.status_code == 200
    campaign = client.post(
        "/campaigns",
        json={
            "substance_id": substance.json()["id"],
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "auto_send_enabled": False,
        },
    )
    assert campaign.status_code == 201

    result = client.post(
        f"/campaigns/{campaign.json()['id']}/run-autonomous",
        json={"supplier_ids": [supplier.json()["id"]]},
    )

    assert result.status_code == 200
    payload = result.json()
    assert payload["sent"] == 0
    assert payload["simulated"] == 1
    assert payload["items"][0]["policy_decision"] == "TEST_OVERRIDE_ALLOW"
    assert payload["items"][0]["status"] == "test_override_simulated_send"


def test_safety_override_does_not_override_messenger_without_consent(client) -> None:
    admin_token, _ = _register_and_login(client, "admin4@procurement-crm.com")
    override = client.put(
        "/safety-override",
        headers=_auth(admin_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": True,
        },
    )
    assert override.status_code == 200

    substance = client.post("/substances", json={"cas": "64-17-5", "primary_name": "Ethanol"})
    supplier = client.post(
        "/suppliers",
        json={
            "name": "Messenger Only Supplier",
            "website": "https://supplier.example.com",
            "risk_level": "low",
            "risk_score": 0,
            "contacts": [
                {
                    "channel": "whatsapp",
                    "value": "+48100100100",
                    "source_url": "https://supplier.example.com/contact",
                    "evidence_text": "Public WhatsApp listed on contact page.",
                    "is_primary": True,
                }
            ],
        },
    )
    campaign = client.post(
        "/campaigns",
        json={
            "substance_id": substance.json()["id"],
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "auto_send_enabled": True,
        },
    )

    result = client.post(
        f"/campaigns/{campaign.json()['id']}/run-autonomous",
        json={"supplier_ids": [supplier.json()["id"]]},
    )
    assert result.status_code == 200
    assert result.json()["items"][0]["policy_decision"] == "BLOCK"


def test_safety_override_production_locked(client, monkeypatch) -> None:
    admin_token, _ = _register_and_login(client, "admin5@procurement-crm.com")
    monkeypatch.setattr(get_settings(), "app_env", "production")
    response = client.put(
        "/safety-override",
        headers=_auth(admin_token),
        json={
            "enabled": True,
            "reason": "Testing own local workflow behavior",
            "expires_in_minutes": 30,
            "confirm_test_only": True,
        },
    )
    assert response.status_code == 422
