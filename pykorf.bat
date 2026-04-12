@echo off
setlocal enabledelayedexpansion

REM ============================================
REM pyKorf Launcher
REM ============================================

REM --- Launcher version constants ---
REM BAT_MAJOR: must match the installed app's major version (controls zip filename).
REM            Bump when a breaking app change forces a new launcher.
REM BAT_VERSION: this specific launcher's version (MAJOR.MINOR.PATCH).
REM              Bump on any launcher fix/improvement; enables auto-update.
REM AUTO_UPDATE: TRUE = silently self-update when a newer launcher is on GitHub.
REM              FALSE = never self-update; user must get new bat from administrator.
set "BAT_MAJOR=0"
set "BAT_VERSION=0.6.0"
set "AUTO_UPDATE=TRUE"

set "APPDATA_DIR=%APPDATA%\pyKorf"

REM Color codes (disabled for compatibility)
set "CYAN="
set "GREEN="
set "RED="
set "YELLOW="
set "GRAY="
set "WHITE="
set "RESET="

REM ============================================
REM Launcher Self-Update Check
REM ============================================
REM Download latest pykorf.bat from GitHub releases and replace self if newer.
REM Uses %~f0 so this works regardless of where the user saved pykorf.bat.

if /i "!AUTO_UPDATE!"=="FALSE" goto :self_update_skip

set "SELF_LOCAL_VER=!BAT_VERSION!"
set "SELF_TMP=%TEMP%\pykorf_self_upd.bat"
set "SELF_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf.bat"

curl -L --fail --silent --max-time 30 -o "!SELF_TMP!" "!SELF_URL!" 2>nul
if %errorlevel% neq 0 goto :self_update_skip
if not exist "!SELF_TMP!" goto :self_update_skip

REM Extract BAT_VERSION from downloaded file
for /f "tokens=2 delims==" %%v in ('findstr /c:"set \"BAT_VERSION=" "!SELF_TMP!"') do set "SELF_REMOTE_VER=%%v"
set "SELF_REMOTE_VER=!SELF_REMOTE_VER:~1,-1!"
if "!SELF_REMOTE_VER!"=="" goto :self_update_skip

REM Parse local version
for /f "tokens=1,2,3 delims=." %%a in ("!SELF_LOCAL_VER!") do (
    set "_LM=%%a"
    set "_LN=%%b"
    set "_LP=%%c"
)

REM Parse remote version
for /f "tokens=1,2,3 delims=." %%a in ("!SELF_REMOTE_VER!") do (
    set "_RM=%%a"
    set "_RN=%%b"
    set "_RP=%%c"
)

REM Guard: all six parts must be present before comparing
if "!_RM!"=="" goto :self_update_skip
if "!_RN!"=="" goto :self_update_skip
if "!_RP!"=="" goto :self_update_skip
if "!_LM!"=="" goto :self_update_skip
if "!_LN!"=="" goto :self_update_skip
if "!_LP!"=="" goto :self_update_skip

REM Compare: major, then minor, then patch
set "_NEED_UPDATE=0"
if !_RM! gtr !_LM! set "_NEED_UPDATE=1"
if !_RM! equ !_LM! (
    if !_RN! gtr !_LN! set "_NEED_UPDATE=1"
    if !_RN! equ !_LN! (
        if !_RP! gtr !_LP! set "_NEED_UPDATE=1"
    )
)

if "!_NEED_UPDATE!"=="1" (
    echo %CYAN%  Launcher update available: !SELF_LOCAL_VER! → !SELF_REMOTE_VER!%RESET%
    echo %GRAY%  Updating pykorf.bat...%RESET%
    copy /y "!SELF_TMP!" "%~f0" >nul 2>&1
    if !errorlevel! equ 0 (
        del "!SELF_TMP!" >nul 2>&1
        echo %GREEN%  OK  Launcher updated. Relaunching...%RESET%
        echo.
        endlocal
        call "%~f0" %*
        exit /b
    ) else (
        del "!SELF_TMP!" >nul 2>&1
        echo %YELLOW%  WARNING: Could not replace launcher — permission denied?%RESET%
        echo %GRAY%  Continuing with existing version.%RESET%
        echo.
    )
)

:self_update_skip
if defined SELF_TMP del "!SELF_TMP!" >nul 2>&1

