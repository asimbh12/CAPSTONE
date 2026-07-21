# Stage 4 onboarding test guide

For comprehensive extraction, use **AI allowed** (the default). Gemini analyses document text
and uses URL Context for public pages, including JavaScript-rendered pages that expose little
text to CAPSTONE's local reader. The review screen reports retrieval method, locally visible
character count, and input quality.

**Local only** never sends source content to Gemini. It is intentionally limited to dated text
entries and will not comprehensively interpret undated achievements, qualifications,
publications, grants, or document structure. DOCX paragraph and table text are both preserved.
For LinkedIn and access-controlled sites, upload a public profile PDF/export because automated
page retrieval may be blocked.

Deakin Experts profile URLs are expanded automatically into the profile, research outputs,
research/grants, professional activities, and teaching/supervision sections. Each section is
analysed separately, duplicates are merged, and the supporting section URL is retained on each
proposed asset.

Google Scholar profiles are expanded into 100-result pages (up to 1,000 results), stopping after
the first empty continuation page. Other public profile hubs are inspected for relevant
same-profile sections and pagination links with a 20-page safety limit. Every analysed page is
retained in the source manifest for coverage review and repeatable reprocessing.

1. Open <http://127.0.0.1:5173> and choose **Import career**.
2. Select a public-information CV in PDF, DOCX, or TXT format, or enter an accessible public
   professional URL. For broader coverage, add two to ten typed URLs such as an institutional
   profile, ORCID, Google Scholar, personal website, or media profile and analyse them together.
3. Keep **AI allowed** for comprehensive analysis when the content is eligible to leave the
   computer, or choose **Local only** for limited deterministic extraction.
4. Confirm the public-information declaration and analyse the source.
5. Review and edit every proposed profile field and career asset. Clear **Include this career
   asset** for anything that should not be imported.
6. Apply the proposal, then verify **Profile & goals**, **Career assets**, and **Timeline**.

The workspace shows the active provider and model, retains recent analyses, and supports saving
manual corrections, reprocessing an eligible source, and suppressing an unwanted proposal.
Open a career asset and choose **AI enrich** to merge derived tags and themes without modifying
the user-authored title, description, dates, role, or impact statement. Provider operations record
status and character counts for troubleshooting without logging source bodies or API keys.

Profile URL diagnostics are appended to `data/logs/profile-ingestion.jsonl`. The JSONL records
page discovery, local retrieval outcomes, Gemini retrieval diagnostics, warnings, asset counts,
pagination stop reasons, timings and final coverage. Source page contents and credentials are not
logged. Development verification output is retained in `data/logs/development-testing.log`.

Multi-source analysis extracts each URL independently and then creates one consolidated proposal.
The review shows coverage by source type, source labels for each proposed asset, deduplicated
overlaps, and conflicts between profile values. Applying the proposal creates separate evidence
links back to every supporting public source. Reprocessing repeats the entire saved URL collection.

Existing user-authored profile values are never overwritten. Duplicate asset titles are skipped.
Original uploaded documents remain under the local `data/originals` directory and SQLite stores
their metadata. LinkedIn should be supplied as a downloaded profile PDF or data export because
automated scraping is intentionally unsupported.

## Gemini configuration

Copy `.env.example` to `.env`, set `CAPSTONE_AI_PROVIDER=gemini`, and add a free-tier
`CAPSTONE_GEMINI_API_KEY`. Restart Docker Compose after changing configuration. The default model
is configurable through `CAPSTONE_GEMINI_MODEL`. Never commit `.env`.
