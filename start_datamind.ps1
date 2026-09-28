# DataMind Startup Script for PowerShell
# This script starts the DataMind ML Platform

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
if (-not (Test-Path "app.py")) {
    Write-Host "ERROR: app.py not found in current directory" -ForegroundColor Red
    Write-Host "Please run this script from the DataMind project root directory" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Install dependencies if needed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -e . > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -e .
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Dependencies installed/verified." -ForegroundColor Green
Write-Host ""

# Start the Streamlit application
Write-Host "Starting DataMind..." -ForegroundColor Green
Write-Host "The application will open in your default browser." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Cyan
Write-Host ""

streamlit run app.py