REM ============================================
REM Uninstall flag check
REM ============================================
if /i "%~1"=="/uninstall" goto :uninstall
if /i "%~1"=="--uninstall" goto :uninstall
if /i "%~1"=="--uninstall-app" (
    set "CONFIRM=Y"
    goto :uninstall_app_only
)

REM ============================================
REM Fast path - already installed
REM ============================================
if not exist "%APPDATA_DIR%\.venv\Scripts\python.exe" goto :first_install

set "INST_VER=0.0.0"
if exist "%APPDATA_DIR%\VERSION" set /p INST_VER=<"%APPDATA_DIR%\VERSION"
set "INST_MAJOR=0"
for /f "tokens=1 delims=." %%a in ("!INST_VER!") do set "INST_MAJOR=%%a"

if not "!INST_MAJOR!"=="!BAT_MAJOR!" (
    cls
    echo.
    echo %RED%  +-------------------------------------------------------+%RESET%
    echo %RED%  ^|   Launcher Outdated                                   ^|%RESET%
    echo %RED%  ^|                                                       ^|%RESET%
    echo %RED%  ^|   This launcher is not compatible with the installed  ^|%RESET%
    echo %RED%  ^|   version of pyKorf.                                  ^|%RESET%
    echo %RED%  ^|                                                       ^|%RESET%
    echo %RED%  ^|   Contact your administrator for the updated          ^|%RESET%
    echo %RED%  ^|   pykorf.bat file.                                    ^|%RESET%
    echo %RED%  +-------------------------------------------------------+%RESET%
    echo.
    pause
    exit /b 1
)

REM ============================================
REM App version update check (GitHub API)
REM ============================================
set "APP_ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"

