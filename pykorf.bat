@echo off
setlocal enabledelayedexpansion

REM ============================================
REM pyKorf Launcher - Enhanced Installation
REM ============================================

REM Initialize environment
chcp 65001 > nul
set "SCRIPT_DIR=%~dp0"
set "APPDATA_DIR=%APPDATA%\pyKorf"
set "ESC="

REM Color codes
set "BLUE=%ESC%[94m"
set "CYAN=%ESC%[96m"
set "GREEN=%ESC%[92m"
set "RED=%ESC%[91m"
set "YELLOW=%ESC%[93m"
set "GRAY=%ESC%[90m"
set "RESET=%ESC%[0m"

REM ============================================
REM Header
REM ============================================
cls
echo.
echo %CYAN%          ######  #     # #    # ####### ######  ####### %RESET%
echo %CYAN%          #     #  #   #  #   #  #     # #     # #       %RESET%
echo %CYAN%          #     #   # #   #  #   #     # #     # #       %RESET%
echo %CYAN%          ######     #    ####   #     # ######  #####   %RESET%
echo %CYAN%          #          #    #  #   #     # #   #   #       %RESET%
echo %CYAN%          #          #    #   #  #     # #    #  #       %RESET%
echo %CYAN%          #          #    #    # ####### #     # #       %RESET%
echo.
echo %GRAY%                   Enterprise Hydraulic Modeling Toolkit%RESET%
echo.

REM ============================================
REM STEP 1: Python Detection (3.13)
REM ============================================
echo %BLUE%[1/4]%RESET% Checking Python installation...

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

echo.
echo %YELLOW%[!] Python 3.13 is required but not found.%RESET%
echo %GRAY%Attempting to install via winget...%RESET%
echo.

winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo.
    echo %RED%[X] Automatic installation failed.%RESET%
    echo Please install Python 3.13 manually from: %CYAN%https://www.python.org/downloads/%RESET%
    pause
    exit /b 1
)

echo.
echo %GREEN%[OK] Python 3.13 installed successfully.%RESET%
echo.
echo %YELLOW%========================================%RESET%
echo  Terminal restart required
echo %YELLOW%========================================%RESET%
echo.
echo  Please CLOSE this window and run %CYAN%pykorf.bat%RESET% again.
pause
exit /b

:python_found
for /f "tokens=*" %%v in ('!PYTHON_EXE! --version') do set "PYVER_STR=%%v"
echo %GREEN%[OK] Found !PYVER_STR!%RESET%

REM ============================================
REM STEP 2: UV Package Manager
REM ============================================
echo.
echo %BLUE%[2/4]%RESET% Checking package manager (uv)...

!PYTHON_EXE! -m uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %GRAY%Installing uv for faster setup...%RESET%
    !PYTHON_EXE! -m pip install --quiet uv
    if %errorlevel% neq 0 (
        echo %YELLOW%[!] Failed to install uv. Falling back to standard pip.%RESET%
        set "USE_UV=0"
    ) else (
        set "USE_UV=1"
    )
) else (
    set "USE_UV=1"
)

if "!USE_UV!"=="1" (
    echo %GREEN%[OK] uv ready%RESET%
) else (
    echo %GREEN%[OK] pip ready%RESET%
)

REM ============================================
REM STEP 3: Application Setup
REM ============================================
echo.
echo %BLUE%[3/4]%RESET% Syncing application files...

set "CURRENT_VERSION=unknown"
if exist "%SCRIPT_DIR%VERSION" set /p CURRENT_VERSION=<"%SCRIPT_DIR%VERSION"

set "INSTALLED_VERSION=none"
if exist "%APPDATA_DIR%\VERSION" set /p INSTALLED_VERSION=<"%APPDATA_DIR%\VERSION"

echo %GRAY%   Local version : !CURRENT_VERSION!%RESET%
echo %GRAY%   Installed     : !INSTALLED_VERSION!%RESET%

if "!CURRENT_VERSION!"=="!INSTALLED_VERSION!" (
    if exist "%APPDATA_DIR%\pykorf" (
        echo %GREEN%[OK] Files are up to date.%RESET%
        goto :env_setup
    )
)

echo %YELLOW%   Updating application to !CURRENT_VERSION!...%RESET%

REM Ensure directory exists
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"

REM Robust sync using robocopy
robocopy "%SCRIPT_DIR%pykorf" "%APPDATA_DIR%\pykorf" /E /PURGE /R:3 /W:5 /NFL /NDL /NJH /NJS /nc /ns /np >nul
copy /y "%SCRIPT_DIR%pyproject.toml" "%APPDATA_DIR%\" >nul
copy /y "%SCRIPT_DIR%VERSION" "%APPDATA_DIR%\" >nul

echo %GREEN%[OK] Sync complete.%RESET%

:env_setup
REM ============================================
REM STEP 4: Environment & Dependencies
REM ============================================
echo.
echo %BLUE%[4/4]%RESET% Preparing virtual environment...

cd /d "%APPDATA_DIR%"

REM Create venv if missing
if not exist ".venv\Scripts\python.exe" (
    if "!USE_UV!"=="1" (
        !PYTHON_EXE! -m uv venv .venv --quiet
    ) else (
        !PYTHON_EXE! -m venv .venv
    )
    if %errorlevel% neq 0 (
        echo %RED%[X] Failed to create environment.%RESET%
        pause
        exit /b 1
    )
)

REM Install/Update dependencies
echo %GRAY%   Updating dependencies...%RESET%
if "!USE_UV!"=="1" (
    !PYTHON_EXE! -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
) else (
    ".venv\Scripts\python.exe" -m pip install -e . --quiet
)

if %errorlevel% neq 0 (
    echo %RED%[X] Dependency installation failed.%RESET%
    pause
    exit /b 1
)

echo %GREEN%[OK] Environment is ready.%RESET%

REM ============================================
REM Launch
REM ============================================
timeout /t 1 >nul
cls
echo.
echo %CYAN%   Launching pyKorf TUI...%RESET%
echo.

".venv\Scripts\python.exe" -m pykorf

endlocal
