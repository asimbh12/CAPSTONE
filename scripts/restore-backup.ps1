param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "Restore is destructive. Re-run with -ConfirmRestore after reviewing the backup path."
}

$root = [System.IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$dataRoot = [System.IO.Path]::GetFullPath((Join-Path $root "data"))
$backup = [System.IO.Path]::GetFullPath($BackupPath)
if (-not (Test-Path -LiteralPath $backup -PathType Leaf) -or [System.IO.Path]::GetExtension($backup) -ne ".zip") {
    throw "Backup must be an existing CAPSTONE ZIP file."
}

$running = docker compose -f (Join-Path $root "docker-compose.yml") ps --status running --quiet
if ($running) {
    throw "Stop CAPSTONE with 'docker compose down' before restoring a backup."
}

$restoreRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("capstone-restore-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $restoreRoot | Out-Null
try {
    Expand-Archive -LiteralPath $backup -DestinationPath $restoreRoot
    $manifestPath = Join-Path $restoreRoot "manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) { throw "Backup manifest is missing." }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    if ($manifest.backup_version -ne "1.0") { throw "Unsupported backup version." }

    foreach ($entry in $manifest.files) {
        $candidate = [System.IO.Path]::GetFullPath((Join-Path $restoreRoot $entry.path))
        if (-not $candidate.StartsWith([System.IO.Path]::GetFullPath($restoreRoot), [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe path found in backup manifest."
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Backup file is missing: $($entry.path)" }
        $actualHash = (Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualHash -ne $entry.sha256) { throw "Checksum mismatch: $($entry.path)" }
    }

    $snapshot = Join-Path $restoreRoot "database\capstone.db"
    if (-not (Test-Path -LiteralPath $snapshot)) { throw "Database snapshot is missing." }
    New-Item -ItemType Directory -Force -Path $dataRoot | Out-Null
    $safetyRoot = Join-Path $dataRoot ("pre-restore-" + (Get-Date -Format "yyyyMMddTHHmmss"))
    New-Item -ItemType Directory -Path $safetyRoot | Out-Null
    if (Test-Path -LiteralPath (Join-Path $dataRoot "capstone.db")) {
        Copy-Item -LiteralPath (Join-Path $dataRoot "capstone.db") -Destination $safetyRoot
    }
    foreach ($folder in @("originals", "derived", "generated")) {
        $current = Join-Path $dataRoot $folder
        if (Test-Path -LiteralPath $current) { Copy-Item -LiteralPath $current -Destination $safetyRoot -Recurse }
        $restored = Join-Path $restoreRoot $folder
        if (Test-Path -LiteralPath $restored) { Copy-Item -LiteralPath $restored -Destination $dataRoot -Recurse -Force }
    }
    Copy-Item -LiteralPath $snapshot -Destination (Join-Path $dataRoot "capstone.db") -Force
    Write-Host "CAPSTONE backup restored. Previous data was preserved at $safetyRoot"
}
finally {
    if ([System.IO.Path]::GetFullPath($restoreRoot).StartsWith([System.IO.Path]::GetTempPath(), [System.StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $restoreRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