for /f %%v in ('powershell -command "try { (Invoke-RestMethod -Uri 'https://api.github.com/repos/Unmask06/pykorf/releases/latest' -TimeoutSec 15).tag_name } catch { '' }" 2^>nul') do set "REMOTE_APP_VER=%%v"
set "REMOTE_APP_VER=!REMOTE_APP_VER:v=!"
if "!REMOTE_APP_VER!"=="" goto :app_update_done
if "!INST_VER!"=="!REMOTE_APP_VER!" goto :app_update_done

REM Versions differ - download and apply update
echo %CYAN%  Updating pyKorf !INST_VER! ? !REMOTE_APP_VER!...%RESET%
echo.

set "UPD_ZIP=%TEMP%\pykorf_update.zip"
set "UPD_DIR=%TEMP%\pykorf_upd"

curl -L --fail --silent --max-time 120 -o "!UPD_ZIP!" "!APP_ZIP_URL!" 2>nul
if %errorlevel% neq 0 (
    echo %YELLOW%  Update download failed - launching existing version%RESET%
    echo.
    goto :app_update_done
)

if exist "!UPD_DIR!" rd /s /q "!UPD_DIR!"
mkdir "!UPD_DIR!"
tar -xf "!UPD_ZIP!" -C "!UPD_DIR!" >nul 2>&1
if !errorlevel! neq 0 (
    del "!UPD_ZIP!" >nul 2>&1
    rd /s /q "!UPD_DIR!" >nul 2>&1
    echo %YELLOW%  Update extraction failed - launching existing version%RESET%
    echo.
    goto :app_update_done
)
del "!UPD_ZIP!" >nul 2>&1

REM Overlay new files onto APPDATA_DIR, preserving data/ and config.json
robocopy "!UPD_DIR!" "%APPDATA_DIR%" /E /XD "data" /XF "config.json" /NFL /NDL /NJH /NJS >nul 2>&1
rd /s /q "!UPD_DIR!" >nul 2>&1

REM Delete .venv and rebuild fresh
cd /d "%APPDATA_DIR%"
if exist ".venv" (
    echo %GRAY%  Removing old virtual environment...%RESET%
    rd /s /q ".venv" >nul 2>&1
)

echo %GRAY%  Creating fresh virtual environment...%RESET%
set "PYTHON_EXE=py -3.13"
!PYTHON_EXE! -m uv venv .venv --quiet

echo %GRAY%  Installing dependencies...%RESET%
py -3.13 -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
if %errorlevel% neq 0 (
    echo %YELLOW%  Dependency installation failed - launching existing version%RESET%
    echo.
    goto :app_update_done
)

echo %GREEN%  OK  Updated to !REMOTE_APP_VER!%RESET%
echo.

:app_update_done

cd /d "%APPDATA_DIR%"

REM -- Launch with auto-repair on venv errors ------------------------------------
".venv\Scripts\pykorf.exe" --no-debug
set "LAUNCH_ERR=%errorlevel%"
if "!LAUNCH_ERR!"=="0" exit /b

REM Non-zero exit - attempt one venv rebuild before giving up
echo.
echo %YELLOW%  pyKorf exited with error !LAUNCH_ERR! - attempting venv repair...%RESET%
echo.

if exist ".venv" rd /s /q ".venv" >nul 2>&1
py -3.13 -m uv venv .venv --quiet
if %errorlevel% neq 0 (
    echo %RED%  Failed to create virtual environment.%RESET%
    goto :launch_reinstall
)

set "VENV_UV=%APPDATA_DIR%\.venv\Scripts\uv.exe"
if exist "!VENV_UV!" (
    "!VENV_UV!" pip install --python ".venv\Scripts\python.exe" -e . --quiet
) else (
    py -3.13 -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
)
if %errorlevel% neq 0 (
    echo %RED%  Failed to reinstall dependencies.%RESET%
    goto :launch_reinstall
)

echo %GREEN%  OK Venv repaired - relaunching...%RESET%
echo.
".venv\Scripts\pykorf.exe" --no-debug
if %errorlevel% equ 0 exit /b

:launch_reinstall
echo.
echo %YELLOW%  Venv repair failed - attempting full reinstall...%RESET%
echo.

REM Run uninstall_app_only silently (CONFIRM=Y skips prompt)
set "CONFIRM=Y"
goto :uninstall_app_only_no_pause

:uninstall_app_only_no_pause
echo %GRAY%  Removing application...%RESET%
if exist "%APPDATA_DIR%\data" (
    robocopy "%APPDATA_DIR%\data" "%TEMP%\pykorf_data_bak" /E /MOVE /NFL /NDL /NJH /NJS >nul 2>&1
)
if exist "%APPDATA_DIR%\config.json" (
    copy /y "%APPDATA_DIR%\config.json" "%TEMP%\pykorf_cfg_bak.json" >nul 2>&1
)
rd /s /q "%APPDATA_DIR%" >nul 2>&1
mkdir "%APPDATA_DIR%" >nul 2>&1
if exist "%TEMP%\pykorf_data_bak" (
    robocopy "%TEMP%\pykorf_data_bak" "%APPDATA_DIR%\data" /E /MOVE /NFL /NDL /NJH /NJS >nul 2>&1
)
if exist "%TEMP%\pykorf_cfg_bak.json" (
    copy /y "%TEMP%\pykorf_cfg_bak.json" "%APPDATA_DIR%\config.json" >nul 2>&1
    del "%TEMP%\pykorf_cfg_bak.json" >nul 2>&1
)
echo %GREEN%  OK  Application removed.%RESET%
echo.

REM Download fresh release before reinstall
echo %GRAY%  Downloading latest release...%RESET%
set "REINSTALL_ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"
set "REINSTALL_ZIP_PATH=%TEMP%\pykorf_reinstall.zip"
set "REINSTALL_EXTRACT_DIR=%TEMP%\pykorf_reinstall"

curl -L --fail --silent --max-time 120 -o "!REINSTALL_ZIP_PATH!" "!REINSTALL_ZIP_URL!" 2>nul
if %errorlevel% neq 0 (
    echo %RED%  Failed to download latest release.%RESET%
    echo %YELLOW%  Please check your internet connection and try again.%RESET%
    goto :launch_failed
)

if exist "!REINSTALL_EXTRACT_DIR!" rd /s /q "!REINSTALL_EXTRACT_DIR!"
mkdir "!REINSTALL_EXTRACT_DIR!"
powershell -Command "Expand-Archive -Path '!REINSTALL_ZIP_PATH!' -DestinationPath '!REINSTALL_EXTRACT_DIR!' -Force" 2>nul
if %errorlevel% neq 0 (
    echo %RED%  Failed to extract release archive.%RESET%
    del "!REINSTALL_ZIP_PATH!" >nul 2>&1
    goto :launch_failed
)

REM Copy files to APPDATA_DIR (preserving data/ and config.json that were restored)
robocopy "!REINSTALL_EXTRACT_DIR!" "%APPDATA_DIR%" /E /NFL /NDL /NJH /NJS >nul 2>&1
del "!REINSTALL_ZIP_PATH!" >nul 2>&1
rd /s /q "!REINSTALL_EXTRACT_DIR!" >nul 2>&1

if not exist "%APPDATA_DIR%\pyproject.toml" (
    echo %RED%  Downloaded release is missing pyproject.toml.%RESET%
    goto :launch_failed
)

REM Now perform fresh install
echo %GRAY%  Performing fresh installation...%RESET%
cd /d "%APPDATA_DIR%"
set "PYTHON_EXE=py -3.13"
!PYTHON_EXE! -m uv venv .venv --quiet
py -3.13 -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
if %errorlevel% neq 0 (
    echo %RED%  Failed to install dependencies.%RESET%
    goto :launch_failed
)
echo %GREEN%  OK  Installation complete.%RESET%
echo.
echo %GRAY%  Launching pyKorf...%RESET%
echo.
".venv\Scripts\pykorf.exe" --no-debug
if %errorlevel% equ 0 exit /b

:launch_failed
echo.
echo %RED%  +---------------------------------------------------------+%RESET%
echo %RED%  ^|   pyKorf failed to start                                ^|%RESET%
echo %RED%  ^|                                                         ^|%RESET%
echo %RED%  ^|   Automatic repair and reinstall were attempted but     ^|%RESET%
echo %RED%  ^|   did not resolve the issue.                            ^|%RESET%
echo %RED%  ^|                                                         ^|%RESET%
echo %RED%  ^|   Please contact: Prasanna Palanivel                    ^|%RESET%
echo %RED%  +---------------------------------------------------------+%RESET%
echo.
pause
exit /b 1

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
echo %GRAY%  ---------------------------------------------------------%RESET%
echo %WHITE%    First-time setup  -  Steps 1 - 4  -  Runs once%RESET%
echo %GRAY%  ---------------------------------------------------------%RESET%
echo.

REM ============================================
REM STEP 1: Python Detection (3.13)
REM ============================================
echo %CYAN%  +-- [1 / 4]  Python Runtime%RESET%
echo %CYAN%  ^|%RESET%

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

echo %CYAN%  ^|%RESET%  %YELLOW%  Python 3.13 not found - attempting automatic install...%RESET%
echo %CYAN%  ^|%RESET%

winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
if %errorlevel% neq 0 (
    echo %CYAN%  ^|%RESET%
    echo %CYAN%  +--%RESET%  %RED%X  Automatic install failed%RESET%
    echo %WHITE%     Install Python 3.13 manually and run pykorf.bat again.%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  ^|%RESET%  %GREEN%OK  Python 3.13 installed%RESET%
echo %CYAN%  +--%RESET%
echo.
echo %YELLOW%  +-------------------------------------------------------+%RESET%
echo %YELLOW%  ^|   Restart required                                    ^|%RESET%
echo %YELLOW%  ^|   Close this window and run pykorf.bat again.         ^|%RESET%
echo %YELLOW%  +-------------------------------------------------------+%RESET%
echo.
pause
exit /b

:python_found
for /f "tokens=*" %%v in ('!PYTHON_EXE! --version') do set "PYVER_STR=%%v"
echo %CYAN%  ^|%RESET%  %GREEN%OK  !PYVER_STR! detected%RESET%
echo %CYAN%  +--%RESET%
echo.

REM ============================================
REM STEP 2: UV Package Manager
REM ============================================
echo %CYAN%  +-- [2 / 4]  Package Manager%RESET%
echo %CYAN%  ^|%RESET%

!PYTHON_EXE! -m uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %CYAN%  ^|%RESET%  %GRAY%  Installing uv...%RESET%
    !PYTHON_EXE! -m pip install --quiet uv
    if %errorlevel% neq 0 (
        echo %CYAN%  ^|%RESET%  %YELLOW%  uv unavailable - falling back to pip%RESET%
        set "USE_UV=0"
    ) else (
        set "USE_UV=1"
    )
) else (
    set "USE_UV=1"
)

if "!USE_UV!"=="1" (
    echo %CYAN%  ^|%RESET%  %GREEN%OK  uv ready%RESET%
) else (
    echo %CYAN%  ^|%RESET%  %GREEN%OK  pip ready%RESET%
)
echo %CYAN%  +--%RESET%
echo.

REM ============================================
REM STEP 3: Download pyKorf
REM ============================================
echo %CYAN%  +-- [3 / 4]  Download pyKorf%RESET%
echo %CYAN%  ^|%RESET%

set "ZIP_URL=https://github.com/Unmask06/pykorf/releases/latest/download/pykorf-v!BAT_MAJOR!.zip"
set "ZIP_PATH=%TEMP%\pykorf.zip"

echo %CYAN%  ^|%RESET%  %GRAY%  Downloading...%RESET%
curl -L --fail --silent --max-time 120 -o "!ZIP_PATH!" "!ZIP_URL!"
if %errorlevel% neq 0 (
    echo %CYAN%  ^|%RESET%
    echo %CYAN%  +--%RESET%  %RED%X  Download failed%RESET%
    echo.
echo %YELLOW%  +-------------------------------------------------------+%RESET%
echo %YELLOW%  ^|   If pyKorf has released a new major version,         ^|%RESET%
echo %YELLOW%  ^|   contact your administrator for the updated           ^|%RESET%
echo %YELLOW%  ^|   pykorf.bat file.                                    ^|%RESET%
echo %YELLOW%  +-------------------------------------------------------+%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  ^|%RESET%  %GRAY%  Extracting...%RESET%
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"
powershell -Command "Expand-Archive -Path '!ZIP_PATH!' -DestinationPath '%APPDATA_DIR%' -Force"
if %errorlevel% neq 0 (
    echo %CYAN%  ^|%RESET%
    echo %CYAN%  +--%RESET%  %RED%X  Extraction failed%RESET%
    echo.
    pause
    exit /b 1
)
del "!ZIP_PATH!" >nul 2>&1

echo %CYAN%  ^|%RESET%  %GREEN%OK  Downloaded and extracted%RESET%
echo %CYAN%  +--%RESET%
echo.

REM ============================================
REM STEP 4: Virtual Environment & Dependencies
REM ============================================
:env_setup
echo %CYAN%  +-- [4 / 4]  Virtual Environment%RESET%
echo %CYAN%  ^|%RESET%

cd /d "%APPDATA_DIR%"

if not exist ".venv\Scripts\python.exe" (
    echo %CYAN%  ^|%RESET%  %GRAY%  Creating environment...%RESET%
    if "!USE_UV!"=="1" (
        !PYTHON_EXE! -m uv venv .venv --quiet
    ) else (
        !PYTHON_EXE! -m venv .venv
    )
    if %errorlevel% neq 0 (
        echo %CYAN%  ^|%RESET%
        echo %CYAN%  +--%RESET%  %RED%X  Failed to create environment%RESET%
        echo.
        pause
        exit /b 1
    )
)

echo %CYAN%  ^|%RESET%  %GRAY%  Installing dependencies...%RESET%
if "!USE_UV!"=="1" (
    !PYTHON_EXE! -m uv pip install --python ".venv\Scripts\python.exe" -e . --quiet
) else (
    ".venv\Scripts\python.exe" -m pip install -e . --quiet
)

if %errorlevel% neq 0 (
    echo %CYAN%  ^|%RESET%
    echo %CYAN%  +--%RESET%  %RED%X  Dependency installation failed%RESET%
    echo.
    pause
    exit /b 1
)

echo %CYAN%  ^|%RESET%  %GREEN%OK  Environment ready%RESET%
echo %CYAN%  +--%RESET%
echo.
echo %GRAY%  ---------------------------------------------------------%RESET%
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
echo %GRAY%  ---------------------------------------------------------%RESET%
echo %WHITE%    Starting...%RESET%
echo %GRAY%  ---------------------------------------------------------%RESET%
echo.
echo %GREEN%  INFO: Your default browser will open automatically.%RESET%
echo %GREEN%        Do not close this terminal while pyKorf is running.%RESET%
echo.

".venv\Scripts\pykorf.exe" --no-debug

endlocal
goto :eof

REM ============================================
REM Uninstall
REM ============================================
:uninstall
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
echo %GRAY%  ---------------------------------------------------------%RESET%
echo %WHITE%    Uninstall pyKorf%RESET%
echo %GRAY%  ---------------------------------------------------------%RESET%
echo.

if not exist "%APPDATA_DIR%" (
    echo %YELLOW%  pyKorf is not installed.%RESET%
    echo.
    pause
    exit /b 0
)

echo %WHITE%  Choose what to remove:%RESET%
echo.
echo %WHITE%    [1]  App only          %GRAY%(keeps your saved data and settings)%RESET%
echo %WHITE%    [2]  Complete uninstall %GRAY%(removes everything including saved data)%RESET%
echo %WHITE%    [0]  Cancel%RESET%
echo.
set /p UNINST_CHOICE=  Enter choice:

if "!UNINST_CHOICE!"=="0" (
    echo.
    echo %GRAY%  Cancelled.%RESET%
    echo.
    pause
    exit /b 0
)

if "!UNINST_CHOICE!"=="1" goto :uninstall_app_only
if "!UNINST_CHOICE!"=="2" goto :uninstall_complete

echo %YELLOW%  Invalid choice. Exiting.%RESET%
echo.
pause
exit /b 1

:uninstall_app_only
echo.
echo %WHITE%  This will remove the pyKorf application but keep your saved data.%RESET%
echo.
if /i "!CONFIRM!"=="Y" goto :confirm_skip
set /p CONFIRM=  Are you sure? (Y/N):
:confirm_skip
if /i not "!CONFIRM!"=="Y" (
    echo.
    echo %GRAY%  Cancelled.%RESET%
    echo.
    pause
    exit /b 0
)
echo.
echo %GRAY%  Removing application...%RESET%
REM Preserve data/ and config.json - move them out, wipe dir, restore
if exist "%APPDATA_DIR%\data" (
    robocopy "%APPDATA_DIR%\data" "%TEMP%\pykorf_data_bak" /E /MOVE /NFL /NDL /NJH /NJS >nul 2>&1
)
if exist "%APPDATA_DIR%\config.json" (
    copy /y "%APPDATA_DIR%\config.json" "%TEMP%\pykorf_cfg_bak.json" >nul 2>&1
)
rd /s /q "%APPDATA_DIR%" >nul 2>&1
mkdir "%APPDATA_DIR%" >nul 2>&1
if exist "%TEMP%\pykorf_data_bak" (
    robocopy "%TEMP%\pykorf_data_bak" "%APPDATA_DIR%\data" /E /MOVE /NFL /NDL /NJH /NJS >nul 2>&1
)
if exist "%TEMP%\pykorf_cfg_bak.json" (
    copy /y "%TEMP%\pykorf_cfg_bak.json" "%APPDATA_DIR%\config.json" >nul 2>&1
    del "%TEMP%\pykorf_cfg_bak.json" >nul 2>&1
)
if exist "%APPDATA_DIR%\.venv" goto :uninstall_failed
echo %GREEN%  OK  Application removed. Your saved data is intact.%RESET%
echo %WHITE%     Run pykorf.bat again to reinstall.%RESET%
echo.
pause
exit /b 0

:uninstall_complete
echo.
echo %RED%  This will permanently remove pyKorf and all saved data.%RESET%
echo.
set /p CONFIRM=  Are you sure? (Y/N):
if /i not "!CONFIRM!"=="Y" (
    echo.
    echo %GRAY%  Cancelled.%RESET%
    echo.
    pause
    exit /b 0
)
echo.
echo %GRAY%  Removing all pyKorf data...%RESET%
rd /s /q "%APPDATA_DIR%" >nul 2>&1
if exist "%APPDATA_DIR%" goto :uninstall_failed
echo %GREEN%  OK  pyKorf has been completely removed.%RESET%
echo %WHITE%     You can delete pykorf.bat manually.%RESET%
echo.
pause
exit /b 0

:uninstall_failed
echo.
echo %RED%  +-------------------------------------------------------+%RESET%
echo %RED%  ^|   Uninstall Failed                                    ^|%RESET%
echo %RED%  ^|                                                       ^|%RESET%
echo %RED%  ^|   Could not remove pyKorf files.                      ^|%RESET%
echo %RED%  ^|   Close any open pyKorf windows and try again, or    ^|%RESET%
echo %RED%  ^|   contact the developer for assistance.               ^|%RESET%
echo %RED%  +-------------------------------------------------------+%RESET%
echo.
pause
exit /b 1
