@echo off
REM pyKorf Launcher
REM Auto-installs Python 3.13 and uv if needed, then runs the pyKorf TUI

setlocal enabledelayedexpansion

REM Get the directory where this bat file is located (remove trailing backslash)
set SCRIPT_DIR=%~dp0
if "%SCRIPT_DIR:~-1%"=="\" set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set APPDATA_DIR=%APPDATA%\pyKorf

echo ========================================
echo        pyKorf Launcher
echo ========================================
echo.

REM ============================================
REM STEP 1: Check and Install Python 3.13
REM ============================================
echo Step 1 of 4: Checking Python...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [NOT FOUND] Python is not installed.
    echo.
    echo Installing Python 3.13 via winget...
    echo This may take a few minutes. Please wait...
    echo.
    winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Python installation failed.
        echo Please install Python 3.13 manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Python 3.13 installed successfully.
    echo.
    echo ========================================
    echo IMPORTANT: One more step required!
    echo ========================================
    echo.
    echo Please CLOSE this terminal window and
    echo double-click pykorf.bat again to continue.
    echo.
    echo This ensures Python is available in your PATH.
    echo.
    pause
    exit /b
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] Found Python %PYVER%
echo.

REM ============================================
REM STEP 2: Check and Install uv
REM ============================================
echo Step 2 of 4: Checking uv package manager...
echo.

python -m pip show uv >nul 2>&1
if errorlevel 1 (
    echo [NOT FOUND] uv is not installed.
    echo.
    echo Installing uv via pip...
    echo This will only take a moment...
    echo.
    python -m pip install uv
    
    if errorlevel 1 (
        echo.
        echo [ERROR] uv installation failed.
        echo Please install uv manually: python -m pip install uv
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] uv installed successfully.
    echo.
)

echo [OK] uv is available
echo.

REM Clear screen for a clean start
cls

REM ============================================
REM STEP 3: Setup Application Directory
REM ============================================
echo Step 3 of 4: Setting up application...
echo.

REM Create APPDATA directory if it doesn't exist
if not exist "%APPDATA_DIR%" (
    echo Creating application directory...
    mkdir "%APPDATA_DIR%"
)

REM Copy all files except pykorf.bat to APPDATA using robocopy
echo Copying application files...
robocopy "%SCRIPT_DIR%" "%APPDATA_DIR%" /E /XD .git .agents tests dist .opencode .venv __pycache__ pykorf\config /XF pykorf.bat *.zip *.exclude /NFL /NDL /NJH /NJS /nc /ns

echo [OK] Application files copied to %APPDATA_DIR%
echo.

REM Clear screen before launching
cls

REM ============================================
REM STEP 4: Install dependencies
REM ============================================
echo Step 4 of 4: Installing dependencies...
echo.

cd /d "%APPDATA_DIR%"
python -m uv sync --no-dev

if errorlevel 1 (
    echo [WARNING] Dependency sync had issues, trying pip install...
    python -m pip install -e .
)

echo.
echo ========================================
echo        Starting pyKorf TUI
echo ========================================
echo.

python -m uv run --no-dev python -m pykorf

endlocal