param(
    [string]$TaskName = "BuffotteDailyReport",
    [string]$PythonExe = "$PWD\.venv\Scripts\python.exe",
    [string]$ScriptPath = "$PWD\src\run_daily_report.py",
    [string]$StartTime = "23:58"
)

# Register a scheduled task to run the project's python script daily at specified time.
# Usage (PowerShell elevated):
# .\register_schtask.ps1 -TaskName "BuffotteDailyReport" -PythonExe "C:\path\to\python.exe" -ScriptPath "C:\path\to\run_daily_report.py" -StartTime "23:58"

# Require elevated privileges because registering a task for SYSTEM requires admin rights
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as Administrator to register a task under SYSTEM. Please re-run PowerShell as Administrator and try again."
    exit 1
}

$action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$principal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -RunLevel Highest
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Force -ErrorAction Stop
    Write-Output "Scheduled task '$TaskName' successfully registered to run $ScriptPath at $StartTime daily."
} catch {
    Write-Error "Failed to register scheduled task '$TaskName': $_"
    exit 1
}
