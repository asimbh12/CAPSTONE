$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Push-Location "$root\backend"
try {
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }
    & ".venv\Scripts\python.exe" -m pip install --upgrade pip
    & ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
    New-Item -ItemType Directory -Force -Path "data" | Out-Null
    & ".venv\Scripts\alembic.exe" upgrade head
}
finally {
    Pop-Location
}

Push-Location "$root\frontend"
try {
    npm.cmd install
}
finally {
    Pop-Location
}

Push-Location $root
try {
    npm.cmd install
}
finally {
    Pop-Location
}

Write-Host "CAPSTONE development dependencies are installed."

