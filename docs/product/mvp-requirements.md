# CAPSTONE MVP Product Requirements

## 1. Purpose

CAPSTONE helps a professional answer:

> What is the highest-value action I should take next to maximise my long-term career objectives?

The MVP establishes a reusable career intelligence foundation and validates three workflows:

1. Capturing and reusing career assets.
2. Ranking career opportunities.
3. Analysing jobs and generating grounded application material.

## 2. Product principles

1. **Every career event becomes reusable strategic capital.** Information is stored once and reused across analyses and documents.
2. **User facts remain authoritative.** AI must not overwrite user-entered facts, source documents, or adopted goals.
3. **Evidence precedes generation.** Generated claims must be grounded in selected career assets and evidence.
4. **Local first.** Source documents and application data remain on the user's Windows computer.
5. **Explainable recommendations.** Scores and recommendations expose their inputs and reasoning.
6. **Reversible AI enrichment.** AI may automatically manage derived tags and suggestions, but changes are logged and can be corrected.
7. **No autonomous applications.** CAPSTONE may discover or analyse an opportunity but never applies on the user's behalf.
8. **Career agnostic.** The common domain model must not assume an academic, corporate, government, defence, or healthcare career.

## 3. MVP user and operating context

- One local user.
- Windows host.
- Browser-based interface served locally.
- Docker Desktop and Docker Compose are the primary runtime.
- Native developer commands are also documented.
- Authentication and authorisation are disabled.
- Only publicly available professional information, up to official/public professional level, is permitted.
- Multi-user operation and cloud hosting are outside the MVP.

## 4. Functional scope

### 4.1 Career profile

The user can maintain:

- Name, current title, and organisation.
- Career mission and narrative.
- Professional themes.
- Short-, medium-, and long-term goals.
- Target roles, recognition, fellowships, awards, and leadership positions.
- AI-suggested career trajectories, which remain suggestions until adopted by the user.

### 4.2 Career asset repository

The user can create, view, edit, archive, search, filter, import, and export career assets. An asset contains:

- Title, description, category, optional subcategory, date or date range, and lifecycle status.
- Impact summary, organisation, role, visibility, keywords, and strategic themes.
- Links to evidence, documents, people, organisations, goals, targets, and opportunities.
- Provenance showing whether each value was user-entered, imported, extracted, or AI-derived.

The MVP supports all categories from the original vision through configurable reference data rather than hard-coded application logic.

### 4.3 Evidence and documents

- Upload PDF, DOCX, TXT, and JSON files.
- Store original files unchanged on the local filesystem.
- Store file metadata and stable relative paths in SQLite.
- Store extracted text, analysis, and generated outputs separately from originals.
- Calculate a checksum to support integrity checking and duplicate detection.
- Let the user set AI handling to `ai_allowed`, `local_only`, or `redacted`.
- Preview supported content and download originals.

### 4.4 AI enrichment

The initial AI implementation uses Gemini through a provider-neutral interface. It may:

- Apply and update derived tags and themes automatically.
- Suggest links between assets, goals, criteria, and opportunities.
- Extract structured information from permitted source content.
- Suggest target requirements and career trajectories.
- Summarise evidence and recommend next actions.

AI must not overwrite user-entered facts, original documents, or adopted goals. Derived changes must be auditable, reversible, and manually correctable.

### 4.5 Opportunity management and prioritisation

The user can add and manage jobs, awards, fellowships, grants, board roles, advisory roles, government appointments, industry opportunities, leadership opportunities, thought-leadership opportunities, media opportunities, and custom types.

Each opportunity supports:

- Title, description, type, organisation, URL, opening date, closing date, status, owner, next action, notes, and source.
- Strategic value from 1 to 5.
- Probability from 0 to 100 percent.
- Effort from 1 to 5.
- Deterministic base score and normalised display score.
- Deadline urgency displayed separately.
- AI-suggested values clearly distinguished from user-entered values.

The system produces a ranked list and explains every score.

### 4.6 User-defined targets and readiness

