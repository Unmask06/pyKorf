@echo off
REM pyKorf Launcher
REM Auto-installs Python 3.13 and uv if needed, then runs the pyKorf TUI

setlocal enabledelayedexpansion

REM Get the directory where this bat file is located
set "SCRIPT_DIR=%~dp0"
set "APPDATA_DIR=%APPDATA%\pyKorf"

echo ========================================
echo        pyKorf Launcher
echo ========================================
echo.

REM ============================================
REM STEP 1: Check and Install Python 3.13
REM ============================================
echo Step 1 of 4: Checking Python...
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
    echo  IMPORTANT: One more step required!
    echo ========================================
    echo.
    echo  Please CLOSE this terminal window and
    echo  double-click pykorf.bat again to continue.
    echo.
    echo  This ensures Python is available in your PATH.
    echo.
    pause
    exit /b
)

REM Get Python 3.13 version
for /f "tokens=2" %%i in ('py -3.13 --version 2^>^&1') do set "PYVER=%%i"
echo [OK] Found Python %PYVER%
echo.

REM ============================================
REM STEP 2: Check and Install uv
REM ============================================
echo Step 2 of 4: Checking uv package manager...
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

REM ============================================
REM STEP 3: Version Check and File Setup
REM ============================================
echo Step 3 of 4: Setting up application...
echo.

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

echo   Distributed version : !CURRENT_VERSION!
echo   Installed version   : !INSTALLED_VERSION!
echo.

REM Compare versions - if different, wipe and reinstall
if "!CURRENT_VERSION!"=="!INSTALLED_VERSION!" (
    echo [OK] Already up to date.
) else (
    echo [UPDATE] New version detected. Updating...

    REM Remove old installation completely (including .venv)
    if exist "%APPDATA_DIR%" (
        echo Removing old installation...
        rmdir /s /q "%APPDATA_DIR%"
    )

    REM Create fresh APPDATA directory
    mkdir "%APPDATA_DIR%"

    REM Copy application files using xcopy
    echo Copying application files...
    xcopy /e /i /y /q "%SCRIPT_DIR%pykorf" "%APPDATA_DIR%\pykorf" >nul
    copy /y "%SCRIPT_DIR%pyproject.toml" "%APPDATA_DIR%\" >nul
    copy /y "%SCRIPT_DIR%VERSION" "%APPDATA_DIR%\" >nul

    echo [OK] Version !CURRENT_VERSION! installed to %APPDATA_DIR%
)

echo.

REM ============================================
REM STEP 4: Create Venv and Install Dependencies
REM ============================================
echo Step 4 of 4: Installing dependencies...
echo.

cd /d "%APPDATA_DIR%"

REM Create venv with Python 3.13 if it doesn't exist
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment with Python 3.13...
    py -3.13 -m venv .venv

    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Install dependencies using uv (targeting the venv)
echo Installing dependencies...
py -3.13 -m uv pip install --python "%APPDATA_DIR%\.venv\Scripts\python.exe" -e . >nul 2>&1

if errorlevel 1 (
    echo [WARNING] uv install failed, falling back to pip...
    "%APPDATA_DIR%\.venv\Scripts\python.exe" -m pip install -e . >nul 2>&1

    if errorlevel 1 (
        echo [ERROR] Package installation failed.
        pause
        exit /b 1
    )
)

echo [OK] Dependencies installed.
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

"%APPDATA_DIR%\.venv\Scripts\python.exe" -m pykorf

endlocal
