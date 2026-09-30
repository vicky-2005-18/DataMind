# DataMind Startup Script for PowerShell
# This script starts the DataMind ML Platform
# Run from scripts/ directory

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   DataMind ML Platform" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python version:" -ForegroundColor Green
Write-Host $pythonVersion
Write-Host ""

# Check if we're in the correct directory
if (-not (Test-Path "..\app.py")) {
    Write-Host "ERROR: app.py not found in parent directory" -ForegroundColor Red
    Write-Host "Please run this script from the scripts/ directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -e .. > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -e ..
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Dependencies installed/verified." -ForegroundColor Green
Write-Host ""

# Clean up any existing storage directory (from ZIP downloads or previous runs)
if (Test-Path "..\storage") {
    Write-Host "Removing existing storage directory..." -ForegroundColor Yellow
    Remove-Item -Path "..\storage" -Recurse -Force
    Write-Host "Storage directory cleaned!" -ForegroundColor Green
}

# Create .env file from .env.example if it doesn't exist
if (-not (Test-Path "..\.env")) {
    if (Test-Path "..\.env.example") {
        Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
        Copy-Item "..\.env.example" "..\.env"
        Write-Host ".env file created successfully!" -ForegroundColor Green
    } else {
        Write-Host "WARNING: .env.example not found. Creating minimal .env file..." -ForegroundColor Yellow
        @"
DATAMIND_STORAGE_DIR=./storage
DATAMIND_LOG_LEVEL=INFO
DATAMIND_MAX_UPLOAD_MIB=10
DATAMIND_MAX_ROWS=20000
DATAMIND_MAX_COLUMNS=100
DATAMIND_DEFAULT_SEED=42
OMP_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1
"@ | Out-File -FilePath "..\.env" -Encoding utf8
        Write-Host "Minimal .env file created!" -ForegroundColor Green
    }
} else {
    Write-Host ".env file already exists. Skipping creation." -ForegroundColor Green
}

Write-Host ""

# Start the Streamlit application
Write-Host "Starting DataMind..." -ForegroundColor Green
Write-Host "The application will open in your default browser." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Cyan
Write-Host ""

Set-Location ..
python -m streamlit run app.py
