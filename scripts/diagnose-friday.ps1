[CmdletBinding()]
param(
    [switch]$RunPytest
)

$ErrorActionPreference = "Continue"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Backend = Join-Path $RepoRoot "Friday_OS\Backend"
$VenvPython = Join-Path $Backend ".venv\Scripts\python.exe"

Write-Host "=== FridayOS local diagnostic (read-only) ===" -ForegroundColor Cyan
Write-Host "Repository: $RepoRoot"

Push-Location $RepoRoot
try {
    Write-Host ""
    Write-Host "--- Git ---" -ForegroundColor Yellow
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git status --short --branch
        git log -1 --oneline
    } else {
        Write-Warning "Git is not installed or not on PATH."
    }

    Write-Host ""
    Write-Host "--- Runtime versions ---" -ForegroundColor Yellow
    foreach ($command in @("python", "py", "node", "npm", "wsl")) {
        $resolved = Get-Command $command -ErrorAction SilentlyContinue
        if ($resolved) {
            if ($command -eq "py") {
                & py -3.12 --version 2>&1
            } else {
                & $command --version 2>&1
            }
        } else {
            Write-Host "$command : not found"
        }
    }

    Write-Host ""
    Write-Host "--- Python environment ---" -ForegroundColor Yellow
    $Python = $null
    if (Test-Path $VenvPython) {
        $Python = $VenvPython
        Write-Host "Using backend virtual environment: $VenvPython"
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        $Python = (Get-Command python).Source
        Write-Warning "Backend .venv not found; using PATH Python for diagnostics only."
    }

    if ($Python) {
        & $Python --version
        Write-Host "Installed package consistency:"
        & $Python -m pip check

        Write-Host "Direct-import availability:"
        $Modules = @(
            "livekit", "dotenv", "psutil", "pyautogui", "pyperclip",
            "win32gui", "rapidfuzz", "playwright", "chardet", "chromadb",
            "pypdf", "sqlalchemy", "langchain_community", "apscheduler",
            "watchdog", "pydantic", "mcp"
        )
        $env:FRIDAY_DIAGNOSTIC_MODULES = $Modules -join ","
        & $Python -c "import importlib.util, os; names=os.environ['FRIDAY_DIAGNOSTIC_MODULES'].split(','); [print(n + ': ' + ('OK' if importlib.util.find_spec(n) else 'MISSING')) for n in names]"
        Remove-Item Env:FRIDAY_DIAGNOSTIC_MODULES -ErrorAction SilentlyContinue

        if ($RunPytest) {
            Write-Host ""
            Write-Host "--- Pytest ---" -ForegroundColor Yellow
            & $Python -m pytest -q
            Write-Host "Pytest exit code: $LASTEXITCODE"
        }
    } else {
        Write-Warning "No Python interpreter found."
    }

    Write-Host ""
    Write-Host "--- Configuration presence (values are never printed) ---" -ForegroundColor Yellow
    $EnvFile = Join-Path $RepoRoot ".env"
    if (Test-Path $EnvFile) {
        Write-Host ".env exists. Secret values were not read or displayed."
        $Names = Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=') { $Matches[1] }
        } | Sort-Object -Unique
        Write-Host ("Variable names: " + ($Names -join ", "))
    } else {
        Write-Host ".env not found at repository root."
    }

    Write-Host ""
    Write-Host "Diagnostic complete. This script does not install packages, change files, start services, or display secret values." -ForegroundColor Green
}
finally {
    Pop-Location
}
