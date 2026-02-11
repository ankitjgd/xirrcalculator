# XIRR Calculator Startup Script for Windows (PowerShell)
# This script sets up the virtual environment and runs the calculator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  XIRR Calculator Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        Write-Host "Please ensure Python 3.7 or higher is installed and in PATH" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Virtual environment created successfully" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Check if dependencies are installed
$depsInstalled = $true
try {
    python -c "import pandas, numpy, scipy, reportlab" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $depsInstalled = $false
    }
} catch {
    $depsInstalled = $false
}

if (-Not $depsInstalled) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "Dependencies already installed" -ForegroundColor Green
}

Write-Host ""

# Run the XIRR calculator
if ($args.Count -eq 0) {
    # No argument provided, use default behavior
    python xirr_calculator.py
} else {
    # CSV file path provided as argument
    python xirr_calculator.py $args[0]
}

# Deactivate virtual environment
deactivate

Write-Host ""
Read-Host "Press Enter to exit"
