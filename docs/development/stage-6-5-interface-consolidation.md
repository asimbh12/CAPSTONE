# Stage 6.5 interface consolidation

Stage 6.5 is a focused usability pass between target readiness and job applications. It does
not change career data, scoring rules, ingestion behaviour, or AI authority.

## What changed

- Desktop navigation now remains visible in a compact left workspace rail.
- Small screens use a temporary navigation drawer.
- Page headings, spacing, cards, buttons, alerts, chips, and accordions use a shared visual
  hierarchy.
- Target readiness is presented as one expandable target summary at a time, with the target
  status, readiness score, progress, criteria, mappings, and assessment history grouped
  together.
- Import guidance is collapsed by default so the source controls remain the primary action.
- Timeline records are checked for possible near-duplicates using title, date, organisation,
  category, and role context. The user compares source and evidence detail, chooses the record to
  retain, and confirms before rejected records are archived; nothing is permanently deleted.
- API and local-workspace status remain visible without competing with page content.

## Usability baseline

The interface should support these behaviours before Stage 7 begins:

1. A user can identify the current workspace and move to another one without returning to the
   overview.
2. Each page starts with its purpose and primary action before detailed records.
3. Long reference information and secondary detail use progressive disclosure.
4. Dense records remain readable at desktop widths and navigation remains available on mobile.
5. Existing workflows and automated tests continue to work without data migration.

## Verification

Run the frontend checks:

```powershell
cd frontend
npm run lint
npm test -- --run
npm run build
```

Then open <http://127.0.0.1:5173>, check the desktop navigation, reduce the browser width to
confirm the menu drawer appears, and review **Import career** and **Targets & readiness**.
