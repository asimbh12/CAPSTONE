import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_target_mapping_and_versioned_readiness(client: TestClient) -> None:
    asset = client.post(
        "/api/assets",
        json={
            "title": "Research leadership",
            "description": "Led a public research program",
            "category": "Leadership",
        },
    ).json()
    evidence = client.post(
        f"/api/assets/{asset['id']}/evidence",
        json={
            "title": "Public program evidence",
            "description": "Published program record",
            "source_url": "https://example.org/program",
            "document_id": None,
        },
    ).json()
    target_response = client.post(
        "/api/targets",
        json={
            "title": "Research executive",
            "description": "Progress toward executive research leadership",
            "target_type": "Leadership",
            "status": "adopted",
            "target_date": "2028-12-31",
            "provenance": "user",
            "criteria": [
                {
                    "title": "Research leadership",
                    "description": "Evidence of leading programs",
                    "weight": 3,
                    "sort_order": 0,
                    "provenance": "user",
                },
                {
                    "title": "External recognition",
                    "description": "Recognised sector contribution",
                    "weight": 1,
                    "sort_order": 1,
                    "provenance": "user",
                },
            ],
        },
    )
    assert target_response.status_code == 201
    target = target_response.json()
    first, second = target["criteria"]
    mapped = client.put(
        f"/api/targets/criteria/{first['id']}/mappings",
        json={"asset_ids": [asset["id"]], "evidence_ids": [evidence["id"]]},
    )
    assert mapped.status_code == 200
    payload = {
        "criteria": [
            {
                "criterion_id": first["id"],
                "coverage": 80,
                "confidence": 75,
                "explanation": "Strong mapped evidence",
                "recommended_action": "Add external validation",
            },
            {
                "criterion_id": second["id"],
                "coverage": 20,
                "confidence": 50,
                "explanation": "Limited evidence",
                "recommended_action": "Pursue sector recognition",
            },
        ]
    }
    first_report = client.post(f"/api/targets/{target['id']}/assessments", json=payload)
    assert first_report.status_code == 200
    report = first_report.json()
    assert report["version"] == 1 and report["readiness_score"] == 65.0
    assert report["overall_confidence"] == 68.8
    assert report["strengths"] == ["Research leadership"]
    assert report["gaps"] == ["External recognition"]
    assert report["criteria"][0]["asset_ids"] == [asset["id"]]
    assert (
        client.post(f"/api/targets/{target['id']}/assessments", json=payload).json()["version"] == 2
    )
    assert client.get("/api/targets").json()[0]["latest_assessment"]["version"] == 2


def test_readiness_requires_every_current_criterion(client: TestClient) -> None:
    target = client.post(
        "/api/targets",
        json={
            "title": "Board role",
            "target_type": "Advisory",
            "criteria": [{"title": "Governance", "weight": 1}],
        },
    ).json()
    response = client.post(f"/api/targets/{target['id']}/assessments", json={"criteria": []})
    assert response.status_code == 422


def test_strategic_goal_mapping_builds_readiness_trajectory(client: TestClient) -> None:
    goal = client.post(
        "/api/goals",
        json={
            "title": "Lead national research capability",
            "description": "Build toward national research leadership",
            "horizon": "long_term",
            "target_date": "2030-12-31",
        },
    ).json()
    target = client.post(
        "/api/targets",
        json={
            "title": "National research centre director",
            "criteria": [{"title": "National leadership", "weight": 1}],
        },
    ).json()
    mapped = client.put(
        f"/api/targets/{target['id']}/goals", json={"goal_ids": [goal["id"]]}
    )
    assert mapped.status_code == 200
    assert mapped.json()["goal_ids"] == [goal["id"]]
    criterion_id = target["criteria"][0]["id"]
    for coverage in (40, 70):
        response = client.post(
            f"/api/targets/{target['id']}/assessments",
            json={
                "criteria": [
                    {
                        "criterion_id": criterion_id,
                        "coverage": coverage,
                        "confidence": 80,
                        "explanation": "Versioned progress evidence",
                        "recommended_action": "Continue building national evidence",
                    }
                ]
            },
        )
        assert response.status_code == 200

    progress = client.get("/api/targets/goal-readiness")
    assert progress.status_code == 200
    readiness = progress.json()[0]
    assert readiness["goal_id"] == goal["id"]
    assert readiness["linked_target_ids"] == [target["id"]]
    assert readiness["readiness_score"] == 70
    assert readiness["trend"] == 30
    assert readiness["status"] == "progressing"
    assert [point["readiness_score"] for point in readiness["trajectory"]] == [40, 70]


