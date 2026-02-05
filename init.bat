@echo off
setlocal enableextensions enabledelayedexpansion

REM ============================================================
REM  init.bat - NagiFlow Initialization Script
REM ============================================================

REM ====== Configuration ======
set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "WEB=%ROOT%web"
set "WORKSPACE=%USERPROFILE%\NagiFlow"

echo ============================================================
echo  [INFO] Initializing NagiFlow...
echo  [INFO] Project Root: %ROOT%
echo ============================================================

REM ====== Stage 1: Check Requirements ======
echo.
echo [INFO] Stage 1/4: Checking system requirements...

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found in PATH.
  echo         Please install Python 3.12+ and restart your terminal.
  exit /b 1
) else (
  echo [SUCCESS] Python found.
)

where pnpm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] pnpm not found in PATH.
  echo         Please install pnpm and restart your terminal.
  exit /b 1
) else (
  echo [SUCCESS] pnpm found.
)

where ollama >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Ollama not found in PATH.
  echo         Please install Ollama and restart your terminal.
  exit /b 1
) else (
  echo [SUCCESS] Ollama found.
  ollama --version
)

REM ====== Stage 2: Backend Setup ======
echo.
echo [INFO] Stage 2/4: Setting up Backend...

if not exist "%BACKEND%\venv\Scripts\python.exe" (
  echo [INFO] Creating Python virtual environment...
  python -m venv "%BACKEND%\venv"
)

echo [INFO] Activating virtual environment...
call "%BACKEND%\venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] Failed to activate virtual environment.
  exit /b 1
)

echo [INFO] Installing backend dependencies...
python -m pip install --upgrade pip
python -m pip install -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
  echo [ERROR] Failed to install backend requirements.
  exit /b 1
)

REM ====== Stage 3: Frontend Setup ======
echo.
echo [INFO] Stage 3/4: Setting up Frontend...

pushd "%WEB%"

echo [INFO] Installing frontend packages (pnpm install)...
call pnpm install
if errorlevel 1 (
  popd
  echo [ERROR] pnpm install failed.
  exit /b 1
)

echo [INFO] Building frontend (pnpm build)...
call pnpm build
if errorlevel 1 (
  popd
  echo [ERROR] pnpm build failed.
  exit /b 1
)

popd

REM ====== Stage 4: Workspace Configuration ======
echo.
echo [INFO] Stage 4/4: Configuring Workspace...
echo [INFO] Target Workspace: %WORKSPACE%

if not exist "%WORKSPACE%" (
  echo [INFO] Creating workspace directory...
  mkdir "%WORKSPACE%"
  if errorlevel 1 (
    echo [ERROR] Failed to create workspace at: "%WORKSPACE%"
    exit /b 1
  )
)

if not exist "%WORKSPACE%\env" (
  echo [INFO] Creating default env file...
  type nul > "%WORKSPACE%\env"
  if errorlevel 1 (
    echo [ERROR] Failed to create env file at: "%WORKSPACE%\env"
    exit /b 1
  )
)

echo.
echo ============================================================
echo [SUCCESS] NagiFlow initialization complete!
echo ============================================================
exit /b 0