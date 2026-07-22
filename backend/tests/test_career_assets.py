from fastapi.testclient import TestClient


def test_profile_asset_evidence_and_timeline_workflow(client: TestClient) -> None:
    profile_response = client.put(
        "/api/profile",
        json={
            "name": "Test Professional",
            "current_title": "Director",
            "current_organisation": "Example Institute",
            "career_mission": "Advance translational innovation",
            "career_narrative": "A public professional narrative.",
        },
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["name"] == "Test Professional"

    theme_response = client.post(
        "/api/themes", json={"name": "International Leadership", "description": ""}
    )
    organisation_response = client.post(
        "/api/organisations",
        json={
            "name": "Example Institute",
            "organisation_type": "University",
            "website": "https://example.edu",
            "notes": "",
        },
    )
    assert theme_response.status_code == 201
    assert organisation_response.status_code == 201

    asset_payload = {
        "title": "International conference chair",
        "description": "Led a public international conference.",
        "category": "Leadership Asset",
        "subcategory": "Conference leadership",
        "start_date": "2025-12-01",
        "end_date": "2025-12-03",
        "date_precision": "day",
        "status": "active",
        "impact_summary": "Convened an international professional community.",
        "organisation_id": organisation_response.json()["id"],
        "role": "General Chair",
        "visibility": "public",
        "tags": ["conference", "leadership"],
        "keywords": ["international"],
        "theme_ids": [theme_response.json()["id"]],
    }
    asset_response = client.post("/api/assets", json=asset_payload)
    assert asset_response.status_code == 201
    asset = asset_response.json()
    assert asset["themes"][0]["name"] == "International Leadership"
    assert asset["organisation"]["name"] == "Example Institute"

    evidence_response = client.post(
        f"/api/assets/{asset['id']}/evidence",
        json={
            "title": "Official event page",
            "description": "Lists the public chair appointment.",
            "source_url": "https://example.org/event",
            "document_id": None,
        },
    )
    assert evidence_response.status_code == 201

    search_response = client.get("/api/assets", params={"search": "conference"})
    assert search_response.status_code == 200
    assert search_response.json()["total"] == 1
    assert len(search_response.json()["items"][0]["evidence"]) == 1

    timeline_response = client.get("/api/timeline")
    assert timeline_response.status_code == 200
    assert timeline_response.json()[0]["title"] == "International conference chair"


def test_document_upload_is_local_only_and_duplicate_aware(client: TestClient) -> None:
    files = {"file": ("evidence.txt", b"Public professional evidence", "text/plain")}
    data = {"ai_handling_policy": "local_only", "confirmed_public_information": "true"}
    first = client.post("/api/documents", files=files, data=data)
    second = client.post("/api/documents", files=files, data=data)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["ai_handling_policy"] == "local_only"
    assert first.json()["extraction_status"] == "completed"


def test_document_upload_requires_public_information_confirmation(client: TestClient) -> None:
    response = client.post(
        "/api/documents",
        files={"file": ("evidence.txt", b"Public professional evidence", "text/plain")},
        data={"ai_handling_policy": "local_only", "confirmed_public_information": "false"},
    )

    assert response.status_code == 422


def test_timeline_duplicate_review_requires_confirmation_and_archives_rejected_record(
    client: TestClient,
) -> None:
    base_asset = {
        "description": "Led an international research conference.",
        "category": "Leadership Asset",
        "subcategory": "Conference leadership",
        "start_date": "2025-12-01",
        "end_date": None,
        "date_precision": "day",
        "status": "active",
        "impact_summary": "",
        "organisation_id": None,
        "role": "General Chair",
        "visibility": "public",
        "tags": [],
        "keywords": [],
        "theme_ids": [],
    }
    first = client.post(
        "/api/assets", json={**base_asset, "title": "International conference chair"}
    ).json()
    second = client.post(
        "/api/assets", json={**base_asset, "title": "Chair, International Conference"}
    ).json()

    groups = client.get("/api/timeline/duplicates")
    assert groups.status_code == 200
    assert len(groups.json()) == 1
    assert {item["id"] for item in groups.json()[0]["items"]} == {
        first["id"], second["id"]
    }
    assert len(client.get("/api/timeline").json()) == 2

    resolution = client.post(
        "/api/timeline/duplicates/resolve",
        json={"keep_id": first["id"], "archive_ids": [second["id"]]},
    )
    assert resolution.status_code == 200
    assert resolution.json()["kept_id"] == first["id"]
    assert resolution.json()["archived_ids"] == [second["id"]]
    assert [item["id"] for item in client.get("/api/timeline").json()] == [first["id"]]
    assert client.get(f"/api/assets/{second['id']}").json()["status"] == "archived"
    assert client.get("/api/timeline/duplicates").json() == []
