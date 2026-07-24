from fastapi.testclient import TestClient


def test_empty_dashboard_prioritises_foundation_and_backup(client: TestClient) -> None:
    response = client.get("/api/dashboard")

    assert response.status_code == 200
    dashboard = response.json()
    assert dashboard["metrics"] == {
        "active_assets": 0,
        "asset_categories": 0,
        "strategic_goals": 0,
        "timeline_events": 0,
        "open_opportunities": 0,
        "closing_soon": 0,
    }
    assert [item["key"] for item in dashboard["actions"][:3]] == [
        "complete-profile",
        "import-career",
        "create-backup",
    ]
    assert dashboard["actions"][0]["priority"] > dashboard["actions"][1]["priority"]


def test_dashboard_recommends_evidence_grounded_work_in_stable_order(
    client: TestClient,
) -> None:
    client.put(
        "/api/profile",
        json={
            "name": "Test Professional",
            "current_title": "Director",
            "current_organisation": "Example Institute",
            "career_mission": "Create public value",
            "career_narrative": "Executive research leader.",
        },
    )
    asset = client.post(
        "/api/assets",
        json={
            "title": "Research program director",
            "description": "Led a public research program.",
            "category": "Experience",
            "impact_summary": "",
        },
    ).json()
    client.post(
        "/api/goals",
        json={"title": "National centre director", "horizon": "medium_term"},
    )

    first = client.get("/api/dashboard").json()
    second = client.get("/api/dashboard").json()

    assert first["actions"] == second["actions"]
    keys = [item["key"] for item in first["actions"]]
    assert keys[:3] == ["assess-goals", "review-impact-summaries", "create-backup"]
    assert "add-evidence" in keys
    assert first["metrics"]["active_assets"] == 1
    assert first["metrics"]["strategic_goals"] == 1
    assert first["recent_assets"][0]["id"] == asset["id"]


def test_dashboard_removes_completed_asset_actions(client: TestClient) -> None:
    client.put(
        "/api/profile",
        json={"name": "Test Professional"},
    )
    asset = client.post(
        "/api/assets",
        json={
            "title": "Research program director",
            "description": "Led a public research program.",
            "category": "Experience",
            "impact_summary": "Established a multidisciplinary program with public evidence.",
        },
    ).json()
    client.post(
        f"/api/assets/{asset['id']}/evidence",
        json={
            "title": "Official profile",
            "description": "Publicly documents the role.",
            "source_url": "https://example.org/profile",
            "document_id": None,
        },
    )

    actions = client.get("/api/dashboard").json()["actions"]
    keys = {item["key"] for item in actions}
    assert "review-impact-summaries" not in keys
    assert "add-evidence" not in keys
