# Stage 7 — Job applications

## What is included

- Choose a dedicated paste-text or upload-document path for a public position description.
- Upload PDF, DOCX, or TXT files up to 20 MB; originals remain in local storage.
- Extract a reviewable requirement proposal without changing career records.
- Require explicit confirmation before evidence mapping.
- Automatically map active career assets and calculate fit and evidence confidence.
- Show strengths, gaps, explanations, and recommendations.
- Generate comprehensive, role-specific cover letter, selection criteria, tailored CV, and
  interview notes with Gemini; use an explicitly labelled local fallback if Gemini is unavailable.
- Show evidence limitations reported during drafting and replace earlier drafts when regenerating.
- Export the latest materials as a combined DOCX or PDF application pack.

## Interactive test

1. Open `http://127.0.0.1:5173` and choose **Job applications**.
2. Enter a role title and organisation.
3. Select **Paste position description** or **Upload position document**. Paste the complete text,
   or choose a PDF, DOCX, or TXT file.
4. Confirm it contains only public professional information and select **Import and extract requirements**.
5. Review the proposed requirement list. Select **Confirm requirements** only when it accurately represents the position description.
6. Select **Map evidence & assess**. Expand each requirement to inspect its mapped asset count, coverage, confidence, and explanation.
7. Inspect the overall fit, strengths, and evidence gaps. A gap means the current career inventory lacks sufficiently related evidence; it is not proof that the user lacks the capability.
8. Select **Generate drafts**. Review all four tabs and verify that no claim extends beyond the mapped career evidence.
9. Download both **DOCX** and **PDF** and inspect every page before using the material externally.

## Guardrails

- Uploaded originals remain in local storage; SQLite holds application metadata and extracted working text.
- Requirements remain proposals until the user confirms them.
- Evidence mapping is additive and never overwrites user-provided career assets.
- Drafts explicitly mark evidence gaps and do not fabricate replacement examples.
- Generated application materials are working drafts and require user review before submission.

## Automated verification

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m mypy app
.\.venv\Scripts\python.exe -m ruff check app tests
```

Frontend:

```powershell
cd frontend
npm.cmd run lint
npm.cmd test -- --run
npm.cmd run build
```
