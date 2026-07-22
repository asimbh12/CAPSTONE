from fastapi.testclient import TestClient

POSITION = """
Director, National Research Centre
Selection criteria
- Demonstrated research leadership and centre strategy.
- Experience securing major competitive research grants.
- Strong stakeholder communication and industry engagement.
- Desirable experience mentoring higher degree research candidates.
"""


def _create(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/applications",
        json={
            "role_title": "Director, National Research Centre",
            "organisation": "Example University",
            "position_description": POSITION,
            "source_url": "https://example.org/role",
            "confirmed_public_information": True,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_application_requires_public_information_confirmation(client: TestClient) -> None:
    response = client.post(
        "/api/applications",
        json={
            "role_title": "Director",
            "position_description": POSITION,
            "confirmed_public_information": False,
        },
    )
    assert response.status_code == 422


def test_review_assess_draft_and_export_workflow(client: TestClient) -> None:
    asset = client.post(
        "/api/assets",
        json={
            "title": "Research centre leadership",
            "description": "Led national research strategy and industry engagement.",
            "category": "Leadership",
            "impact_summary": "Secured competitive research grants and mentored HDR candidates.",
            "visibility": "public",
        },
    )
    assert asset.status_code == 201
    application = _create(client)
    assert application["requirements"]
    application_id = application["id"]

    premature = client.post(f"/api/applications/{application_id}/assess")
    assert premature.status_code == 409

    requirements = [
        {
            "title": row["title"],
            "description": row["description"],
            "requirement_type": row["requirement_type"],
            "weight": row["weight"],
        }
        for row in application["requirements"]
    ]
    confirmed = client.put(
        f"/api/applications/{application_id}/requirements",
        json={"requirements": requirements, "confirmed": True},
    )
    assert confirmed.status_code == 200
    assessed = client.post(f"/api/applications/{application_id}/assess")
    assert assessed.status_code == 200
    assert assessed.json()["assessment"]["fit_score"] > 0
    assert any(row["asset_ids"] for row in assessed.json()["requirements"])

    drafted = client.post(f"/api/applications/{application_id}/drafts")
    assert drafted.status_code == 200
    assert {row["draft_type"] for row in drafted.json()["drafts"]} == {
        "cover_letter",
        "selection_criteria",
        "tailored_cv",
        "interview_notes",
    }
    assert all(row["unsupported_claims"] == [] for row in drafted.json()["drafts"])

    docx = client.get(f"/api/applications/{application_id}/export/docx")
    pdf = client.get(f"/api/applications/{application_id}/export/pdf")
    assert docx.status_code == 200 and docx.content.startswith(b"PK")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
