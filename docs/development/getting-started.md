# Getting Started

## Prerequisites

- Windows 10 or 11.
- Docker Desktop with Docker Compose, for the primary local runtime.
- Node.js 24 and npm 11, for native frontend development.
- Python 3.12 or 3.13, for native backend development.

## Run with Docker Compose

From the repository root:

```powershell
docker compose up --build
```

Open:

- Web interface: <http://127.0.0.1:5173>
- API documentation: <http://127.0.0.1:8000/api/docs>
- API health: <http://127.0.0.1:8000/api/health>
- API readiness: <http://127.0.0.1:8000/api/health/ready>

Stop the application without deleting local data:

```powershell
docker compose down
```

The services bind to loopback only. Runtime data is stored beneath `data/` and is excluded from Git.

## Native development setup

From PowerShell at the repository root:

```powershell
.\scripts\setup.ps1
```

Start the API in one terminal:

```powershell
Set-Location backend
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the web interface in another terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

## Verification

Run backend and frontend static checks, tests, the production frontend build, and migration drift checks:

```powershell
.\scripts\verify.ps1
```

After setup, install Playwright's Chromium browser once and run the end-to-end smoke test:

```powershell
npx.cmd playwright install chromium
npm.cmd run e2e
```

## Database migrations

Application startup applies existing migrations but never creates migrations automatically. After an intentional model change:

```powershell
Set-Location backend
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe the change"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe check
```

Review every generated migration before committing it.

## Troubleshooting

- If Docker cannot read `%USERPROFILE%\.docker\config.json`, correct its Windows file permissions or restart Docker Desktop under the logged-in user.
- If port 5173 or 8000 is occupied, stop the conflicting local process before starting CAPSTONE.
- If the UI reports `API offline`, verify the API health URL directly and check CORS values in `.env` or Compose.
- Do not delete `data/` to fix a migration problem when real data is present. Back it up and diagnose the migration instead.

