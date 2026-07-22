# Delivery Roadmap

## Stage 1 — Product and architecture baseline

Deliverables:

- Approved MVP product requirements.
- Testable acceptance criteria.
- System context, container, module, and data-flow diagrams.
- Initial relational domain and scoring models.
- AI authority, provenance, privacy, and grounding rules.
- Architecture decision log and delivery stages.

Exit condition: the owner approves the Stage 1 baseline and unresolved questions do not block repository scaffolding.

## Stage 2 — Repository foundation

- Scaffold frontend and backend.
- Configure Docker Compose and local data volumes.
- Establish SQLModel, Alembic, settings, health checks, and structured errors.
- Configure linting, typing, Pytest, Vitest, Playwright, and CI-ready commands.
- Add secret templates and Git exclusions.

## Stage 3 — Career assets vertical slice

- Career profile, themes, goals, assets, evidence, documents, people, and organisations.
- PDF/DOCX/TXT/JSON upload and local preservation.
- Search, filtering, timeline projection, provenance, and audit events.
- Versioned JSON templates, dry-run import, and export.
- Backup and restore before real seed data is introduced.

## Stage 4 — AI enrichment

- Document-led onboarding from CVs and career materials, with public-profile URL ingestion.
- Reviewable extraction proposals that populate blank profile fields, assets, organisations,
  evidence, themes, and the timeline after user confirmation.
- Provider-neutral contracts and Gemini adapter.
- Document-level AI policy enforcement.
- Structured tagging, theme extraction, association suggestions, and automatic enrichment.
- Manual correction, suppression, reprocessing, usage/error handling, and deterministic test doubles.

Stage 4 delivered: document/link onboarding, explicit provider status, reviewed apply, ingestion
history, correction/reprocessing/suppression, additive asset enrichment, audit events, and
privacy-preserving AI operation telemetry.
Multi-source onboarding adds typed URL collections, consolidated review, cross-source
deduplication, conflict detection, coverage reporting, and source-level provenance.

## Stage 5 — Opportunity prioritisation

- Opportunity lifecycle and categories.
- Validated scoring inputs and versioned deterministic scoring.
- Rankings, filters, urgency, explanations, next actions, and dashboard summaries.

Stage 5 delivered: opportunity creation/editing and lifecycle management, organisation and
public-source links, validated 1–5 strategic value / 0–100 probability / 1–5 effort inputs,
versioned assessment history, deterministic ranking, deadline urgency, score explanations,
search and filters, archive handling, next actions, audit events, and overview summaries.

## Stage 6 — Targets and readiness

- User-defined targets and weighted criteria.
- AI-suggested trajectories and criteria with explicit adoption.
- Evidence mapping, versioned readiness assessment, gaps, strengths, and recommendations.

Stage 6 delivered: user-adopted targets, positive weighted criteria, career asset and evidence
mappings, versioned deterministic readiness and confidence snapshots, strengths, gaps,
recommended actions, audit events, and Gemini trajectory suggestions that remain unadopted until
the user explicitly reviews and saves them.

## Stage 7 — Job applications

- Position-description upload and pasted-text ingestion.
- Requirement extraction, review, and confirmation.
- Evidence mapping, fit/readiness analysis, and unsupported-claim detection.
- On-screen drafts and DOCX/PDF export for cover letters, selection criteria, tailored CVs, and interview notes.

## Stage 8 — MVP hardening

- Dashboard integration and next-best-action recommendations.
- End-to-end workflow coverage and accessibility review.
- Migration, backup/restore, data-integrity, AI-policy, and failure-recovery tests.
- Windows installation, operation, and troubleshooting guides.
- Test with the owner's public professional seed dataset.

## Deferred roadmap

After MVP validation: broader document templates, fellowships, awards, grants, CRM, thought leadership, discovery/monitoring, honours, analytics expansion, PostgreSQL, authentication, multi-user workspaces, cloud deployment, encryption and production monitoring.
