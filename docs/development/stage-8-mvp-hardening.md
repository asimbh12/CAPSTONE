# Stage 8 — MVP hardening

Stage 8 turns the completed feature work into a testable local MVP. It does not add the deferred
multi-user, authentication or cloud-deployment scope.

## Integrated dashboard

The Overview page now obtains a single consistent dashboard snapshot from `GET /api/dashboard`.
It displays system-wide metrics and deterministic next-best actions. Actions are sorted by a
stable priority score and point to the relevant workspace.

The rules prioritise:

1. opportunities closing within 14 days;
2. missing profile or career-evidence foundations;
3. unconfirmed job requirements and unmapped application evidence;
4. unassessed strategic goals and targets;
5. experience records missing impact summaries;
6. assets without evidence, opportunities without next actions and undrafted applications;
7. failed imports and backups older than seven days.

These recommendations do not call an AI provider and do not change data.

## Backup integrity and recovery

Every backup now receives two checks before the interface reports its result:

- every archived file is compared with the manifest byte size and SHA-256 checksum;
- the SQLite snapshot runs `PRAGMA integrity_check`.

`GET /api/data/backups/{filename}/verify` can recheck a stored backup. The manifest records
non-secret runtime metadata and explicitly states that secrets are excluded.

The automated recovery test extracts the SQLite snapshot into a clean temporary location, opens
it independently and confirms that saved profile data can be read.

## Stage 8 verification

Run the backend quality and test suite:

```powershell
cd backend
.\.venv\Scripts\ruff.exe check app tests --no-cache
.\.venv\Scripts\mypy.exe --no-incremental app
.\.venv\Scripts\python.exe -m pytest
```

Run the frontend checks:

```powershell
cd frontend
npm run lint
npm test -- --run
npm run build
```

Then start the production-like local containers:

```powershell
docker compose up -d --build
docker compose ps
```

Confirm:

1. Overview displays next-best actions in a sensible priority order.
2. Each **Open workspace** button navigates to the stated workspace.
3. Completing a workflow removes or lowers the corresponding action after Overview is reloaded.
4. **Data safety → Create and verify backup** reports checksum and SQLite integrity success.
5. The API and web containers remain bound to `127.0.0.1`.

See [Windows operations](windows-operations.md) for startup, recovery and troubleshooting.
