@echo off
REM pyKorf Launcher - Enhanced User Experience
REM Auto-installs Python 3.13 and uv if needed, then runs the pyKorf TUI

setlocal enabledelayedexpansion

REM Get the directory where this bat file is located
set "SCRIPT_DIR=%~dp0"
set "APPDATA_DIR=%APPDATA%\pyKorf"

REM ============================================
REM Clean Output Header
REM ============================================
cls
echo/
echo/
echo/
echo/
echo/
echo/
echo/
echo/
echo/
echo/
echo           ██████╗  ██████╗ ██╗     ██╗     ██╗███╗   ██╗███████╗
echo           ██╔══██╗██╔═══██╗██║     ██║     ██║████╗  ██║██╔════╝
echo           ██████╔╝██║   ██║██║     ██║     ██║██╔██╗ ██║█████╗  
echo           ██╔══██╗██║   ██║██║     ██║     ██║██║╚██╗██║██╔══╝  
echo           ██║  ██║╚██████╔╝███████╗███████╗██║██║ ╚████║███████╗
echo           ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝
echo/
echo                    Enterprise Hydraulic Modeling Toolkit
echo/
echo/

REM ============================================
REM STEP 1: Check and Install Python 3.13
REM ============================================
echo [1/4] Checking Python installation...
echo/

py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo/
    echo ⚠  Python 3.13 is not installed.
    echo/
    echo Installing Python 3.13...
    echo/
    winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements

    if errorlevel 1 (
        echo/
        echo ✗ Installation failed.
        echo Please install Python 3.13 manually from https://www.python.org/downloads/
        echo/
        pause
        exit /b 1
    )

    echo/
    echo ✓ Python 3.13 installed successfully.
    echo/
    echo ========================================
    echo  One more step required!
    echo ========================================
    echo/
    echo  Please CLOSE this terminal and
    echo  double-click pykorf.bat again.
    echo/
    echo  This ensures Python is properly configured.
    echo/
    pause
    exit /b
)

for /f "tokens=2" %%i in ('py -3.13 --version 2^>^&1') do set "PYVER=%%i"
echo ✓ Found Python %PYVER%
echo/

REM ============================================
REM STEP 2: Check and Install uv
REM ============================================
echo [2/4] Checking package manager...
echo/

py -3.13 -m pip show uv >nul 2>&1
if errorlevel 1 (
    echo/
    echo Installing uv...
    echo/
    py -3.13 -m pip install uv

    if errorlevel 1 (
        echo/
        echo ✗ Installation failed.
        echo Please install uv manually: py -3.13 -m pip install uv
        echo/
        pause
        exit /b 1
    )
    echo/
    echo ✓ uv installed successfully.
    echo/
)

echo ✓ Package manager ready
echo/

REM ============================================
REM STEP 3: Version Check and File Setup
REM ============================================
echo [3/4] Setting up application...
echo/

REM Read version from the extracted zip folder (next to this bat file)
set "CURRENT_VERSION=unknown"
if exist "%SCRIPT_DIR%VERSION" (
    set /p CURRENT_VERSION=<"%SCRIPT_DIR%VERSION"
)

REM Read installed version from APPDATA
set "INSTALLED_VERSION=none"
if exist "%APPDATA_DIR%\VERSION" (
    set /p INSTALLED_VERSION=<"%APPDATA_DIR%\VERSION"
)

echo   Current version : !CURRENT_VERSION!
echo   Installed       : !INSTALLED_VERSION!
echo/

REM Compare versions - if different, wipe and reinstall
if "!CURRENT_VERSION!"=="!INSTALLED_VERSION!" (
    echo ✓ Already up to date.
) else (
    echo  Updating to version !CURRENT_VERSION!...

    REM Remove only the old package code, keep user data (config.json, data/)
    if exist "%APPDATA_DIR%\pykorf" (
        rmdir /s /q "%APPDATA_DIR%\pykorf"
    )

    REM Ensure APPDATA directory exists (preserve user data)
    if not exist "%APPDATA_DIR%" (
        mkdir "%APPDATA_DIR%"
    )

    REM Copy application files using xcopy
    xcopy /e /i /y /q "%SCRIPT_DIR%pykorf" "%APPDATA_DIR%\pykorf" >nul
    copy /y "%SCRIPT_DIR%pyproject.toml" "%APPDATA_DIR%\" >nul
    copy /y "%SCRIPT_DIR%VERSION" "%APPDATA_DIR%\" >nul

    echo ✓ Version !CURRENT_VERSION! installed.
)

echo/

REM ============================================
REM STEP 4: Create Venv and Install Dependencies
REM ============================================
echo [4/4] Preparing your environment...
echo/

cd /d "%APPDATA_DIR%"

REM Create venv with Python 3.13 if it doesn't exist
if not exist ".venv\Scripts\python.exe" (
    py -3.13 -m venv .venv

    if errorlevel 1 (
        echo/
        echo ✗ Failed to create environment.
        pause
        exit /b 1
    )
)

REM Install dependencies using uv (targeting the venv)
py -3.13 -m uv pip install --python "%APPDATA_DIR%\.venv\Scripts\python.exe" -e . >nul 2>&1

if errorlevel 1 (
    "%APPDATA_DIR%\.venv\Scripts\python.exe" -m pip install -e . >nul 2>&1

    if errorlevel 1 (
        echo/
        echo ✗ Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo ✓ Environment ready.
echo/

REM Clear screen before launching
cls

REM ============================================
REM Launch pyKorf TUI
REM ============================================
echo   Launching pyKorf TUI...
echo/

"%APPDATA_DIR%\.venv\Scripts\python.exe" -m pykorf

endlocal
