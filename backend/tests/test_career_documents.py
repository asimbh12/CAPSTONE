from fastapi.testclient import TestClient


def seed_career(client: TestClient) -> str:
    client.put(
        "/api/profile",
        json={
            "name": "Jane Example",
            "current_title": "Research Director",
            "current_organisation": "Example Institute",
            "career_mission": "Translate research into public benefit.",
            "career_narrative": "A research and innovation leader.",
        },
    )
    response = client.post(
        "/api/assets",
        json={
            "title": "Led national research program",
            "description": "Directed a multidisciplinary research program.",
            "category": "Leadership Asset",
            "subcategory": "",
            "start_date": "2023-01-01",
            "end_date": None,
            "date_precision": "day",
            "status": "active",
            "impact_summary": "Built a national partnership translating research into practice.",
            "organisation_id": None,
            "role": "Program Director",
            "visibility": "public",
            "tags": ["leadership"],
            "keywords": ["translation"],
            "theme_ids": [],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_generate_edit_and_export_grounded_career_document(client: TestClient) -> None:
    asset_id = seed_career(client)
    response = client.post(
        "/api/career-documents",
        json={
            "document_type": "professional_biography",
            "title": "Conference biography",
            "audience": "National research conference",
            "purpose": "Introduce a keynote speaker.",
            "tone": "executive",
            "asset_ids": [asset_id],
        },
    )
    assert response.status_code == 201
    document = response.json()
    assert document["provider"] == "grounded_template"
    assert document["asset_ids"] == [asset_id]
    assert "Jane Example" in document["content"]
    assert "national partnership" in document["content"]

    updated = client.put(
        f"/api/career-documents/{document['id']}",
        json={
            "title": "Reviewed conference biography",
            "content": document["content"] + "\n\nReviewed and approved.",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Reviewed conference biography"

    listing = client.get("/api/career-documents")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    docx = client.get(f"/api/career-documents/{document['id']}/export/docx")
    pdf = client.get(f"/api/career-documents/{document['id']}/export/pdf")
    assert docx.status_code == 200
    assert docx.content.startswith(b"PK")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")


def test_generation_requires_active_evidence(client: TestClient) -> None:
    response = client.post(
        "/api/career-documents",
        json={
            "document_type": "linkedin_about",
            "title": "LinkedIn About",
            "audience": "",
            "purpose": "",
            "tone": "accessible",
            "asset_ids": [],
        },
    )
    assert response.status_code == 409
