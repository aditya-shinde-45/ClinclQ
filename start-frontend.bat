@echo off
REM Quick start script for frontend (Windows)

echo Starting ClinIQ Frontend...
echo.

if not exist "frontend\package.json" (
    echo Error: Must run from project root directory
    exit /b 1
)

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Check if .env exists
if not exist ".env" (
    echo Creating .env file from .env.example...
    copy .env.example .env
)

echo.
echo Starting Vite dev server on http://localhost:8443
echo.
call npm run dev
