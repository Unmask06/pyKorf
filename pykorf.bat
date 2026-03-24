@echo off
setlocal enabledelayedexpansion

REM ============================================
REM pyKorf Launcher
REM ============================================

REM --- Launcher version constants ---
REM BAT_MAJOR: must match the installed app's major version (controls zip filename).
REM            Bump when a breaking app change forces a new launcher.
REM BAT_VERSION: this specific launcher's version (MAJOR.MINOR).
REM              Bump on any launcher fix/improvement; enables auto-update.
REM AUTO_UPDATE: TRUE = silently self-update when a newer launcher is on GitHub.
REM              FALSE = never self-update; user must get new bat from administrator.
set "BAT_MAJOR=1"
set "BAT_VERSION=1.0"
set "AUTO_UPDATE=TRUE"

chcp 65001 > nul
set "APPDATA_DIR=%APPDATA%\pyKorf"
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

REM Color codes
set "CYAN=%ESC%[96m"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "GRAY=%ESC%[90m"
set "WHITE=%ESC%[97m"
set "RESET=%ESC%[0m"

REM ============================================
REM Launcher self-update check
REM (silent network check; skipped gracefully if offline)
REM ============================================
set "VER_URL=https://github.com/Unmask06/pykorf/releases/latest/download/bat_version.txt"
set "BAT_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf.bat"
set "VER_TMP=%TEMP%\pk_bat_ver.txt"

curl -L --fail --silent --max-time 5 -o "!VER_TMP!" "!VER_URL!" 2>nul
if %errorlevel% neq 0 goto :self_update_done

set "REMOTE_VER="
set /p REMOTE_VER=<"!VER_TMP!"
del "!VER_TMP!" >nul 2>&1
if "!REMOTE_VER!"=="" goto :self_update_done

REM Parse local  BAT_VERSION (MAJOR.MINOR)
set "L_MAJ=0" & set "L_MIN=0"
for /f "tokens=1,2 delims=." %%a in ("!BAT_VERSION!") do ( set /a "L_MAJ=%%a" & set /a "L_MIN=%%b" )

REM Parse remote BAT_VERSION (MAJOR.MINOR)
set "R_MAJ=0" & set "R_MIN=0"
for /f "tokens=1,2 delims=." %%a in ("!REMOTE_VER!") do ( set /a "R_MAJ=%%a" & set /a "R_MIN=%%b" )

set "NEED_UPDATE=0"
if !R_MAJ! gtr !L_MAJ! set "NEED_UPDATE=1"
if !R_MAJ! equ !L_MAJ! ( if !R_MIN! gtr !L_MIN! set "NEED_UPDATE=1" )

if "!NEED_UPDATE!"=="0" goto :self_update_done
if /i not "!AUTO_UPDATE!"=="TRUE" goto :self_update_done

REM --- Download new launcher and hand off to a helper that replaces this file ---
set "SELF=%~f0"
set "NEW_BAT=%TEMP%\pykorf_new.bat"
set "UPD=%TEMP%\pk_upd.bat"

curl -L --fail --silent -o "!NEW_BAT!" "!BAT_URL!" 2>nul
if %errorlevel% neq 0 goto :self_update_done

(
    echo @echo off
    echo ping -n 2 127.0.0.1 ^>nul
    echo copy /y "!NEW_BAT!" "!SELF!" ^>nul 2^>nul
    echo del "!NEW_BAT!" 2^>nul
    echo start "" "!SELF!"
    echo ^(goto^) 2^>nul ^& del "%%~f0"
) > "!UPD!"

echo %CYAN%  Launcher updated !BAT_VERSION! → !REMOTE_VER!. Relaunching...%RESET%
start /min "" "!UPD!"
exit /b

:self_update_done

REM ============================================
REM Fast path — already installed
REM ============================================
if not exist "%APPDATA_DIR%\.venv\Scripts\python.exe" goto :first_install

set "INST_VER=0.0.0"
if exist "%APPDATA_DIR%\VERSION" set /p INST_VER=<"%APPDATA_DIR%\VERSION"
set "INST_MAJOR=0"
for /f "tokens=1 delims=." %%a in ("!INST_VER!") do set "INST_MAJOR=%%a"

