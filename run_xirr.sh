#!/bin/bash

# XIRR Calculator Startup Script
# This script sets up the virtual environment and runs the calculator

echo "===================================================="
echo "  XIRR Calculator Setup"
echo "===================================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import pandas, numpy, scipy" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        deactivate
        exit 1
    fi
    echo "Dependencies installed successfully"
else
    echo "Dependencies already installed"
fi

echo ""

# Run the XIRR calculator
if [ -z "$1" ]; then
    # No argument provided, use default CSV file
    python xirr_calculator.py
else
    # CSV file path provided as argument
    python xirr_calculator.py "$1"
fi

# Deactivate virtual environment
deactivate
