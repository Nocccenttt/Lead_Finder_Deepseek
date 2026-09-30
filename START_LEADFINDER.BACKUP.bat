@echo off
setlocal
cd /d "%~dp0"
title LeadFinder
color 0B

echo ============================================
echo             LEADFINDER
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed.
    echo Install Python 3.11 or newer, then run this file again.
    echo.
    pause
    exit /b 1
)

python --version
echo.

if not exist ".env" (
    echo ERROR: .env file was not found.
    echo.
    echo Copy your API configuration into:
    echo %CD%\.env
    echo.
    echo Required:
    echo   GOOGLE_MAPS_API_KEY
    echo   DEEPSEEK_API_KEY
    echo   PEXELS_API_KEY
    echo.
    pause
    exit /b 1
)

echo .env found.
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo Virtual environment ready.
echo.
echo Installing / updating LeadFinder dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :deps_error
".venv\Scripts\python.exe" -m pip install Flask openai python-dotenv beautifulsoup4 requests
if errorlevel 1 goto :deps_error

echo.
echo Dependencies ready.
echo.
echo Starting LeadFinder dashboard...
echo.
echo This computer:
echo   http://127.0.0.1:3000
echo.
echo Other devices on the same network can use:
echo   http://YOUR-COMPUTER-IP:3000
echo.
echo Keep this window open while using LeadFinder.
echo Press CTRL+C here to stop LeadFinder.
echo.

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:3000"

".venv\Scripts\python.exe" preview_dashboard.py
goto :end

:deps_error
echo.
echo ERROR: Dependency installation failed.
echo Check your internet connection and try again.
echo.
pause
exit /b 1

:end
echo.
echo ============================================
echo LeadFinder has stopped.
echo ============================================
pause
