# CAPSTONE

**Career Advancement, Positioning, Strategy, Tracking, Opportunity Navigation and Excellence**

CAPSTONE is a local-first, AI-assisted career intelligence platform. It turns public professional achievements, experience, relationships, and supporting documents into reusable career assets for opportunity prioritisation and job applications.

The first release is a single-user Windows web application with no authentication. It uses a React/TypeScript frontend, FastAPI backend, SQLite database, local document storage, and a provider-neutral AI integration initially configured for Gemini.

## Current status

Stage 3 provides the first complete career-intelligence workflow: profile, goals, themes,
career assets, evidence and local documents, search/filtering, timeline generation, versioned
JSON import/export, audit events, and coordinated local backups.

Stage 4 begins with document-led onboarding. Use **Import career** to upload a PDF, DOCX,
or TXT CV, or analyse an accessible public professional page. CAPSTONE creates an editable
proposal before filling blank profile fields and creating evidence-backed career assets.
JSON remains available for technical portability but is not required for onboarding.
The enrichment workspace also provides provider visibility, ingestion history, correction,
reprocessing and suppression controls, plus additive AI-managed asset tags and themes.
Multiple typed public URLs can be analysed as one source collection with cross-source
deduplication, conflict warnings, coverage summaries, and source-level evidence provenance.
Public URL analysis uses Gemini URL Context when **AI allowed** is selected, while DOCX imports
preserve both paragraph and table content. The review screen reports source coverage and warns
when a page exposes too little readable text for reliable local-only extraction.

Stage 5 adds an **Opportunities** workspace for jobs, grants, fellowships, awards, leadership,
board, media, and custom opportunities. It provides lifecycle tracking, deadline urgency,
next actions, filters, and reproducible priority rankings. Each assessment preserves its
inputs and scoring algorithm version; urgency is deliberately displayed separately.

Stage 6 adds a **Targets** workspace for defining desired roles and trajectories, mapping
career assets and evidence to weighted target criteria, and producing versioned readiness
assessments. Gemini can suggest trajectories from the user's existing public profile and
career assets; suggestions remain drafts until the user explicitly adopts them.

## Run locally

With Docker Desktop running:

```powershell
docker compose up --build
```

Then open <http://127.0.0.1:5173>. See the
[development guide](docs/development/getting-started.md) for native setup and verification.

See the [Stage 3 testing guide](docs/development/stage-3-testing.md) for the interactive
career-asset and data-safety workflow.
See the [Stage 4 onboarding guide](docs/development/stage-4-onboarding.md) for CV and public-link
ingestion.
See the [Stage 5 testing guide](docs/development/stage-5-opportunities.md) for opportunity
tracking and prioritisation.
See the [Stage 6 testing guide](docs/development/stage-6-targets-readiness.md) for target
definition, evidence mapping, AI suggestions, and readiness assessments.

## Documentation

- [Product requirements](docs/product/mvp-requirements.md)
- [Acceptance criteria](docs/product/acceptance-criteria.md)
- [System architecture](docs/architecture/system-architecture.md)
- [Domain model](docs/architecture/domain-model.md)
- [AI and data policy](docs/product/ai-data-policy.md)
- [Risk register](docs/product/risk-register.md)
- [Glossary](docs/product/glossary.md)
- [Architecture decisions](docs/decisions/README.md)
- [Delivery roadmap](docs/product/delivery-roadmap.md)
