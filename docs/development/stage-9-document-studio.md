# Stage 9 — Career Document Studio

Stage 9 begins the post-MVP document-generation engine. Its first slice creates reusable career
communications independently of a job application.

## Delivered document types

- Professional biography
- Executive profile
- LinkedIn About section

The user selects the intended audience, purpose and tone. Generation uses the career profile and
active career assets, records the exact asset identifiers used, and never updates those sources.
Gemini is used when configured; otherwise a deterministic grounded draft keeps the workflow
testable offline. Requests that lack verified support are returned as evidence limitations instead
of being invented.

Each generated document is stored locally, remains editable on screen, and can be exported as
DOCX or PDF. Saving an edited draft creates an audit event without overwriting its source assets.

## Test workflow

1. Open **Document studio**.
2. Choose a document type, audience, purpose and tone.
3. Generate the draft and confirm that its source-asset count is shown.
4. Review and edit the document, then save it.
5. Download both DOCX and PDF and check their layout.
