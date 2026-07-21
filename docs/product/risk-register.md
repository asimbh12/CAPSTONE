# MVP Risk Register

| ID | Risk | Likelihood | Impact | Initial treatment | Owner |
|---|---|---:|---:|---|---|
| R-01 | A user enters sensitive or confidential information despite warnings. | Medium | High | Restrict scope, warn at every ingestion boundary, provide AI policies, add detection warnings, and minimise external requests. | Product/engineering |
| R-02 | AI invents, exaggerates, or misattributes a career claim. | Medium | High | Require evidence identifiers for factual claims, flag unsupported content, validate structured output, and require document review. | Engineering |
| R-03 | Gemini free-tier limits or model changes disrupt testing. | High | Medium | Provider abstraction, retries/backoff, visible degradation, usage limits, mock provider, and provider contract tests. | Engineering |
| R-04 | Database and filesystem backups become inconsistent. | Medium | High | Coordinated backup procedure, relative paths, checksums, manifest, restore test, and staged file operations. | Engineering |
| R-05 | DOCX/PDF extraction or rendering loses structure. | Medium | Medium | Preserve originals, expose extracted text for review, use fixtures from representative documents, and visually verify exports. | Engineering/product |
| R-06 | Automated tags recreate values the user deliberately removed. | Medium | Medium | Store provenance and suppression records; do not re-add without new evidence or explicit reset. | Engineering |
| R-07 | Opportunity/readiness scores appear more objective than their inputs justify. | Medium | Medium | Explain formula and inputs, separate confidence and urgency, label estimates, and support user edits. | Product |
| R-08 | Real seed data is loaded before backup, schema, and AI controls are safe. | Medium | High | Complete versioned template, validation, backup/restore, and AI-policy tests before loading the dataset. | Product/engineering |
| R-09 | SQLite or the local modular design becomes embedded in domain logic. | Low | Medium | Repository boundaries, Alembic migrations, portable types, and no unnecessary SQLite-specific SQL. | Engineering |
| R-10 | Local services are accidentally exposed to the network. | Low | High | Bind to loopback by default, document overrides, and add deployment checks. | Engineering |
| R-11 | Public web content contains prompt injection or hostile instructions. | Medium | High | Treat imported content as data, never as instructions; delimit sources; use narrow structured contracts and output validation. | Engineering |
| R-12 | Scope expands into later specialist modules before core workflows are validated. | Medium | Medium | Use the accepted MVP boundary and roadmap exit gates; route new ideas to the deferred backlog. | Product |

## Review cadence

Review the register at each delivery-stage exit and whenever an AI provider, storage model, deployment boundary, or accepted data class changes. A risk rated high impact must have a tested control before the affected workflow uses real data.
