@echo off
REM =============================
REM Set your WSL distribution name below.
REM To find it, run: wsl -l -v
REM Example: set WSL_DIST=Ubuntu-22.04
set WSL_DIST=Ubuntu
REM =============================

echo Starting Sponnect Application...

:: Set the path to your project (inside WSL)
set SPONNECT_PATH=/home/soham/sponnectv3

:: Start Redis Server
start wt new-tab wsl -d %WSL_DIST% -- bash -c "redis-server"

:: Start MailHog
start wt new-tab wsl -d %WSL_DIST% -- bash -c "mailhog"

:: Start Celery Worker
start wt new-tab wsl -d %WSL_DIST% -- bash -c "cd %SPONNECT_PATH%/sponnect/backend && ./celery_worker.sh"

:: Start Celery Beat
start wt new-tab wsl -d %WSL_DIST% -- bash -c "cd %SPONNECT_PATH%/sponnect/backend && ./celery_beat.sh"

:: Start Flask Backend
start wt new-tab wsl -d %WSL_DIST% -- bash -c "cd %SPONNECT_PATH%/sponnect/backend && flask run"

:: Start Vue Frontend
start wt new-tab wsl -d %WSL_DIST% -- bash -c "cd %SPONNECT_PATH%/sponnect/frontend && npm run dev"

echo All Sponnect components are starting in separate terminals.
echo Press any key to exit this window...
pause > nul