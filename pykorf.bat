@echo off
setlocal enabledelayedexpansion

REM ============================================
REM pyKorf Launcher - Enhanced Installation
REM ============================================

REM Initialize environment
chcp 65001 > nul
set "SCRIPT_DIR=%~dp0"
set "APPDATA_DIR=%APPDATA%\pyKorf"
for /f %%a in ('echo prompt $E^| cmd') do set "ESC=%%a"

REM Color codes
set "BLUE=%ESC%[94m"
set "CYAN=%ESC%[96m"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "GRAY=%ESC%[90m"
set "WHITE=%ESC%[97m"
set "RESET=%ESC%[0m"

REM ============================================
REM Header
REM ============================================
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
echo %WHITE%    Setup  ·  Steps 1 – 4  ·  Runs once, stays ready%RESET%
echo %GRAY%  ────────────────────────────────────────────────────────%RESET%
echo.

REM ============================================
REM STEP 1: Python Detection (3.13)
REM ============================================
echo %CYAN%  ┌─ [1 / 4]  Python Runtime%RESET%
echo %CYAN%  │%RESET%

REM Try 'py' launcher first
set "PYTHON_EXE="
py -3.13 --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py -3.13"
    goto :python_found
)

REM Try 'python' and check version
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
REM STEP 3: Application Setup
REM ============================================
echo %CYAN%  ┌─ [3 / 4]  Application Files%RESET%
echo %CYAN%  │%RESET%

REM If source files were already cleaned up from a previous run, skip syncing
if not exist "%SCRIPT_DIR%pykorf" (
    if exist "%APPDATA_DIR%\pykorf" (
        echo %CYAN%  │%RESET%  %GREEN%✓  Already installed%RESET%
        echo %CYAN%  └─%RESET%
        echo.
        goto :env_setup
    )
)

set "CURRENT_VERSION=unknown"
if exist "%SCRIPT_DIR%VERSION" set /p CURRENT_VERSION=<"%SCRIPT_DIR%VERSION"

set "INSTALLED_VERSION=none"
if exist "%APPDATA_DIR%\VERSION" set /p INSTALLED_VERSION=<"%APPDATA_DIR%\VERSION"

if "!CURRENT_VERSION!"=="!INSTALLED_VERSION!" (
    if exist "%APPDATA_DIR%\pykorf" (
        echo %CYAN%  │%RESET%  %GREEN%✓  v!CURRENT_VERSION! — up to date%RESET%
        echo %CYAN%  └─%RESET%
        echo.
        goto :env_setup
    )
)

echo %CYAN%  │%RESET%  %GRAY%  Installing v!CURRENT_VERSION!...%RESET%

REM Ensure directory exists
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"

REM Robust sync using robocopy
robocopy "%SCRIPT_DIR%pykorf" "%APPDATA_DIR%\pykorf" /E /PURGE /R:3 /W:5 /NFL /NDL /NJH /NJS /nc /ns /np >nul
set "SYNC_OK=0"
if !ERRORLEVEL! lss 8 set "SYNC_OK=1"
copy /y "%SCRIPT_DIR%pyproject.toml" "%APPDATA_DIR%\" >nul
copy /y "%SCRIPT_DIR%VERSION" "%APPDATA_DIR%\" >nul

echo %CYAN%  │%RESET%  %GREEN%✓  Installed — v!CURRENT_VERSION!%RESET%

REM Remove source files from the launch folder — only pykorf.bat is needed from now on
if "!SYNC_OK!"=="1" (
    if exist "%SCRIPT_DIR%pykorf" rd /s /q "%SCRIPT_DIR%pykorf"
    if exist "%SCRIPT_DIR%pyproject.toml" del /q "%SCRIPT_DIR%pyproject.toml"
    if exist "%SCRIPT_DIR%VERSION" del /q "%SCRIPT_DIR%VERSION"
    echo %CYAN%  │%RESET%  %GRAY%  Cleaned up — only pykorf.bat needed from now on%RESET%
)
echo %CYAN%  └─%RESET%
echo.

:env_setup
REM ============================================
REM STEP 4: Environment & Dependencies
REM ============================================
echo %CYAN%  ┌─ [4 / 4]  Virtual Environment%RESET%
echo %CYAN%  │%RESET%

cd /d "%APPDATA_DIR%"

REM Create venv if missing
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

REM Install/Update dependencies
echo %CYAN%  │%RESET%  %GRAY%  Updating dependencies...%RESET%
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
