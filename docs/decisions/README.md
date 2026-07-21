# Architecture Decision Log

| ID | Decision | Status |
|---|---|---|
| ADR-001 | Use a local modular monolith | Accepted |
| ADR-002 | Use SQLite with Alembic migrations | Accepted |
| ADR-003 | Store documents locally and metadata in SQLite | Accepted |
| ADR-004 | Use a provider-neutral AI boundary with Gemini first | Accepted |
| ADR-005 | Allow reversible automatic AI enrichment without overwriting user facts | Accepted |
| ADR-006 | Model graph relationships relationally for the MVP | Accepted |
| ADR-007 | Use deterministic opportunity scoring with separate urgency | Accepted |
| ADR-008 | Restrict MVP data to public professional information | Accepted |

## ADR-001: Local modular monolith

**Decision:** Use a React frontend and FastAPI modular-monolith backend, operated locally through Docker Compose.

**Why:** The MVP has one user and one deployment boundary. A modular monolith keeps transactions, development, backup, and debugging simple while retaining internal domain boundaries.

**Consequences:** Modules must communicate through application services rather than database shortcuts. Independent services can be extracted later only if operational needs justify them.

## ADR-002: SQLite and Alembic

**Decision:** Use SQLite for the MVP and Alembic for schema migrations.

**Why:** SQLite is sufficient for a local single-user product; Alembic is compatible with SQLModel/SQLAlchemy and supplies explicit, testable schema evolution.

**Consequences:** Avoid unnecessary SQLite-only SQL. A future multi-user release will require a planned PostgreSQL migration and concurrency review.

## ADR-003: Local document storage

**Decision:** Preserve document binaries on the local filesystem and store metadata and relative paths in SQLite.

**Why:** This supports local control, portable backup, and avoids inflating the relational database.

**Consequences:** Database and files must be backed up and restored as one consistent data set. Checksums and missing-file diagnostics are required.

## ADR-004: Provider-neutral AI

**Decision:** Define task-oriented AI contracts and implement Gemini first.

**Why:** Gemini's free tier supports early testing, while CAPSTONE is expected to move to a more comprehensive provider later.

**Consequences:** Domain and workflow code cannot import a provider SDK. Provider capabilities and structured-output differences are isolated in adapters.

## ADR-005: Automatic but reversible enrichment

**Decision:** AI can apply derived tags and themes without approval but cannot overwrite user-authoritative data.

**Why:** Automatic enrichment supplies the intended value without creating a review bottleneck.

**Consequences:** Provenance, auditing, manual corrections, suppressions, and safe re-enrichment semantics are mandatory.

## ADR-006: Relational knowledge graph

**Decision:** Use explicit relational associations and a constrained generic link facility rather than a graph database.

**Why:** MVP relationship queries are well served by SQLite, and a second persistence technology would add disproportionate complexity.

**Consequences:** Graph visualisations are projections from relational data. Revisit only if measured query patterns justify it.

## ADR-007: Opportunity scoring

**Decision:** Use strategic value 1–5, probability 0–100, effort 1–5, normalise the formula to 0–100, and show urgency separately.

**Why:** The calculation is transparent and stable while avoiding a hidden deadline modifier.

**Consequences:** AI may suggest input values, but it cannot directly assign the computed result. Algorithm versions are retained.

## ADR-008: Public professional data only

**Decision:** The MVP must reject or warn against sensitive, confidential, classified, or private data and is designed only for public professional information.

**Why:** This limits testing risk while privacy, authentication, and production security are intentionally deferred.

**Consequences:** Entry warnings, content policies, AI transmission controls, and safe logging are still required. This is risk reduction, not a guarantee that users cannot enter prohibited content.

