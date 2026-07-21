# System Architecture

## Context

```mermaid
flowchart LR
    User["Local user"] -->|"Browser on localhost"| UI["CAPSTONE web interface"]
    UI --> API["CAPSTONE API"]
    API --> DB[("SQLite metadata and structured data")]
    API --> FS["Local document repository"]
    API --> AI["AI provider adapter"]
    AI -->|"Only permitted, minimised content"| Gemini["Gemini API"]
    API --> Export["DOCX, PDF and JSON outputs"]
```

CAPSTONE is deployed locally with Docker Compose. The browser interface communicates only with the local API. The API owns persistence, scoring, document processing, AI policy enforcement, and generation.

## Container view

```mermaid
flowchart TB
    subgraph Windows["Windows host"]
        Browser["Browser"]
        subgraph Compose["Docker Compose"]
            Web["React + TypeScript + Vite + Material UI"]
            Api["FastAPI + SQLModel + Alembic"]
        end
        Data[("SQLite volume")]
        Original["Original document volume"]
        Derived["Extracted and generated document volume"]
        Secrets["Local environment secrets"]
    end
    Browser --> Web
    Web --> Api
    Api --> Data
    Api --> Original
    Api --> Derived
    Secrets --> Api
    Api --> Gemini["Gemini API"]
```

## Backend modules

```mermaid
flowchart LR
    HTTP["API routes"] --> Application["Application services"]
    Application --> Profile["Profiles and goals"]
    Application --> Assets["Assets and evidence"]
    Application --> Opportunities["Opportunities and scoring"]
    Application --> Targets["Targets and readiness"]
    Application --> Jobs["Job applications"]
    Application --> Imports["Import/export"]
    Application --> Documents["Document processing/generation"]
    Application --> Intelligence["AI orchestration"]
    Intelligence --> Policy["AI data-policy gate"]
    Policy --> Provider["Provider-neutral AI interface"]
    Provider --> Gemini["Gemini adapter"]
    Application --> Persistence["Repositories / unit of work"]
    Persistence --> SQLite[("SQLite")]
    Documents --> Files["Local filesystem"]
    Application --> Audit["Audit service"]
```

Module boundaries are logical within a modular monolith. A distributed architecture would add operational cost without helping the single-user MVP.

## Repository structure

```text
CAPSTONE/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── migrations/
│   └── tests/
├── frontend/
│   ├── src/
│   └── tests/
├── data/
│   ├── originals/
│   ├── derived/
│   ├── generated/
│   ├── imports/
│   └── backups/
├── schemas/
├── docs/
├── tests/e2e/
├── docker-compose.yml
└── README.md
```

Runtime data directories will be ignored by Git. Placeholder files may preserve the intended directory structure.

## Key data flows

### Asset ingestion

```mermaid
sequenceDiagram
    actor U as User
    participant W as Web UI
    participant A as API
    participant F as Local files
    participant D as SQLite
    participant G as AI policy/provider

    U->>W: Enter asset and upload evidence
    W->>A: Submit facts, file, AI policy
    A->>A: Validate public-information acknowledgement
    A->>F: Preserve immutable original
    A->>D: Store asset, metadata, checksum, provenance
    alt AI policy permits
        A->>G: Send minimised eligible content
        G-->>A: Structured tags and suggestions
        A->>D: Store derived values and audit event
    end
    A-->>W: Return asset and enrichment status
```

### Job application

```mermaid
sequenceDiagram
    actor U as User
    participant W as Web UI
    participant A as API
    participant D as Career repository
    participant G as AI provider
    participant X as Export engine

    U->>W: Upload or paste job description
    W->>A: Create job application
    A->>G: Extract structured requirements
    G-->>A: Draft role and criteria
    A-->>W: Present for review
    U->>W: Confirm or edit requirements
    W->>A: Request evidence mapping and analysis
    A->>D: Select eligible assets and evidence
    A->>G: Analyse grounded fit and gaps
    G-->>A: Structured analysis with source references
    A-->>W: Display fit, readiness, gaps, and warnings
    U->>W: Request application documents
    A->>G: Generate from confirmed requirements and evidence
    G-->>A: Structured grounded draft
    A->>X: Render DOCX and PDF
    X-->>W: Preview and downloads
```

## Persistence rules

- SQLite contains structured domain data, extracted text where appropriate, metadata, stable relative paths, checksums, and audit data.
- Original document binaries are stored beneath `data/originals` and are not overwritten.
- Derived text and transformations are stored beneath `data/derived`.
- Generated application documents are stored beneath `data/generated`.
- Paths stored in the database are relative to a configurable data root to keep backups portable.
- File writes use staged temporary files and atomic moves where supported.
- Deleting a domain link does not silently delete an original document; retention is explicit.

## Technology baseline

| Concern | Selection |
|---|---|
| Frontend | React, TypeScript, Vite, Material UI |
| Backend | FastAPI, Python, SQLModel |
| Migration | Alembic |
| Database | SQLite for MVP |
| AI | Provider interface with Gemini adapter first |
| Backend tests | Pytest |
| Frontend tests | Vitest and Testing Library |
| End-to-end tests | Playwright |
| Local deployment | Docker Compose on Windows |
| Documents | Local filesystem; metadata in SQLite |
| Export | DOCX, PDF, versioned JSON |

## Future compatibility

The MVP does not implement multi-tenancy, but domain identifiers and repository boundaries should avoid assumptions that prevent later migration to PostgreSQL and authenticated users. Premature `user_id` and `workspace_id` columns will not be added everywhere until their semantics are designed in the multi-user phase.

