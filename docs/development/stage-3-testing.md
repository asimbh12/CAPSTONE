# Stage 3 Testing Guide

## Interactive workflow

Run CAPSTONE and open <http://127.0.0.1:5173>.

1. Open **Profile & goals** and save a public professional profile.
2. Add one or more professional themes and strategic goals.
3. Open **Career assets** and add a dated asset with an impact summary.
4. Search by part of its title or description and filter by category.
5. Open the asset, add URL evidence, then attach a small PDF, DOCX, TXT, or JSON file.
6. Confirm the public-information declaration and retain `Local only` for the first test.
7. Open **Timeline** and verify the dated asset appears chronologically.
8. Open **Data safety**, export JSON, run a dry-run import with the template, and create a backup.

Do not use real seed data until backup creation, download, and an offline restore test have succeeded.

## Automated verification

```powershell
.\scripts\verify.ps1
npm.cmd run e2e
```

## Offline restore test

Stop CAPSTONE and restore a backup explicitly:

```powershell
docker compose down
.\scripts\restore-backup.ps1 -BackupPath .\data\backups\capstone-backup-YYYYMMDDTHHMMSSZ.zip -ConfirmRestore
docker compose up --build
```

The script verifies the manifest and every file checksum, requires the containers to be stopped, and preserves the current database/documents under `data/pre-restore-*` before replacing them.

