# CAPSTONE

**Career Advancement, Positioning, Strategy, Tracking, Opportunity Navigation and Excellence**

CAPSTONE is a local-first, AI-assisted career intelligence platform. It turns public professional achievements, experience, relationships, and supporting documents into reusable career assets for opportunity prioritisation and job applications.

The first release is a single-user Windows web application with no authentication. It uses a React/TypeScript frontend, FastAPI backend, SQLite database, local document storage, and a provider-neutral AI integration initially configured for Gemini.

## Current status

Stage 3 provides the first complete career-intelligence workflow: profile, goals, themes,
career assets, evidence and local documents, search/filtering, timeline generation, versioned
JSON import/export, audit events, and coordinated local backups.

## Run locally

With Docker Desktop running:

```powershell
docker compose up --build
```

Then open <http://127.0.0.1:5173>. See the
[development guide](docs/development/getting-started.md) for native setup and verification.

See the [Stage 3 testing guide](docs/development/stage-3-testing.md) for the interactive
career-asset and data-safety workflow.

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
