@echo off
title NagiFlow
setlocal

set ROOT=%~dp0

echo ================================================
echo   NagiFlow - Starting services
echo ================================================
echo.

:: Check .env exists
if not exist "%ROOT%backend\.env" (
    echo [WARN] backend\.env not found.
    echo        Copy backend\.env.example to backend\.env and fill in the values.
    echo.
)

:: 1. Ollama (LLM backend)
echo [1/3] Starting Ollama...
start "NagiFlow - Ollama" cmd /k "ollama serve"

:: 2. Backend (FastAPI + uvicorn)
echo [2/3] Starting Backend...
start "NagiFlow - Backend" cmd /k "cd /d "%ROOT%backend" && call .venv\Scripts\activate.bat && uvicorn nagiflow.main:app --reload"

:: 3. Frontend (Vite dev server)
echo [3/3] Starting Frontend...
start "NagiFlow - Frontend" cmd /k "cd /d "%ROOT%web" && pnpm dev"

echo.
echo ================================================
echo   Services started in separate windows
echo ------------------------------------------------
echo   Backend  : http://localhost:8000
echo   API docs : http://localhost:8000/docs
echo   Frontend : http://localhost:3000
echo ================================================
echo.

endlocal
