from datetime import date, timedelta

from fastapi.testclient import TestClient


def create_assessed_target(client: TestClient) -> str:
    target = client.post(
        "/api/targets",
        json={
            "title": "National Academy Fellowship",
            "description": "Recognition for national research leadership.",
            "target_type": "Fellowship",
            "status": "adopted",
            "target_date": None,
            "provenance": "user",
            "criteria": [
                {
                    "title": "National leadership",
                    "description": "Demonstrated national leadership and impact.",
                    "weight": 1,
                    "sort_order": 0,
                    "provenance": "user",
                }
            ],
        },
    )
    assert target.status_code == 201
    row = target.json()
    assessment = client.post(
        f"/api/targets/{row['id']}/assessments",
        json={
            "criteria": [
                {
                    "criterion_id": row["criteria"][0]["id"],
                    "coverage": 82,
                    "confidence": 76,
                    "explanation": "Strong mapped leadership record.",
                    "recommended_action": "Secure sponsor confirmation.",
                }
            ]
        },
    )
    assert assessment.status_code == 200
    return row["id"]


def test_fellowship_reuses_target_readiness_and_tracks_workflow(client: TestClient) -> None:
    target_id = create_assessed_target(client)
    deadline = date.today() + timedelta(days=14)
    created = client.post(
        "/api/fellowships",
        json={
            "name": "Example Academy Fellow",
            "organisation": "Example Academy",
            "website": "https://example.org/fellowship",
            "deadline": str(deadline),
            "status": "seeking_sponsor",
            "target_id": target_id,
            "opportunity_id": None,
            "sponsor_name": "Public Professor",
            "sponsor_status": "candidate",
            "next_action": "Discuss nomination evidence.",
            "notes": "Public professional pathway.",
        },
    )
    assert created.status_code == 201
    fellowship = created.json()
    assert fellowship["readiness_score"] == 82
    assert fellowship["readiness_confidence"] == 76
    assert fellowship["readiness_version"] == 1
    assert fellowship["deadline_status"] == "closing_soon"
    assert fellowship["days_remaining"] == 14
    assert fellowship["strengths"] == ["National leadership"]

    listing = client.get("/api/fellowships")
    assert listing.status_code == 200
    assert listing.json()["active"] == 1
    assert listing.json()["closing_soon"] == 1
    assert listing.json()["sponsor_attention"] == 1

    updated_payload = {
        "name": fellowship["name"],
        "organisation": fellowship["organisation"],
        "website": fellowship["website"],
        "deadline": fellowship["deadline"],
        "status": "ready",
        "target_id": target_id,
        "opportunity_id": None,
        "sponsor_name": "Public Professor",
        "sponsor_status": "confirmed",
        "next_action": "Complete nomination draft.",
        "notes": fellowship["notes"],
    }
    updated = client.put(f"/api/fellowships/{fellowship['id']}", json=updated_payload)
    assert updated.status_code == 200
    assert updated.json()["sponsor_status"] == "confirmed"

    archived = client.post(f"/api/fellowships/{fellowship['id']}/archive")
    assert archived.status_code == 200
    assert client.get("/api/fellowships").json()["total"] == 0


def test_fellowship_rejects_unknown_target(client: TestClient) -> None:
    response = client.post(
        "/api/fellowships",
        json={
            "name": "Invalid linked fellowship",
            "target_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert response.status_code == 422
