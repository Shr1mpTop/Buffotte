Windows Service (nssm / winsw) wrapping guide

This document explains how to run `run_daily_report.py` (or the fetch/send scripts) as a Windows Service using nssm (Non-Sucking Service Manager) or winsw.

nssm (recommended for simplicity):
1. Download nssm from https://nssm.cc/download and extract.
2. Copy `nssm.exe` to a folder in PATH or use full path.
3. Create a service:
   ```powershell
   nssm install BuffotteService "C:\Anaconda3\envs\buffotte\python.exe" "E:\github\Buffotte\run_daily_report.py"
   ```
4. Configure service details in nssm GUI: set working directory to `E:\github\Buffotte`, set stdout/stderr file to `E:\github\Buffotte\logs\buffotte.out.log`.
5. Start service:
   ```powershell
   nssm start BuffotteService
   ```

winsw (Java-based wrapper) alternative:
1. Download winsw (https://github.com/winsw/winsw/releases) and create an XML config pointing to your python exe and script.
2. Install and start service using the winsw executable.

Notes:
- Running as service requires the service account to have network and DB access. Prefer using a dedicated service account with minimal privileges.
- Logs: configure file rotation for stdout/stderr (nssm supports stdout/stderr file configuration).
- For scheduled daily tasks inside a service, you may keep using Windows scheduler or run an in-process scheduler (APScheduler).
