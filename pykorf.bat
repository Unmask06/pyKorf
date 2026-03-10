@echo off
REM pyKorf Launcher
REM Auto-installs Python 3.13 and uv if needed, then runs the pyKorf TUI

setlocal enabledelayedexpansion

REM Get the directory where this bat file is located
set SCRIPT_DIR=%~dp0
set APPDATA_DIR=%APPDATA%\pyKorf

echo ========================================
echo        pyKorf Launcher
echo ========================================
echo.

REM ============================================
REM STEP 1: Check and Install Python 3.13
REM ============================================
echo Step 1 of 3: Checking Python...
echo.

py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo [NOT FOUND] Python 3.13 is not installed.
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

REM Get Python 3.13 version
for /f "tokens=2" %%i in ('py -3.13 --version 2^>^&1') do set PYVER=%%i
echo [OK] Found Python %PYVER%
echo.

REM ============================================
REM STEP 2: Check and Install uv
REM ============================================
echo Step 2 of 3: Checking uv package manager...
echo.

py -3.13 -m pip show uv >nul 2>&1
if errorlevel 1 (
    echo [NOT FOUND] uv is not installed.
    echo.
    echo Installing uv via pip...
    echo This will only take a moment...
    echo.
    py -3.13 -m pip install uv
    
    if errorlevel 1 (
        echo.
        echo [ERROR] uv installation failed.
        echo Please install uv manually: py -3.13 -m pip install uv
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
echo Step 3 of 3: Setting up application...
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
REM Launch pyKorf TUI
REM ============================================
echo ========================================
echo        Starting pyKorf TUI
echo ========================================
echo.

cd /d "%APPDATA_DIR%"
py -3.13 -m uv run --no-editable python -m pykorf

endlocal
