# MVP Acceptance Criteria

## Definition of done

A capability is complete when its agreed behaviour is implemented, accessible, validated, covered by proportionate automated tests, documented, and does not leave known high-severity defects.

## AC-01 Local startup

- Given a supported Windows machine with Docker Desktop, when the documented startup command is run, the frontend and API become available on localhost.
- No authentication is requested.
- No service binds to a non-localhost interface by default.

## AC-02 Career profile

- The user can create and update mission, narrative, themes, goals, and targets.
- Reloading the application preserves the data.
- AI suggestions cannot silently replace adopted goals or user-entered fields.

## AC-03 Career assets

- The user can create, edit, archive, search, filter, import, and export an asset.
- An asset can link to evidence, documents, organisations, people, themes, goals, targets, and opportunities.
- User-entered and derived fields retain provenance.

## AC-04 Documents and evidence

- PDF, DOCX, TXT, and JSON files can be uploaded after the public-information warning is acknowledged.
- The original file is stored unchanged and has a checksum.
- SQLite contains metadata rather than document binary data.
- Extracted text and generated outputs are stored separately.
- Duplicate content is detected and reported.

## AC-05 AI handling policy

- Every source document has one of: `ai_allowed`, `local_only`, or `redacted`.
- `local_only` content is never included in an external AI request.
- `redacted` content is processed only after the configured redaction step.
- Requests contain only records required for the current operation.

## AC-06 Automatic enrichment

- With AI enabled, an eligible asset receives derived tags and themes.
- Automatic changes record provider, model, time, operation, and affected fields.
- The user can correct or remove a derived tag.
- Re-running enrichment does not overwrite user-entered facts.
- The application remains usable with AI disabled or unavailable.

## AC-07 Opportunity scoring

- Strategic value accepts integers 1–5, probability accepts 0–100, and effort accepts integers 1–5.
- Invalid and zero-effort inputs are rejected.
- The raw and normalised scores are deterministic and reproducible.
- The interface explains the formula and displays urgency separately.
- Ranking changes consistently when inputs change.

## AC-08 Targets and readiness

- The user can define a target and weighted criteria.
- AI can suggest a trajectory or criteria without automatically adopting them.
- Assets and evidence can be mapped to criteria.
- A readiness report identifies matched evidence, gaps, strengths, confidence, and actions.
- Changing criteria or evidence results in a versioned reassessment.

## AC-09 Job ingestion

- A job can be created from an uploaded PDF/DOCX/TXT file or pasted text, with an optional URL.
- Extracted role details and requirements are presented for review.
- The user can edit and confirm requirements before final analysis.
- The original job source remains preserved.

## AC-10 Job analysis

- Confirmed requirements can be mapped to career assets and evidence.
- Fit and readiness results show their contributing requirements and evidence.
- Missing evidence and unsupported assertions are explicitly identified.
- The analysis does not invent career claims.

## AC-11 Application generation

- The user can generate a tailored cover letter, selection criteria responses, tailored CV, and interview notes.
- Each factual claim has an internal evidence link or a visible confirmation warning.
- Content is reviewable on screen.
- Each output exports successfully to DOCX and PDF.
- Generated files do not modify source documents.

## AC-12 JSON import/export

- A versioned template is available before real seed data is loaded.
- Import provides a dry run with errors, warnings, duplicates, and proposed changes.
- Invalid records do not cause a partial silent import.
- Exported JSON validates against the documented schema.

## AC-13 Auditability

- Creation, material edits, import actions, AI-derived changes, scoring assessments, and document generation produce audit records.
- API keys, document bodies, and unrestricted prompts are not written to audit logs.

## AC-14 Backup and recovery

- The user can back up the SQLite database, original documents, derived files, and configuration metadata together.
- A documented restore test recreates a working local instance.

## Release gate

The MVP is releasable only when AC-01 through AC-14 pass, migration tests pass from an empty database, the three priority workflows pass end-to-end, and no unresolved critical/high security or data-loss defect remains.

