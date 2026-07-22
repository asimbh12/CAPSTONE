from fastapi.testclient import TestClient


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
