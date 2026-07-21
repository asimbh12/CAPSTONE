# Stage 5 opportunity testing

## What Stage 5 delivers

The Opportunities workspace records jobs, awards, fellowships, grants, board/advisory,
government, industry, leadership, thought-leadership, media, and custom opportunities. It
supports the full lifecycle from discovery to outcome, with a named owner, next action,
public source, organisation, notes, and opening/closing dates.

Priority is deterministic and reproducible. Version `opportunity-priority-v1` calculates:

`raw = (strategic value × probability / 100) ÷ effort`

`display = round(strategic value × probability ÷ (5 × effort), 1)`

Strategic value and effort use 1–5 scales; probability uses 0–100. An effort of zero and
out-of-range values are rejected. Every save creates a retained assessment record containing
the inputs, result, source (`user` or `ai`), explanation, timestamp, and algorithm version.
Deadline urgency is calculated separately and never changes the priority score.

## Interactive test

1. Start Docker Desktop, run `docker compose up -d --build`, and open
   <http://127.0.0.1:5173>.
2. Select **Opportunities**, then **Add opportunity**.
3. Create a test opportunity with strategic value 5, probability 80, and effort 2.
4. Confirm the ranked card displays `40/100` and explains the three inputs.
5. Add a closing date within three days and confirm a critical deadline chip appears without
   changing the score.
6. Add a second opportunity with a higher score and confirm it appears at rank 1.
7. Filter by type and status, edit the next action and lifecycle status, and confirm the card
   updates.
8. Open **Overview** and confirm open-opportunity and closing-soon totals.
9. Archive the test opportunity and confirm it disappears from the default list.

Only enter publicly available professional information. Existing local career data remains
in the local SQLite database and documents remain in local storage.
