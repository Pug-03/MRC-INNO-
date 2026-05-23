@echo off
REM One-click launcher for the Cap Sorter dashboard.
REM Double-click this file to start everything and open the website.

cd /d "%~dp0"

echo.
echo Starting Cap Sorter...
echo.

REM Start the backend (Python) in its own window.
start "Cap Sorter - Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe run.py"

REM Start the frontend (Vite) in its own window.
start "Cap Sorter - Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

REM Give the servers a few seconds to start, then open the dashboard in the browser.
timeout /t 6 /nobreak >nul
start "" http://localhost:5175

echo.
echo Two windows should have opened: Backend and Frontend.
echo Do NOT close them while you want to use the dashboard.
echo To stop the dashboard, close both of those windows.
echo.
pause
