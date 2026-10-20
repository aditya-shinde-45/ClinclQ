@echo off
REM Quick start script for backend (Windows)

echo Starting ClinIQ Backend...
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo Error: Must run from project root directory
    exit /b 1
)

cd backend

REM Check if virtual environment exists
if not exist "venv" (
    py -3.12 -m venv venv 2>nul || python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
if not exist "venv\Scripts\uvicorn.exe" (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found!
    echo Copying .env.example to .env
    copy .env.example .env
    echo.
    echo Please edit backend\.env with your Supabase credentials before continuing!
    echo Press Ctrl+C to exit and edit .env, or press any key to continue anyway...
    pause
)

REM Start the server
echo.
echo Starting FastAPI server on http://localhost:8000
echo API docs available at http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
