@echo off
REM DataMind Startup Script
REM This script starts the DataMind ML Platform
REM Run from scripts/ directory

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

REM Determine repository root directory
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
pushd "%ROOT_DIR%"

REM Check if app.py exists in project root
if not exist "app.py" (
    echo ERROR: app.py not found in project root: %CD%
    pause
    popd
    exit /b 1
)

REM Create .env from .env.example if missing
if not exist ".env" (
    if exist ".env.example" (
        echo Creating .env configuration from .env.example...
        copy /y ".env.example" ".env" >nul
        echo .env file created successfully.
    )
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
        popd
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

python -m streamlit run app.py

popd
pause

