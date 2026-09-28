# DataMind Setup Script
# This script installs all required dependencies for DataMind

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "   DataMind Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher from https://www.python.org/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python version:" -ForegroundColor Green
Write-Host $pythonVersion
Write-Host ""

# Check if pip is available
$pipVersion = pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install pip or reinstall Python with pip included" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "pip version:" -ForegroundColor Green
Write-Host $pipVersion
Write-Host ""

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host ""

# Install project dependencies
Write-Host "Installing DataMind dependencies..." -ForegroundColor Yellow
pip install -e .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================" -ForegroundColor Green
    Write-Host "   Setup Complete!" -ForegroundColor Green
    Write-Host "====================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now start DataMind by running:" -ForegroundColor Cyan
    Write-Host "  .\start_datamind.ps1" -ForegroundColor White
    Write-Host "  or" -ForegroundColor White
    Write-Host "  streamlit run app.py" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Please check the error messages above and try again" -ForegroundColor Yellow
}

Read-Host "Press Enter to exit"
