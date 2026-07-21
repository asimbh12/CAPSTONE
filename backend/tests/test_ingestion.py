from fastapi.testclient import TestClient


def test_document_ingestion_reviews_and_populates_without_overwriting_user_facts(
    client: TestClient,
) -> None:
    client.put(
        "/api/profile",
        json={
            "name": "User-authored name",
            "current_title": "",
            "current_organisation": "",
            "career_mission": "User-authored mission",
            "career_narrative": "",
        },
    )
    document = (
        b"Example Professional\nDirector, Example Institute 2020 - present\nLed public programs."
    )
    response = client.post(
        "/api/ingestions/documents",
        files={"file": ("career.txt", document, "text/plain")},
        data={
            "ai_handling_policy": "local_only",
            "confirmed_public_information": "true",
        },
    )
    assert response.status_code == 201
    run = response.json()
    assert run["provider"] == "deterministic"
    assert len(run["proposal"]["assets"]) == 1
    run["proposal"]["profile"]["current_title"] = "Proposed director"

    applied = client.post(f"/api/ingestions/{run['id']}/apply", json={"proposal": run["proposal"]})
    assert applied.status_code == 200
    assert applied.json()["assets_created"] == 1
    profile = client.get("/api/profile").json()
    assert profile["name"] == "User-authored name"
    assert profile["career_mission"] == "User-authored mission"
    assert profile["current_title"] == "Proposed director"
    assert client.get("/api/timeline").json()[0]["start_date"] == "2020-01-01"


def test_ingestion_rejects_unconfirmed_document(client: TestClient) -> None:
    response = client.post(
        "/api/ingestions/documents",
        files={"file": ("career.txt", b"Public career 2020", "text/plain")},
        data={"ai_handling_policy": "local_only", "confirmed_public_information": "false"},
    )
    assert response.status_code == 422
