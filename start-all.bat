@echo off
REM Quick start script to run both backend and frontend (Windows)

echo ==============================================
echo   ClinIQ - Starting Full Stack Application
echo ==============================================
echo.

if not exist "backend\main.py" (
    echo Error: Must run from project root directory
    exit /b 1
)

echo Starting Backend in separate window...
start "ClinIQ Backend (Port 8000)" cmd /k "start-backend.bat"

timeout /t 2 /nobreak >nul

echo Starting Frontend in separate window...
start "ClinIQ Frontend (Port 8443)" cmd /k "start-frontend.bat"

echo.
echo ==============================================
echo   ClinIQ is starting up!
echo   Frontend : http://localhost:8443
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/docs
echo ==============================================
