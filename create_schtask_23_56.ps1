<#
Create a Windows Scheduled Task to run run_daily_report.py every day at 23:56.

Usage (run as Administrator to create task for SYSTEM):
  # create as SYSTEM (no password required, but network access may be limited)
  .\create_schtask_23_56.ps1 -RunAsSystem

  # create under current user (interactive, will prompt for credentials if needed)
  .\create_schtask_23_56.ps1

Options:
  -RunAsSystem: create the task to run as SYSTEM account (may have limited network access)
  -TaskName: override default task name
  -PythonExe: full path to python.exe to use (defaults to current python)
  -WorkDir: working directory containing run_daily_report.py (defaults to script dir)
#>

param(
    [switch]$RunAsSystem,
    [string]$TaskName = 'Buffotte_Daily_Report',
    [string]$PythonExe = '',
    [string]$WorkDir = ''
)

if (-not $PythonExe) {
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        Write-Error "python not found in PATH. Provide -PythonExe full path to python.exe"
        exit 1
    }
}

if (-not $WorkDir) {
    $WorkDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

$scriptPath = Join-Path $WorkDir 'run_daily_report.py'
if (-not (Test-Path $scriptPath)) {
    Write-Error "run_daily_report.py not found at $scriptPath"
    exit 1
}

$action = "`"$PythonExe`" `"$scriptPath`""

if ($RunAsSystem) {
    schtasks /Create /TN $TaskName /TR $action /SC DAILY /ST 23:56 /F /RL HIGHEST /RU SYSTEM | Out-Null
    Write-Host "Created scheduled task '$TaskName' to run as SYSTEM at 23:56 daily."
} else {
    # create under current user
    schtasks /Create /TN $TaskName /TR $action /SC DAILY /ST 23:56 /F /RL HIGHEST | Out-Null
    Write-Host "Created scheduled task '$TaskName' under current user at 23:56 daily."
}

Write-Host "To verify: schtasks /Query /TN $TaskName /V /FO LIST"
