def test_sourcing_batch_import_creates_campaigns_queries_and_tasks(client) -> None:
    response = client.post(
        "/sourcing/batches",
        json={
            "name": "Demo CAS import",
            "csv_text": "CAS,qty\n64-17-5,100 kg\n7732-18-5,200 kg\n64-17-4,bad\n64-17-5,duplicate",
            "quantity": "100 kg",
            "destination_country": "Poland",
            "required_grade": "technical grade",
            "intended_use": "lawful industrial validation",
            "channels": ["legal_search", "contact_form", "alibaba_internal", "indiamart_internal"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["summary"]["valid"] == 2
    assert payload["summary"]["invalid"] == 1
    assert payload["summary"]["duplicates"] == 1
    assert payload["summary"]["campaigns_created"] == 2
    assert payload["summary"]["manual_tasks_created"] == 8
    ready_items = [item for item in payload["items"] if item["status"] == "ready"]
    assert len(ready_items) == 2
    assert any(query["query"] == "64-17-5 supplier" for query in ready_items[0]["queries"])
    assert {task["channel"] for task in ready_items[0]["tasks"]} == {
        "legal_search",
        "contact_form",
        "alibaba_internal",
        "indiamart_internal",
    }


def test_sourcing_batch_report_counts_linked_objects(client) -> None:
    response = client.post(
        "/sourcing/batches",
        json={
            "name": "Report batch",
            "cas_numbers": ["64-17-5"],
            "channels": ["legal_search", "telegram_bot", "signal_manual"],
            "create_campaigns": True,
        },
    )
    assert response.status_code == 201
    batch_id = response.json()["batch_id"]

    report = client.get(f"/sourcing/batches/{batch_id}/report")
    assert report.status_code == 200
    payload = report.json()
    assert payload["batch"]["batch_id"] == batch_id
    assert len(payload["campaign_ids"]) == 1
    assert len(payload["substance_ids"]) == 1
    assert len(payload["manual_task_ids"]) == 3
    assert payload["channel_plan"]["signal_manual"] == "Signal remains manual-task only."
