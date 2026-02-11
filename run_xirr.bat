@echo off
REM XIRR Calculator Startup Script for Windows
REM This script sets up the virtual environment and runs the calculator

echo ============================================================
echo   XIRR Calculator Setup
echo ============================================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        echo Please ensure Python 3.7 or higher is installed and in PATH
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import pandas, numpy, scipy, reportlab" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed successfully
) else (
    echo Dependencies already installed
)

echo.

REM Run the XIRR calculator
if "%~1"=="" (
    REM No argument provided, use default behavior
    python xirr_calculator.py
) else (
    REM CSV file path provided as argument
    python xirr_calculator.py %1
)

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

pause