if not "!INST_MAJOR!"=="!BAT_MAJOR!" (
    cls
    echo.
    echo %RED%  ┌───────────────────────────────────────────────────────┐%RESET%
    echo %RED%  │   Launcher Outdated                                   │%RESET%
    echo %RED%  │                                                       │%RESET%
    echo %RED%  │   This launcher is not compatible with the installed  │%RESET%
    echo %RED%  │   version of pyKorf.                                  │%RESET%
    echo %RED%  │                                                       │%RESET%
    echo %RED%  │   Contact your administrator for the updated          │%RESET%
    echo %RED%  │   pykorf.bat file.                                    │%RESET%
    echo %RED%  └───────────────────────────────────────────────────────┘%RESET%
    echo.
    pause
    exit /b 1
)

cd /d "%APPDATA_DIR%"
".venv\Scripts\python.exe" -m pykorf
exit /b

REM ============================================
REM First-time install
REM ============================================
:first_install
cls
echo.
echo %CYAN%        ######  #     # #    # ####### ######  ####### %RESET%
echo %CYAN%        #     #  #   #  #   #  #     # #     # #       %RESET%
echo %CYAN%        #     #   # #   #  #   #     # #     # #       %RESET%
echo %CYAN%        ######     #    ####   #     # ######  #####   %RESET%
echo %CYAN%        #          #    #  #   #     # #   #   #       %RESET%
echo %CYAN%        #          #    #   #  #     # #    #  #       %RESET%
echo %CYAN%        #          #    #    # ####### #     # #       %RESET%
echo.
echo %GRAY%            Enterprise Hydraulic Modeling Toolkit%RESET%
echo.
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo %WHITE%    First-time setup  ·  Steps 1 – 4  ·  Runs once%RESET%
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo.

REM ============================================
REM STEP 1: Python Detection (3.13)
REM ============================================
echo %CYAN%  ┌─ [1 / 4]  Python Runtime%RESET%
echo %CYAN%  │%RESET%

set "PYTHON_EXE="
py -3.13 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py -3.13"
    goto :python_found
)

for /f "tokens=2" %%v in ('python --version 2^>nul') do (
    set "VER=%%v"
    if "!VER:~0,4!"=="3.13" (
        set "PYTHON_EXE=python"
        goto :python_found
    )
)

echo %CYAN%  │%RESET%  %YELLOW%  Python 3.13 not found — attempting automatic install...%RESET%
echo %CYAN%  │%RESET%

winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo %CYAN%  │%RESET%
    echo %CYAN%  └─%RESET%  %RED%✗  Automatic install failed%RESET%
    echo.
    echo %WHITE%     Install Python 3.13 manually from:%RESET%
    echo %CYAN%     https://www.python.org/downloads/%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  │%RESET%  %GREEN%✓  Python 3.13 installed%RESET%
echo %CYAN%  └─%RESET%
echo.
echo %YELLOW%  ┌───────────────────────────────────────────────────────┐%RESET%
echo %YELLOW%  │   Restart required                                    │%RESET%
echo %YELLOW%  │   Close this window and run pykorf.bat again.         │%RESET%
echo %YELLOW%  └───────────────────────────────────────────────────────┘%RESET%
echo.
pause
exit /b

:python_found
for /f "tokens=*" %%v in ('!PYTHON_EXE! --version') do set "PYVER_STR=%%v"
echo %CYAN%  │%RESET%  %GREEN%✓  !PYVER_STR! detected%RESET%
echo %CYAN%  └─%RESET%
echo.

REM ============================================
REM STEP 2: UV Package Manager
REM ============================================
echo %CYAN%  ┌─ [2 / 4]  Package Manager%RESET%
echo %CYAN%  │%RESET%

!PYTHON_EXE! -m uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %CYAN%  │%RESET%  %GRAY%  Installing uv...%RESET%
    !PYTHON_EXE! -m pip install --quiet uv
    if %errorlevel% neq 0 (
        echo %CYAN%  │%RESET%  %YELLOW%  uv unavailable — falling back to pip%RESET%
        set "USE_UV=0"
    ) else (
        set "USE_UV=1"
    )
) else (
    set "USE_UV=1"
)

