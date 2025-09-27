<#
deploy_windows.ps1

Helper to prepare a Windows host for running Buffotte daily:
  - create a Python venv under the repo (venv)
  - install requirements
  - optionally set environment variables for DB and SMTP (for current user)
  - create scheduled task to run run_daily_report.py at 23:56

Usage (run in an elevated PowerShell if you want SYSTEM task):
  cd E:\github\Buffotte
  .\deploy\deploy_windows.ps1

Arguments:
  -InstallDepsOnly: Only create venv and install dependencies
  -CreateTaskAsSystem: create scheduled task to run as SYSTEM (requires admin)

Note: This script writes environment variables for the current user using setx. If you prefer machine-level secure storage, use a secret manager.
#>

param(
    [switch]$InstallDepsOnly,
    [switch]$CreateTaskAsSystem
)

$repo = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $repo

if (-not (Test-Path "venv")) {
    Write-Host "Creating venv..."
    python -m venv venv
} else {
    Write-Host "venv already exists"
}

$py = Join-Path $repo "venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Python in venv not found at $py"
    Pop-Location
    exit 1
}

Write-Host "Installing requirements..."
& $py -m pip install --upgrade pip
& $py -m pip install -r requirements.txt

if ($InstallDepsOnly) {
    Write-Host "Dependencies installed. Exiting as requested."
    Pop-Location
    exit 0
}

Write-Host "Would you like to set environment variables for DB and SMTP now? (recommended)"
$ans = Read-Host "Set env vars now? (y/N)"
if ($ans -match '^[Yy]') {
    $db_uri = Read-Host "Enter SQLAlchemy DB URI (or leave blank to set BUFFOTTE_DB_URI later)"
    if ($db_uri) {
        setx BUFFOTTE_DB_URI "$db_uri"
        Write-Host "Set BUFFOTTE_DB_URI for current user"
    }
    $smtp_server = Read-Host "SMTP server (e.g. smtp.qq.com)"
    if ($smtp_server) {
        setx BUFFOTTE_SMTP_SERVER "$smtp_server"
        $smtp_port = Read-Host "SMTP port (e.g. 587)"
        if ($smtp_port) { setx BUFFOTTE_SMTP_PORT "$smtp_port" }
        $smtp_user = Read-Host "SMTP username"
        if ($smtp_user) { setx BUFFOTTE_SMTP_USERNAME "$smtp_user" }
        Write-Host "NOTE: For security, set BUFFOTTE_SMTP_PASSWORD manually or use a secure store."
    }
}

Write-Host "Creating scheduled task to run run_daily_report.py at 23:56"
$createScript = Join-Path $repo 'create_schtask_23_56.ps1'
if ($CreateTaskAsSystem) {
    & $createScript -RunAsSystem -PythonExe $py -WorkDir $repo
} else {
    & $createScript -PythonExe $py -WorkDir $repo
}

Write-Host "Deployment helper finished. Verify scheduled task with: schtasks /Query /TN Buffotte_Daily_Report /V /FO LIST"
Pop-Location
