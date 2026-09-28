@echo off
REM DataMind Startup Script
REM This script starts the DataMind ML Platform

echo ====================================
echo    DataMind ML Platform
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if we're in the correct directory
if not exist "app.py" (
    echo ERROR: app.py not found in current directory
    echo Please run this script from the DataMind project root directory
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip install -e . >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -e .
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies installed/verified.
echo.

REM Start the Streamlit application
echo Starting DataMind...
echo The application will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
