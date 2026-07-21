$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Assert-LastCommandSucceeded {
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE."
    }
}

Push-Location "$root\backend"
try {
    & ".venv\Scripts\ruff.exe" check .
    Assert-LastCommandSucceeded
    & ".venv\Scripts\mypy.exe" app
    Assert-LastCommandSucceeded
    & ".venv\Scripts\pytest.exe"
    Assert-LastCommandSucceeded
    & ".venv\Scripts\alembic.exe" upgrade head
    Assert-LastCommandSucceeded
    & ".venv\Scripts\alembic.exe" check
    Assert-LastCommandSucceeded
}
finally {
    Pop-Location
}

Push-Location "$root\frontend"
try {
    npm.cmd run lint
    Assert-LastCommandSucceeded
    npm.cmd run test
    Assert-LastCommandSucceeded
    npm.cmd run build
    Assert-LastCommandSucceeded
}
finally {
    Pop-Location
}

Write-Host "Static analysis, tests, build, and migration checks passed."
