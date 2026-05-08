@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Attempting to install Python 3.12 with winget...
  where winget >nul 2>nul
  if errorlevel 1 (
    echo winget is not available on this machine.
    echo Please install Python 3.11+ from https://www.python.org/downloads/ and check "Add Python to PATH".
    pause
    exit /b 1
  )
  winget install --id Python.Python.3.12 -e
  echo.
  echo Python install finished. If the next step fails, close this window and rerun run_app_windows.bat so PATH refreshes.
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python still is not available on PATH.
  echo Close this window and rerun run_app_windows.bat, or install Python manually with "Add Python to PATH" checked.
  pause
  exit /b 1
)

if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo Failed to create virtual environment.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
pause
