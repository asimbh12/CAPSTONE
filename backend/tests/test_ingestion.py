from fastapi.testclient import TestClient

from app.schemas.ingestion import (
    CareerExtractionProposal,
    ProposedAsset,
    ProposedProfile,
    PublicProfileSource,
)
from app.services.ingestion import merge_source_proposals


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


def test_ingestion_history_corrections_reprocessing_and_suppression(client: TestClient) -> None:
    created = client.post(
        "/api/ingestions/documents",
        files={
            "file": (
                "history.txt",
                b"Public Professional\nBoard Chair 2021 - present",
                "text/plain",
            )
        },
        data={"ai_handling_policy": "local_only", "confirmed_public_information": "true"},
    ).json()
    created["proposal"]["profile"]["current_title"] = "Corrected title"
    corrected = client.put(f"/api/ingestions/{created['id']}/proposal", json=created["proposal"])
    assert corrected.status_code == 200
    assert corrected.json()["proposal"]["profile"]["current_title"] == "Corrected title"

    reprocessed = client.post(f"/api/ingestions/{created['id']}/reprocess")
    assert reprocessed.status_code == 200
    assert reprocessed.json()["provider"] == "deterministic"
    suppressed = client.post(f"/api/ingestions/{created['id']}/suppress")
    assert suppressed.status_code == 200
    assert suppressed.json()["status"] == "suppressed"
    assert client.get("/api/ingestions").json()[0]["id"] == created["id"]
    assert client.get("/api/ingestions/operations").status_code == 200


def test_asset_enrichment_adds_only_derived_fields(client: TestClient) -> None:
    asset = client.post(
        "/api/assets",
        json={
            "title": "Public research leadership",
            "description": "Led collaborative research partnerships and public engagement",
            "category": "Leadership Asset",
        },
    ).json()
    enriched = client.post(f"/api/ingestions/assets/{asset['id']}/enrich")
    assert enriched.status_code == 200
    updated = client.get(f"/api/assets/{asset['id']}").json()
    assert updated["title"] == asset["title"]
    assert updated["description"] == asset["description"]
    assert updated["tags"]


def test_multi_source_merge_deduplicates_and_preserves_provenance() -> None:
    institutional = PublicProfileSource(
        url="https://example.org/profile", source_type="institutional_profile"
    )
    scholar = PublicProfileSource(
        url="https://scholar.example.org/profile", source_type="google_scholar"
    )
    first = CareerExtractionProposal(
        profile=ProposedProfile(name="Example Professional", current_title="Director"),
        assets=[ProposedAsset(title="Research leadership", start_date="2020-01-01")],
    )
    second = CareerExtractionProposal(
        profile=ProposedProfile(name="Example Professional", current_title="Professor"),
        assets=[
            ProposedAsset(
                title="Research leadership",
                start_date="2020-01-01",
                themes=["Research impact"],
            )
        ],
    )
    merged = merge_source_proposals(
        [(institutional, "Institution", first), (scholar, "Scholar", second)]
    )
    assert len(merged.assets) == 1
    assert len(merged.assets[0].source_urls) == 2
    assert merged.assets[0].themes == ["Research impact"]
    assert merged.conflicts
    assert merged.coverage == {"institutional_profile": 1, "google_scholar": 1}