- The user can define a desired target or trajectory.
- A target has user-defined, weighted criteria.
- AI can suggest targets, requirements, milestones, timelines, and criteria.
- Suggestions do not become adopted goals or authoritative requirements until the user accepts or edits them.
- Career assets and evidence can be mapped to criteria.
- Readiness reports show strengths, gaps, supporting evidence, confidence, and recommended actions.

### 4.7 Job application workflow

The user can:

1. Upload a position description in PDF, DOCX, or TXT, or paste job text and an optional URL.
2. Extract role details and selection requirements for review.
3. Confirm or edit extracted requirements.
4. Map career assets and evidence to requirements.
5. View fit, readiness, gaps, and unsupported claims.
6. Generate:
   - A tailored cover letter.
   - Selection criteria responses.
   - A tailored CV.
   - Interview preparation notes.
7. Review generated content on screen.
8. Export generated documents as DOCX and PDF.

All generated factual claims must be linked internally to supporting evidence or explicitly marked as needing user confirmation.

### 4.8 Import and export

- Provide versioned JSON schemas and templates before importing real user data.
- Validate imports before changing stored data.
- Show a dry-run report with errors, warnings, duplicates, and proposed actions.
- Support explicit conflict resolution and idempotent re-import where practical.
- Export all structured user data in a documented JSON format.
- Initial real-world testing uses user-supplied public professional data.

### 4.9 Dashboard

The MVP dashboard shows:

- Career asset totals and recent growth.
- Highest-priority opportunities and approaching deadlines.
- Active job applications and next actions.
- Target readiness summaries.
- AI-generated recommended next actions with explanations.

## 5. Non-functional requirements

### 5.1 Security and privacy

- Bind local services to localhost by default.
- Do not collect or accept sensitive personal, health, classified, confidential employer, security-cleared, or private referee information.
- Show an entry-time warning and require confirmation that uploaded material is suitable.
- Keep secrets outside source control and stored data.
- Send content to AI only when its handling policy permits it.
- Never include unrelated records in an AI request.
- Record AI request metadata without logging secrets or unrestricted prompt content.

### 5.2 Reliability and integrity

- Use database migrations from the first schema.
- Preserve original documents immutably at application level.
- Use transactional writes for structured data.
- Provide backup and restore instructions before real seed data is loaded.
- Maintain an audit history for user-important and AI-derived changes.

### 5.3 Explainability

- Every score exposes its inputs and formula.
- Every generated factual claim identifies supporting sources internally.
- AI suggestions are visually distinguishable from user-adopted decisions.
- Confidence must not be represented as objective probability unless calibrated.

### 5.4 Accessibility and usability

- Target WCAG 2.2 AA for the local web interface.
- Support keyboard navigation, meaningful focus states, labels, and sufficient colour contrast.
- Use responsive layouts for common desktop and tablet widths; mobile is supported for viewing but is not the primary MVP target.

### 5.5 Testability

- Backend: Pytest.
- Frontend units/components: Vitest and Testing Library.
- End-to-end workflows: Playwright.
- AI calls: deterministic contract fixtures and mocks in automated tests.
- Migration, import, scoring, evidence grounding, and export paths require automated coverage.

## 6. Explicitly out of scope

- User accounts, authentication, teams, and workspaces.
- Cloud deployment and cross-device synchronisation.
- PostgreSQL deployment, while avoiding needless SQLite-specific coupling.
- Live email ingestion, RSS monitoring, and general web crawling.
- Automatic applications or external submissions.
- Model training on user data.
- A dedicated graph database.
- Full network CRM, defence influence, grants, honours, awards, and fellowship dashboards.
- Native mobile or desktop applications.

## 7. Assumptions requiring validation during delivery

- Docker Desktop is available on the target Windows machine.
- Gemini free-tier limits are adequate for workflow testing.
- DOCX and PDF rendering can remain faithful enough for initial templates.
- Public professional data is sufficient to exercise grounding and readiness features.
- The user understands that approved content sent to Gemini leaves the local system for processing.

