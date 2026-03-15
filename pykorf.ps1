# pyKorf Launcher - PowerShell Version
# Auto-installs Python 3.13 and uv if needed, then runs the pyKorf TUI

param(
    [switch]$Debug
)

$ErrorActionPreference = "Continue"

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDataDir = "$env:APPDATA\pyKorf"

# ============================================
# Clean Output Header
# ============================================
Clear-Host
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host "           ██████╗  ██████╗ ██╗     ██╗     ██╗███╗   ██╗███████╗" -ForegroundColor Cyan
Write-Host "           ██╔══██╗██╔═══██╗██║     ██║     ██║████╗  ██║██╔════╝" -ForegroundColor Cyan
Write-Host "           ██████╔╝██║   ██║██║     ██║     ██║██╔██╗ ██║█████╗  " -ForegroundColor Cyan
Write-Host "           ██╔══██╗██║   ██║██║     ██║     ██║██║╚██╗██║██╔══╝  " -ForegroundColor Cyan
Write-Host "           ██║  ██║╚██████╔╝███████╗███████╗██║██║ ╚████║███████╗" -ForegroundColor Cyan
Write-Host "           ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "                    Enterprise Hydraulic Modeling Toolkit" -ForegroundColor Gray
Write-Host ""

# ============================================
# STEP 1: Check and Install Python 3.13
# ============================================
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Cyan
Write-Host ""

$PythonCommand = Get-Command "py" -ErrorAction SilentlyContinue
if ($null -eq $PythonCommand) {
    $PythonFound = $false
} else {
    try {
        $pythonVersion = & py -3.13 --version 2>&1
        $PythonFound = ($LASTEXITCODE -eq 0)
    } catch {
        $PythonFound = $false
    }
}

if (-not $PythonFound) {
    Write-Host ""
    Write-Host "⚠  Python 3.13 is not installed." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Installing Python 3.13..." -ForegroundColor Gray
    Write-Host ""
    
    winget install --id Python.Python.3.13 --scope user --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Installation failed." -ForegroundColor Red
        Write-Host "Please install Python 3.13 manually from https://www.python.org/downloads/"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    Write-Host ""
    Write-Host "✓ Python 3.13 installed successfully." -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " One more step required!" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host " Please CLOSE this terminal and" -ForegroundColor White
    Write-Host " double-click pykorf.ps1 again." -ForegroundColor White
    Write-Host ""
    Write-Host " This ensures Python is properly configured." -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 0
}

$pythonVersion = & py -3.13 --version 2>&1
Write-Host "✓ Found $pythonVersion" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 2: Check and Install uv
# ============================================
Write-Host "[2/4] Checking package manager..." -ForegroundColor Cyan
Write-Host ""

$uvCheck = & py -3.13 -m pip show uv 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Installing uv..." -ForegroundColor Gray
    Write-Host ""
    
    & py -3.13 -m pip install uv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Installation failed." -ForegroundColor Red
        Write-Host "Please install uv manually: py -3.13 -m pip install uv"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host ""
    Write-Host "✓ uv installed successfully." -ForegroundColor Green
    Write-Host ""
}

Write-Host "✓ Package manager ready" -ForegroundColor Green
Write-Host ""

# ============================================
# STEP 3: Version Check and File Setup
# ============================================
Write-Host "[3/4] Setting up application..." -ForegroundColor Cyan
Write-Host ""

# Read version from the extracted zip folder (next to this script file)
$CurrentVersion = "unknown"
if (Test-Path "$ScriptDir\VERSION") {
    $CurrentVersion = Get-Content "$ScriptDir\VERSION" -First 1
}

# Read installed version from APPDATA
$InstalledVersion = "none"
if (Test-Path "$AppDataDir\VERSION") {
    $InstalledVersion = Get-Content "$AppDataDir\VERSION" -First 1
}

Write-Host "   Current version : $CurrentVersion" -ForegroundColor Gray
Write-Host "   Installed       : $InstalledVersion" -ForegroundColor Gray
Write-Host ""

# Compare versions - if different, wipe and reinstall
if ($CurrentVersion -eq $InstalledVersion) {
    Write-Host "✓ Already up to date." -ForegroundColor Green
} else {
    Write-Host "  Updating to version $CurrentVersion..." -ForegroundColor Yellow
    
    # Remove only the old package code, keep user data (config.json, data/)
    if (Test-Path "$AppDataDir\pykorf") {
        Remove-Item -Recurse -Force "$AppDataDir\pykorf"
    }
    
    # Ensure APPDATA directory exists (preserve user data)
    if (-not (Test-Path "$AppDataDir")) {
        New-Item -ItemType Directory -Path "$AppDataDir" | Out-Null
    }
    
    # Copy application files
    Copy-Item -Recurse -Force "$ScriptDir\pykorf" "$AppDataDir\pykorf" -ErrorAction SilentlyContinue
    Copy-Item -Force "$ScriptDir\pyproject.toml" "$AppDataDir\" -ErrorAction SilentlyContinue
    Copy-Item -Force "$ScriptDir\VERSION" "$AppDataDir\" -ErrorAction SilentlyContinue
    
    Write-Host "✓ Version $CurrentVersion installed." -ForegroundColor Green
}

Write-Host ""

# ============================================
# STEP 4: Create Venv and Install Dependencies
# ============================================
Write-Host "[4/4] Preparing your environment..." -ForegroundColor Cyan
Write-Host ""

Set-Location "$AppDataDir"

# Create venv with Python 3.13 if it doesn't exist
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & py -3.13 -m venv .venv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Failed to create environment." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Install dependencies using uv (targeting the venv)
& py -3.13 -m uv pip install --python "$AppDataDir\.venv\Scripts\python.exe" -e . 2>&1 | Out-Null

if ($LASTEXITCODE -ne 0) {
    & "$AppDataDir\.venv\Scripts\python.exe" -m pip install -e . 2>&1 | Out-Null
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "✗ Failed to install dependencies." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "✓ Environment ready." -ForegroundColor Green
Write-Host ""

# Clear screen before launching
Clear-Host

# ============================================
# Launch pyKorf TUI with Splash Screen
# ============================================
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host ""
Write-Host "           ██████╗  ██████╗ ██╗     ██╗     ██╗███╗   ██╗███████╗" -ForegroundColor Cyan
Write-Host "           ██╔══██╗██╔═══██╗██║     ██║     ██║████╗  ██║██╔════╝" -ForegroundColor Cyan
Write-Host "           ██████╔╝██║   ██║██║     ██║     ██║██╔██╗ ██║█████╗  " -ForegroundColor Cyan
Write-Host "           ██╔══██╗██║   ██║██║     ██║     ██║██║╚██╗██║██╔══╝  " -ForegroundColor Cyan
Write-Host "           ██║  ██║╚██████╔╝███████╗███████╗██║██║ ╚████║███████╗" -ForegroundColor Cyan
Write-Host "           ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "                    Enterprise Hydraulic Modeling Toolkit" -ForegroundColor Gray
Write-Host ""
Write-Host ""
Write-Host "   Starting pyKorf..." -ForegroundColor Cyan
Write-Host ""
Write-Host "   ⠋ Initializing..." -ForegroundColor Gray
Write-Host ""

& "$AppDataDir\.venv\Scripts\python.exe" -m pykorf
