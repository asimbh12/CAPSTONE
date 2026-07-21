from datetime import date, timedelta

from fastapi.testclient import TestClient


def payload(
    title: str,
    value: int = 5,
    probability: int = 80,
    effort: int = 2,
    closing_date: str | None = None,
) -> dict[str, object]:
    return {
        "title": title,
        "description": "Public role",
        "opportunity_type": "Job",
        "organisation_id": None,
        "url": "https://example.org/role",
        "opening_date": None,
        "closing_date": closing_date,
        "status": "discovered",
        "owner": "Local user",
        "next_action": "Review criteria",
        "notes": "",
        "source": "user",
        "strategic_value": value,
        "probability": probability,
        "effort": effort,
        "score_input_source": "user",
    }


def test_score_is_deterministic_and_explained(client: TestClient) -> None:
    response = client.post("/api/opportunities", json=payload("Leadership role"))
    assert response.status_code == 201
    assessment = response.json()["assessment"]
    assert assessment["raw_score"] == 2.0
    assert assessment["normalized_score"] == 40.0
    assert assessment["algorithm_version"] == "opportunity-priority-v1"
    assert "strategic value" in assessment["explanation"]


def test_effort_zero_is_rejected(client: TestClient) -> None:
    assert client.post("/api/opportunities", json=payload("Invalid", effort=0)).status_code == 422


def test_ranking_and_urgency_are_separate(client: TestClient) -> None:
    soon = (date.today() + timedelta(days=2)).isoformat()
    client.post(
        "/api/opportunities",
        json=payload("Urgent low priority", value=1, probability=20, effort=5, closing_date=soon),
    )
    client.post(
        "/api/opportunities", json=payload("High priority", value=5, probability=90, effort=1)
    )
    result = client.get("/api/opportunities").json()["items"]
    assert result[0]["title"] == "High priority"
    urgent = next(item for item in result if item["title"] == "Urgent low priority")
    assert urgent["urgency"]["level"] == "critical"
    assert urgent["assessment"]["normalized_score"] == 0.8


def test_update_retains_assessment_history(client: TestClient) -> None:
    item = client.post("/api/opportunities", json=payload("Grant")).json()
    updated = payload("Grant", probability=90)
    assert client.put(f"/api/opportunities/{item['id']}", json=updated).status_code == 200
    history = client.get(f"/api/opportunities/{item['id']}/assessments").json()
    assert len(history) == 2


def test_summary_and_archive(client: TestClient) -> None:
    item = client.post("/api/opportunities", json=payload("Fellowship")).json()
    assert client.get("/api/opportunities/summary").json()["active"] == 1
    assert client.post(f"/api/opportunities/{item['id']}/archive").status_code == 200
    assert client.get("/api/opportunities").json()["total"] == 0
