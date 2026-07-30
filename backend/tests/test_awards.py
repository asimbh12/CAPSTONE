from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.test_fellowships import create_assessed_target


def test_award_reuses_readiness_and_tracks_nomination_dossier(client: TestClient) -> None:
    target_id = create_assessed_target(client)
    deadline = date.today() + timedelta(days=21)
    response = client.post(
        "/api/awards",
        json={
            "name": "Example National Research Award",
            "organisation": "Example Foundation",
            "award_type": "research_australia",
            "website": "https://example.org/award",
            "deadline": str(deadline),
            "status": "seeking_nominator",
            "target_id": target_id,
            "opportunity_id": None,
            "nominator_name": "Public Professor",
            "nominator_status": "candidate",
            "dossier_status": "evidence_review",
            "next_action": "Review mapped impact evidence.",
            "notes": "Public professional nomination pathway.",
        },
    )
    assert response.status_code == 201
    award = response.json()
    assert award["readiness_score"] == 82
    assert award["deadline_status"] == "closing_soon"
    assert award["days_remaining"] == 21
    assert award["dossier_status"] == "evidence_review"

    listing = client.get("/api/awards").json()
    assert listing["active"] == 1
    assert listing["closing_soon"] == 1
    assert listing["nomination_attention"] == 1

    payload = {
        key: award[key]
        for key in (
            "name", "organisation", "award_type", "website", "deadline", "status",
            "target_id", "opportunity_id", "nominator_name", "nominator_status",
            "dossier_status", "next_action", "notes",
        )
    }
    payload["nominator_status"] = "confirmed"
    payload["dossier_status"] = "drafting"
    updated = client.put(f"/api/awards/{award['id']}", json=payload)
    assert updated.status_code == 200
    assert updated.json()["nominator_status"] == "confirmed"
    assert updated.json()["dossier_status"] == "drafting"

    assert client.post(f"/api/awards/{award['id']}/archive").status_code == 200
    assert client.get("/api/awards").json()["total"] == 0


def test_award_rejects_unknown_target(client: TestClient) -> None:
    response = client.post(
        "/api/awards",
        json={
            "name": "Invalid linked award",
            "target_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert response.status_code == 422