if "!USE_UV!"=="1" (
    echo %CYAN%  │%RESET%  %GREEN%✓  uv ready%RESET%
) else (
    echo %CYAN%  │%RESET%  %GREEN%✓  pip ready%RESET%
)
echo %CYAN%  └─%RESET%
echo.

REM ============================================
REM STEP 3: Download pyKorf from GitHub
REM ============================================
echo %CYAN%  ┌─ [3 / 4]  Download pyKorf%RESET%
echo %CYAN%  │%RESET%

set "ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"
set "ZIP_PATH=%TEMP%\pykorf.zip"

echo %CYAN%  │%RESET%  %GRAY%  Downloading from GitHub...%RESET%
curl -L --fail --progress-bar -o "!ZIP_PATH!" "!ZIP_URL!"
if %errorlevel% neq 0 (
    echo %CYAN%  │%RESET%
    echo %CYAN%  └─%RESET%  %RED%✗  Download failed%RESET%
    echo.
    echo %YELLOW%  ┌───────────────────────────────────────────────────────┐%RESET%
    echo %YELLOW%  │   If pyKorf has released a new major version,         │%RESET%
    echo %YELLOW%  │   contact your administrator for the updated           │%RESET%
    echo %YELLOW%  │   pykorf.bat file.                                    │%RESET%
    echo %YELLOW%  └───────────────────────────────────────────────────────┘%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  │%RESET%  %GRAY%  Extracting...%RESET%
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"
tar -xf "!ZIP_PATH!" -C "%APPDATA_DIR%\"
if %errorlevel% neq 0 (
    echo %CYAN%  │%RESET%
    echo %CYAN%  └─%RESET%  %RED%✗  Extraction failed%RESET%
    echo.
    pause
    exit /b 1
)
del "!ZIP_PATH!" >nul 2>&1

echo %CYAN%  │%RESET%  %GREEN%✓  Downloaded and extracted%RESET%
echo %CYAN%  └─%RESET%
echo.

REM ============================================
REM STEP 4: Virtual Environment & Dependencies
REM ============================================
:env_setup
echo %CYAN%  ┌─ [4 / 4]  Virtual Environment%RESET%
echo %CYAN%  │%RESET%

cd /d "%APPDATA_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo %CYAN%  │%RESET%  %GRAY%  Creating environment...%RESET%
    if "!USE_UV!"=="1" (
        !PYTHON_EXE! -m uv venv .venv --quiet
    ) else (
        !PYTHON_EXE! -m venv .venv
    )
    if %errorlevel% neq 0 (
        echo %CYAN%  │%RESET%
        echo %CYAN%  └─%RESET%  %RED%✗  Failed to create environment%RESET%
        echo.
        pause
        exit /b 1
    )
)

echo %CYAN%  │%RESET%  %GRAY%  Installing dependencies...%RESET%
if "!USE_UV!"=="1" (
    !PYTHON_EXE! -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
) else (
    ".venv\Scripts\python.exe" -m pip install -e . --quiet
)

if %errorlevel% neq 0 (
    echo %CYAN%  │%RESET%
    echo %CYAN%  └─%RESET%  %RED%✗  Dependency installation failed%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  │%RESET%  %GREEN%✓  Environment ready%RESET%
echo %CYAN%  └─%RESET%
echo.
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo.

REM ============================================
REM Launch
REM ============================================
timeout /t 1 >nul
cls
echo.
echo %CYAN%        ######  #     # #    # ####### ######  ####### %RESET%
echo %CYAN%        #     #  #   #  #   #  #     # #     # #       %RESET%
echo %CYAN%        #     #   # #   #  #   #     # #     # #       %RESET%
echo %CYAN%        ######     #    ####   #     # ######  #####   %RESET%
echo %CYAN%        #          #    #  #   #     # #   #   #       %RESET%
echo %CYAN%        #          #    #   #  #     # #    #  #       %RESET%
echo %CYAN%        #          #    #    # ####### #     # #       %RESET%
echo.
echo %GRAY%            Enterprise Hydraulic Modeling Toolkit%RESET%
echo.
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo %WHITE%    Starting...%RESET%
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo.

".venv\Scripts\python.exe" -m pykorf

endlocal