def test_ai_goal_assessment_maps_existing_achievements(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    goal = client.post(
        "/api/goals",
        json={"title": "IEEE Senior Member", "horizon": "short_term"},
    ).json()
    asset = client.post(
        "/api/assets",
        json={
            "title": "International research leadership",
            "description": "Led international research programs and conferences",
            "category": "Leadership",
        },
    ).json()

    class FakeResponse:
        text = json.dumps(
            {
                "readiness_score": 72,
                "confidence": 85,
                "explanation": "Existing leadership demonstrates substantial readiness.",
                "strengths": ["International research leadership"],
                "gaps": ["Document IEEE-specific service"],
                "recommendations": ["Compile IEEE membership and service evidence"],
                "asset_ids": [asset["id"]],
            }
        )

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            self.models = FakeModels()

    monkeypatch.setenv("CAPSTONE_AI_PROVIDER", "gemini")
    monkeypatch.setenv("CAPSTONE_GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr("google.genai.Client", FakeClient)

    response = client.post(f"/api/targets/goals/{goal['id']}/auto-assess")
    assert response.status_code == 200
    result = response.json()
    assert result["readiness_score"] == 72
    assert result["overall_confidence"] == 85
    assert result["mapped_asset_ids"] == [asset["id"]]
    assert result["mapped_asset_titles"] == ["International research leadership"]
    assert result["trajectory"][0]["readiness_score"] == 72


def test_ai_mapping_links_existing_assets_and_creates_assessment(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    asset = client.post(
        "/api/assets",
        json={
            "title": "HDR Director",
            "description": "Supervised and graduated higher degree research candidates",
            "category": "Research leadership",
        },
    ).json()
    evidence = client.post(
        f"/api/assets/{asset['id']}/evidence",
        json={
            "title": "Official university profile",
            "description": "Public record of HDR leadership",
            "source_url": "https://example.org/profile",
        },
    ).json()
    target = client.post(
        "/api/targets",
        json={
            "title": "Research centre director",
            "criteria": [{"title": "HDR mentorship", "weight": 1}],
        },
    ).json()
    criterion_id = target["criteria"][0]["id"]
    manual_asset = client.post(
        "/api/assets",
        json={
            "title": "Research program leadership",
            "description": "User-confirmed supporting context",
            "category": "Leadership",
        },
    ).json()
    assert (
        client.put(
            f"/api/targets/criteria/{criterion_id}/mappings",
            json={"asset_ids": [manual_asset["id"]], "evidence_ids": []},
        ).status_code
        == 200
    )

    class FakeResponse:
        text = json.dumps(
            {
                "criteria": [
                    {
                        "criterion_id": criterion_id,
                        "asset_ids": [asset["id"], "not-a-real-id"],
                        "coverage": 85,
                        "confidence": 90,
                        "explanation": "HDR Director demonstrates sustained mentorship.",
                        "recommended_action": "Document graduation outcomes.",
                    }
                ]
            }
        )

    class FakeModels:
        @staticmethod
        def generate_content(**kwargs: object) -> FakeResponse:
            return FakeResponse()

    class FakeClient:
        def __init__(self, **kwargs: object) -> None:
            self.models = FakeModels()

    monkeypatch.setenv("CAPSTONE_AI_PROVIDER", "gemini")
    monkeypatch.setenv("CAPSTONE_GEMINI_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr("google.genai.Client", FakeClient)

    response = client.post(f"/api/targets/{target['id']}/auto-map")
    assert response.status_code == 200
    report = response.json()
    assert report["readiness_score"] == 85
    assert report["strengths"] == ["HDR mentorship"]
    assert set(report["criteria"][0]["asset_ids"]) == {manual_asset["id"], asset["id"]}
    assert report["criteria"][0]["evidence_ids"] == [evidence["id"]]
    updated = client.get("/api/targets").json()[0]
    assert set(updated["criteria"][0]["asset_ids"]) == {manual_asset["id"], asset["id"]}
