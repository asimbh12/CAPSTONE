# Stage 4 onboarding test guide

1. Open <http://127.0.0.1:5173> and choose **Import career**.
2. Select a public-information CV in PDF, DOCX, or TXT format, or enter an accessible public
   professional URL. For broader coverage, add two to ten typed URLs such as an institutional
   profile, ORCID, Google Scholar, personal website, or media profile and analyse them together.
3. Choose **Local only** for deterministic extraction, or **AI allowed** when Gemini has been
   configured and the content is eligible to leave the computer.
4. Confirm the public-information declaration and analyse the source.
5. Review and edit every proposed profile field and career asset. Clear **Include this career
   asset** for anything that should not be imported.
6. Apply the proposal, then verify **Profile & goals**, **Career assets**, and **Timeline**.

The workspace shows the active provider and model, retains recent analyses, and supports saving
manual corrections, reprocessing an eligible source, and suppressing an unwanted proposal.
Open a career asset and choose **AI enrich** to merge derived tags and themes without modifying
the user-authored title, description, dates, role, or impact statement. Provider operations record
status and character counts for troubleshooting without logging source bodies or API keys.

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
