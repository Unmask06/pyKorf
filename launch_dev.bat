@echo off
REM ============================================
REM pyKorf Dev Launcher
REM Starts the FastAPI backend (port 8000) and
REM the Vite frontend dev server (port 5173).
REM ============================================
setlocal

set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%"
set "FRONTEND_DIR=%ROOT%pykorf\app\frontend"

echo.
echo  pyKorf Dev Server
echo  =================
echo.

REM --- Check Node.js ---
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm not found. Install Node.js to run the frontend dev server.
    pause
    exit /b 1
)

REM --- Check uv ---
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] uv not found. Install uv to run the backend.
    pause
    exit /b 1
)

REM --- Check frontend node_modules ---
if not exist "%FRONTEND_DIR%\node_modules\" (
    echo [INFO] Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%" && call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install failed.
        pause
        exit /b 1
    )
    echo.
)

echo [1/2] Starting FastAPI backend on port 8000...
start "pyKorf Backend" /D "%BACKEND_DIR%" cmd /c uv run pykorf --debug --port 8000

REM Wait for backend to be ready (check if port 8000 is listening)
echo [WAIT] Waiting for backend to start...
for /l %%i in (1,1,30) do (
    netstat -ano | findstr ":8000.*LISTENING" >nul 2>&1
    if not errorlevel 1 (
        echo [OK] Backend is ready!
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
    echo   ... waiting (%%i/30)
)
echo [WARN] Backend may not have started correctly. Check the backend window.
:backend_ready

echo [2/3] Generating TypeScript types from OpenAPI schema...
cd /d "%FRONTEND_DIR%" && call npm run generate-types
if %errorlevel% neq 0 (
    echo [WARN] Type generation failed. Continuing anyway...
)
echo.

echo [3/3] Starting Vite dev server on port 5173...
start "pyKorf Frontend" /D "%FRONTEND_DIR%" cmd /c npm run dev

echo.
echo  Backend  -> http://localhost:8000
echo  Frontend -> http://localhost:5173
echo.
echo  Opening browser to frontend dev server...
timeout /t 2 /nobreak >nul
start "" "http://localhost:5173"
echo.
echo  Close both terminal windows to stop the servers.
echo.
echo  TypeScript types auto-generated from OpenAPI schema.
echo.

exit /b 0
