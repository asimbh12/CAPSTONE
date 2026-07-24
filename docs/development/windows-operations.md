# CAPSTONE Windows operations

## Prerequisites

- Windows 11 or a supported Windows 10 release
- Docker Desktop using Linux containers
- Git
- At least 4 GB of free disk space for images, backups and local documents

CAPSTONE is a single-user local application. The default Compose configuration exposes the web
application and API only on `127.0.0.1`.

## First start

Open PowerShell in the repository:

```powershell
cd "D:\AI Projects\CAPSTONE"
docker compose up -d --build
docker compose ps
```

Both services should become healthy. Open <http://127.0.0.1:5173>. API readiness is available at
<http://127.0.0.1:8000/api/health/ready>.

Gemini configuration belongs in the repository `.env` file. Never place an API key in source
files, exported JSON, screenshots or support logs.

## Routine operation

Start:

```powershell
docker compose up -d
```

Stop without deleting local data:

```powershell
docker compose down
```

Inspect status and recent logs:

```powershell
docker compose ps
docker compose logs --tail 200 api
docker compose logs --tail 200 web
```

The `data` directory contains the SQLite database and locally stored documents. Do not manually
edit these files while CAPSTONE is running.

## Create and verify a backup

Open **Data safety**, select **Create and verify backup**, and wait for:

- `Backup verified`
- SQLite integrity `ok`
- a non-zero checked-file count

Download the ZIP to another local drive or an approved secure backup location. The archive
contains a checksum manifest, a consistent database snapshot, and original/derived/generated
files. API keys are deliberately excluded.

## Restore a backup

Restoration replaces local application data, so retain the current data directory until the
restored instance has been checked.

1. In **Data safety**, verify the selected stored backup.
2. Stop CAPSTONE with `docker compose down`.
3. Rename `data` to a clearly dated recovery folder such as `data-before-restore-20260724`.
4. Extract the backup ZIP into a new temporary folder.
5. Create a new `data` directory.
6. Copy `database/capstone.db` from the extracted backup to `data/capstone.db`.
7. Copy any extracted `originals`, `derived`, and `generated` folders into the new `data`
   directory without changing their relative paths.
8. Start CAPSTONE with `docker compose up -d`.
9. Confirm the dashboard counts, profile, career assets, evidence downloads and applications.
10. Create and verify a fresh backup of the restored instance.

If validation fails, stop CAPSTONE, remove only the newly restored `data` directory and rename the
dated recovery folder back to `data`.

## Troubleshooting

### API unavailable

Run `docker compose ps` and inspect `docker compose logs --tail 200 api`. A healthy API must answer
the readiness URL. If the database is locked, ensure no second CAPSTONE stack or SQLite editor is
using `data/capstone.db`.

### Browser reports CORS or failed fetch

Use exactly <http://127.0.0.1:5173> or <http://localhost:5173>. Rebuild both services after
configuration changes:

```powershell
docker compose up -d --build --force-recreate
```

### Gemini unavailable

CAPSTONE remains usable for local data entry and deterministic workflows. Confirm that `.env`
contains the provider, model and API key, then recreate the API container. Provider errors should
appear in the interface without removing user-entered data.

### Port already in use

Check whether another CAPSTONE Compose project is running. Stop the duplicate stack instead of
changing the localhost binding unless the application configuration is updated consistently.

### Backup verification fails

Do not restore that archive. Create a new backup. If repeated backups fail, inspect free disk
space, file permissions and API logs before modifying the existing data directory.
