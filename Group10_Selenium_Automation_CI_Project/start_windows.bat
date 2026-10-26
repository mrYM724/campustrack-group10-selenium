@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo CAMPUSTRACK - Group No. 10 Attendance QA Project
 echo ===================================================
where py >nul 2>&1
if not errorlevel 1 (set "PY=py -3") else (set "PY=python")
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python environment...
  %PY% -m venv .venv
  if errorlevel 1 goto :failed
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if errorlevel 1 goto :failed
set "TEST_MODE=1"
set "TEST_TOKEN=local-ci-demo-token"
set "SESSION_SECRET=campustrack-windows-demo-only-change-for-production"
echo.
echo Open http://127.0.0.1:8000 after the server starts.
echo Leave this window open while Selenium tests run.
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
exit /b %errorlevel%
:failed
echo Setup failed. Verify Python 3.11+ and internet for dependencies.
pause
exit /b 1
