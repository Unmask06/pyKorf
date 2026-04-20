@echo off
setlocal enabledelayedexpansion

REM ============================================
REM pyKorf Launcher - Minimal Orchestrator
REM ============================================
REM This batch file handles:
REM   1. Self-update (batch updates itself before Python exists)
REM   2. Python runtime detection/installation
REM   3. First-time download and extraction
REM   4. Delegation to pykorf_installer.py for all other operations
REM
REM All install/update/repair/launch logic is handled by:
REM   py -3.13 pykorf_installer.py <command> [--verbose] [--force-update]
REM
REM Exit codes:
REM   0 = success
REM   1 = error (check installer output for details)

REM --- Launcher constants ---
set "BAT_MAJOR=0"
set "BAT_VERSION=0.6.3"
set "AUTO_UPDATE=TRUE"
set "APPDATA_DIR=%APPDATA%\pyKorf"

REM ============================================
REM 1. Self-Update Check (batch-only)
REM ============================================
REM Download latest pykorf.bat from GitHub and replace self if newer.

if /i "!AUTO_UPDATE!"=="FALSE" goto :self_update_skip

set "SELF_TMP=%TEMP%\pykorf_self_upd.bat"
set "SELF_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf.bat"

curl.exe -L --fail --silent --max-time 30 -o "!SELF_TMP!" "!SELF_URL!" 2>nul
if %errorlevel% neq 0 goto :self_update_skip
if not exist "!SELF_TMP!" goto :self_update_skip

REM Extract BAT_VERSION from downloaded file (look for numeric version pattern)
set "SELF_REMOTE_VER="
for /f "tokens=2 delims==" %%v in ('findstr /r /c:"BAT_VERSION=[0-9]" "!SELF_TMP!"') do (
    for /f "tokens=1 delims= " %%x in ("%%v") do set "SELF_REMOTE_VER=%%x"
)
set "SELF_REMOTE_VER=!SELF_REMOTE_VER:"=!"

REM Skip if version empty or same
if "!SELF_REMOTE_VER!"=="" goto :self_update_skip
if "!SELF_REMOTE_VER!"=="!BAT_VERSION!" goto :self_update_skip

echo   Launcher update available: !BAT_VERSION! - !SELF_REMOTE_VER!
echo   Updating pykorf.bat...

copy /y "!SELF_TMP!" "%~f0" >nul 2>&1
if %errorlevel% equ 0 (
    del "!SELF_TMP!" >nul 2>&1
    echo   OK  Launcher updated. Relaunching...
    endlocal
    call "%~f0" %*
    exit /b
) else (
    del "!SELF_TMP!" >nul 2>&1
    echo   WARNING: Could not replace launcher - permission denied?
)

:self_update_skip
if exist "!SELF_TMP!" del "!SELF_TMP!" >nul 2>&1

REM ============================================
REM 2. Uninstall flag check
REM ============================================
REM Delegate uninstall to installer.py

if /i "%~1"=="/uninstall" goto :run_uninstall
if /i "%~1"=="--uninstall" goto :run_uninstall

REM ============================================
REM 3. Python Runtime Check
REM ============================================
REM Python must exist before we can use the installer.

py -3.13 --version >nul 2>&1
if %errorlevel% equ 0 goto :python_ok

echo.
echo   Python 3.13 not found - attempting automatic install...

winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo   X  Automatic install failed
    echo   Install Python 3.13 manually and run pykorf.bat again.
    echo.
    pause
    exit /b 1
)

echo   OK  Python 3.13 installed
echo.
echo   Restart required - close this window and run pykorf.bat again.
echo.
pause
exit /b

:python_ok

REM ============================================
REM 4. First Install / Missing Installer Check
REM ============================================
REM Existing users: new bat detects missing installer.py and downloads it.

if exist "%APPDATA_DIR%\pykorf_installer.py" goto :delegate_to_installer

REM Need to download release (first install or existing user upgrade)
goto :download_and_install

REM ============================================
REM 5. Delegate to Python Installer
REM ============================================
REM All operations after Python exists are handled by installer.py
REM Installer returns: 0=success, 1=error

:delegate_to_installer
cd /d "%APPDATA_DIR%"
py -3.13 pykorf_installer.py launch %*
exit /b %errorlevel%

REM ============================================
REM Uninstall Handler
REM ============================================
:run_uninstall
if not exist "%APPDATA_DIR%\pykorf_installer.py" (
    if not exist "%APPDATA_DIR%" (
        echo   pyKorf is not installed.
        pause
        exit /b 0
    )
    REM Download installer first
    goto :download_for_uninstall
)

cd /d "%APPDATA_DIR%"
if /i "%~2"=="--full" (
    py -3.13 pykorf_installer.py uninstall --full
) else (
    py -3.13 pykorf_installer.py uninstall
)
exit /b %errorlevel%

:download_for_uninstall
set "ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"
set "ZIP_PATH=%TEMP%\pykorf_uninstall.zip"
curl.exe -L --fail --silent --max-time 60 -o "!ZIP_PATH!" "!ZIP_URL!" 2>nul
if %errorlevel% neq 0 (
    echo   Failed to download installer - cannot uninstall
    pause
    exit /b 1
)
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"
powershell -Command "Expand-Archive -Path '!ZIP_PATH!' -DestinationPath '%APPDATA_DIR%' -Force" 2>nul
del "!ZIP_PATH!" >nul 2>&1
goto :run_uninstall

REM ============================================
REM Download and Install (first-time or missing installer)
REM ============================================
:download_and_install
cls
echo.
echo   pyKorf - Enterprise Hydraulic Modeling Toolkit
echo.
echo   -------------------------------------------------
echo   First-time setup or installer update
echo   -------------------------------------------------
echo.

set "ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"
set "ZIP_PATH=%TEMP%\pykorf.zip"

echo   Downloading pyKorf...
curl.exe -L --fail --silent --max-time 120 -o "!ZIP_PATH!" "!ZIP_URL!"
if %errorlevel% neq 0 (
    echo.
    echo   X  Download failed
    echo   Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)

if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"

echo   Extracting...
powershell -Command "Expand-Archive -Path '!ZIP_PATH!' -DestinationPath '%APPDATA_DIR%' -Force" 2>nul
if %errorlevel% neq 0 (
    del "!ZIP_PATH!" >nul 2>&1
    echo.
    echo   X  Extraction failed
    echo   Free up disk space and try again.
    echo.
    pause
    exit /b 1
)
del "!ZIP_PATH!" >nul 2>&1

echo   OK  Downloaded and extracted
echo.

REM Verify installer.py exists after extraction
if not exist "%APPDATA_DIR%\pykorf_installer.py" (
    echo   X  pykorf_installer.py missing from download
    echo   The release may be incomplete. Contact administrator.
    echo.
    pause
    exit /b 1
)

REM Delegate to installer for venv creation and setup
echo   Setting up installation...
cd /d "%APPDATA_DIR%"
py -3.13 pykorf_installer.py install

if %errorlevel% neq 0 (
    echo.
    echo   X  Installation failed
    echo   Check the error message above and try again.
    echo.
    pause
    exit /b 1
)

echo.
echo   OK  Installation complete
echo.

REM Launch after install
py -3.13 pykorf_installer.py launch %*
exit /b %errorlevel%