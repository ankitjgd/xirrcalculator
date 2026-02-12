# XIRR Calculator by Ankit Bhardwaj

A Python tool (CLI + Web App) to calculate the Extended Internal Rate of Return (XIRR) for your trading portfolio with Nifty 50 benchmark comparison.

**Currently supports:** Zerodha
**Coming soon:** Support for other brokers

## 🌐 Web App

**🚀 Try it online:** [https://xirrcalculatorr.streamlit.app](https://xirrcalculatorr.streamlit.app)

Or run locally:
```bash
streamlit run streamlit_app.py
```

## What is XIRR?

XIRR (Extended Internal Rate of Return) is the most accurate way to measure investment performance when you have irregular cash flows (deposits and withdrawals at different times). Unlike simple returns, XIRR accounts for:
- The timing of each deposit and withdrawal
- The time value of money
- Multiple transactions over time

## Features

### Core Features
- **Multi-Account Support**: Analyze multiple Zerodha accounts simultaneously
  - Individual XIRR calculation for each account
  - Combined portfolio XIRR across all accounts
  - Enter portfolio values separately for each account
  - Comprehensive summary comparison table
- **Automatic CSV Detection**: Scans directory and lets you select which accounts to analyze
- **Comprehensive Transaction Parsing**:
  - Fund additions (deposits)
  - Payouts (withdrawals)
  - Quarterly settlements (automatic detection)
- **Robust XIRR Calculation**: Uses multiple optimization methods (Newton-Raphson, Brent's method, grid search)
- **Detailed Investment Summary**:
  - Total amount invested and withdrawn per account
  - Current portfolio value breakdown (holdings + cash)
  - Net gain/loss calculation
  - Simple return percentage
  - Annualized XIRR percentage
- **Nifty 50 Benchmark Comparison** 📊:
  - Automatic comparison with Nifty 50 index performance
  - Shows hypothetical returns if invested in Nifty 50 on same dates
  - Accounts for both investments and withdrawals
  - Displays outperformance/underperformance metrics
  - Calculates value difference between your portfolio and index

### PDF Report Generation 📄
- **Professional PDF Reports**: Generate beautifully formatted PDF reports
  - Saved in `reports/` folder with timestamps
  - All reports are preserved (no auto-deletion)
  - Custom or auto-timestamped filenames
  - Comprehensive portfolio summary
  - Individual account breakdowns (for multi-account)
  - Nifty 50 benchmark comparison included
  - Comparison tables with all key metrics
  - Print-friendly layout

### Organized Folder Structure 📁
- **`ledger/`**: Place your Zerodha CSV files here
- **`reports/`**: PDF reports are automatically saved here with timestamps
- Clean and organized - no clutter in the main directory

### Additional Features
- **Smart Error Handling**: Gracefully handles extreme loss scenarios where XIRR cannot be calculated
- **Virtual Environment Setup**: Automatic dependency installation via startup script
- **Clean Output**: No information duplication, professional formatting

## Quick Start

### Windows - Complete Setup Guide

#### Step 1: Install Python (If Not Already Installed)

1. **Download Python:**
   - Go to https://www.python.org/downloads/
   - Download Python 3.7 or higher (latest stable version recommended)

2. **Install Python:**
   - Run the installer
   - ⚠️ **IMPORTANT**: Check ☑️ "Add Python to PATH" at the bottom of the installer
   - Click "Install Now"
   - Wait for installation to complete

3. **Verify Installation:**
   - Open Command Prompt (press `Win + R`, type `cmd`, press Enter)
   - Type: `python --version`
   - Should show: `Python 3.x.x`
   - If not recognized, see [Windows Troubleshooting](#windows-specific-issues)

#### Step 2: Download the Calculator

1. **Download this repository:**
   - Click the green "Code" button on GitHub
   - Select "Download ZIP"
   - Extract the ZIP file to a folder (e.g., `C:\xirrcalculator`)

2. **Place your CSV files:**
   - Export your Zerodha ledger(s) from Zerodha Console
   - Copy the CSV file(s) to the `ledger/` folder inside the calculator directory
   - The `ledger/` folder will be created automatically on first run if it doesn't exist

#### Step 3: Run the Calculator

**Option A: Double-Click Method (Easiest)**
1. Navigate to the calculator folder
2. Double-click `run_xirr.bat`
3. First run will set up everything (takes 1-2 minutes)
4. Follow the prompts

**Option B: Command Prompt Method**
1. Open Command Prompt
2. Navigate to calculator folder:
   ```cmd
   cd C:\xirrcalculator
   ```
3. Run the script:
   ```cmd
   run_xirr.bat
   ```
   Or for a specific file:
   ```cmd
   run_xirr.bat your-ledger.csv
   ```

**Option C: PowerShell Method**
1. Open PowerShell (right-click Start → Windows PowerShell)
2. Navigate to calculator folder:
   ```powershell
   cd C:\xirrcalculator
   ```
3. Run the script:
   ```powershell
   .\run_xirr.ps1
   ```
   Or for a specific file:
   ```powershell
   .\run_xirr.ps1 your-ledger.csv
   ```

#### First Run Setup
- The script will automatically:
  - Create a virtual environment (30 seconds)
  - Install all required packages (1-2 minutes)
  - Start the calculator
- Subsequent runs will be much faster (immediate start)

#### Using the Calculator

1. **For single CSV file:**
   - Script will detect and use it automatically
   - Or specify: `run_xirr.bat ledger.csv`

2. **For multiple CSV files:**
   - Script will show a list
   - Select which accounts to analyze
   - Press Enter to use all

3. **Enter portfolio values:**
   - Current holdings value (total stocks value)
   - Current available cash
   - Calculator will show results

4. **Save PDF (optional):**
   - Answer 'y' when prompted
   - Enter custom filename or press Enter for auto-name
   - PDF will be saved in the same folder

### macOS / Linux

#### Single Account

1. Export your Zerodha ledger as a CSV file from Zerodha Console
2. Place the CSV file in the `ledger/` folder
3. Run the startup script:

```bash
./run_xirr.sh
```

4. The script will auto-detect CSV files from the `ledger/` folder
5. Enter your current holdings value and available cash when prompted

#### Multiple Accounts

1. Export ledgers for all your Zerodha accounts as CSV files
2. Place all CSV files in the `ledger/` folder
3. Run without specifying a file:

```bash
./run_xirr.sh
```

4. The script will detect all CSV files and let you select which accounts to analyze

### Windows Quick Reference

After completing the setup above, use these commands:

**Command Prompt:**
```cmd
# Auto-detect CSV files
run_xirr.bat

# Specific CSV file
run_xirr.bat your-ledger.csv
```

**PowerShell:**
```powershell
# Auto-detect CSV files
.\run_xirr.ps1

# Specific CSV file
.\run_xirr.ps1 your-ledger.csv
```

**Or just double-click:** `run_xirr.bat` in File Explorer

### What the Startup Scripts Do

The scripts will automatically:
- Create a virtual environment (first run only)
- Install all dependencies (first run only)
- Detect and let you select CSV files
- Run the calculator

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- **Windows users**: Python must be added to PATH during installation

## Installation

### Method 1: Using the Startup Script (Recommended)

No manual installation needed! The startup scripts handle everything automatically.

**macOS/Linux:** Use `run_xirr.sh`
**Windows (Command Prompt):** Use `run_xirr.bat`
**Windows (PowerShell):** Use `run_xirr.ps1`

### Method 2: Manual Installation

#### macOS / Linux

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the calculator:
```bash
python xirr_calculator.py your-ledger.csv
```

#### Windows

1. Create a virtual environment:
```cmd
python -m venv venv
venv\Scripts\activate
```

2. Install required dependencies:
```cmd
pip install -r requirements.txt
```

3. Run the calculator:
```cmd
python xirr_calculator.py your-ledger.csv
```

## Usage

### Using the Startup Script (Easiest)

#### macOS / Linux
```bash
# With default CSV file scanning
./run_xirr.sh

# With specific CSV file
./run_xirr.sh path/to/your-ledger.csv
```

#### Windows (Command Prompt)
```cmd
# With default CSV file scanning
run_xirr.bat

# With specific CSV file
run_xirr.bat path\to\your-ledger.csv
```

#### Windows (PowerShell)
```powershell
# With default CSV file scanning
.\run_xirr.ps1

# With specific CSV file
.\run_xirr.ps1 path\to\your-ledger.csv
```

### Direct Python Execution

If you've manually installed dependencies in a virtual environment:

#### macOS / Linux
```bash
source venv/bin/activate
python xirr_calculator.py ledger-NBN208.csv
```

#### Windows
```cmd
venv\Scripts\activate
python xirr_calculator.py ledger-NBN208.csv
```

### Input Required

When prompted, enter:
- **Current holdings value**: Total market value of all stocks/securities in your portfolio
- **Current available cash**: Available cash balance in your trading account

### Multi-Account Analysis

If you have multiple Zerodha accounts (or want to analyze ledgers from different periods separately):

1. Place all CSV files in the `ledger/` folder
2. Run the calculator:
   ```bash
   ./run_xirr.sh
   ```
3. The calculator will:
   - Detect all CSV files from the `ledger/` folder
   - Let you select which accounts to include
   - Ask for current holdings and cash **for each account separately**

4. Get detailed results:
   - Individual XIRR for each account
   - Combined portfolio XIRR
   - Summary comparison table

**Example multi-account output:**
```
Found 2 CSV files:
  1. ledger-GZW478.csv
  2. ledger-NBN208.csv

Select files to include: [Press Enter for all]

[Processing: ledger-GZW478.csv]
════════════════════════════════════════════════════════════
  Portfolio Value for: ledger-GZW478.csv
════════════════════════════════════════════════════════════
Enter current holdings value (₹): 1500000
Enter current available cash (₹): 50000
  - Holdings: ₹15,00,000.00
  - Cash: ₹50,000.00
  - Total: ₹15,50,000.00

[Processing: ledger-NBN208.csv]
════════════════════════════════════════════════════════════
  Portfolio Value for: ledger-NBN208.csv
════════════════════════════════════════════════════════════
Enter current holdings value (₹): 2000000
Enter current available cash (₹): 30000
  - Holdings: ₹20,00,000.00
  - Cash: ₹30,000.00
  - Total: ₹20,30,000.00

Combined Portfolio Summary
════════════════════════════════════════════════════════════
Total Holdings: ₹35,00,000.00
Total Cash: ₹80,000.00
Total Value: ₹35,80,000.00

INDIVIDUAL ACCOUNT ANALYSIS
════════════════════════════════════════════════════════════
Account: ledger-GZW478.csv
Total invested: ₹46,73,336.00
Current value: ₹15,50,000.00
XIRR: -18.5%

Account: ledger-NBN208.csv
Total invested: ₹50,88,820.00
Current value: ₹20,30,000.00
XIRR: 2.41%

COMBINED PORTFOLIO
════════════════════════════════════════════════════════════
Total invested: ₹97,62,156.00
Current value: ₹35,80,000.00
XIRR: -8.2%

SUMMARY TABLE
═══════════════════════════════════════════════════════════════════════════
Account              Invested     Withdrawn       Current     Gain/Loss
───────────────────────────────────────────────────────────────────────────
ledger-GZW478.csv  ₹46,73,336  ₹10,88,379  ₹15,50,000  ₹-20,34,957
ledger-NBN208.csv  ₹50,88,820  ₹16,48,722  ₹20,30,000  ₹-14,10,098
───────────────────────────────────────────────────────────────────────────
COMBINED           ₹97,62,156  ₹27,37,101  ₹35,80,000  ₹-34,45,055
```

**The summary table shows:**
- Total invested per account
- Total withdrawn (including payouts and quarterly settlements)
- Current portfolio value
- Net gain/loss (accounts for all inflows and outflows)

### PDF Report Generation

After completing the XIRR analysis, you'll be prompted to save a PDF report:

```
============================================================
Would you like to save this report as PDF? (y/n): y

Enter filename (press Enter for 'xirr_report_20260211_174905.pdf'):

Generating PDF report...
✓ PDF report saved successfully: reports/xirr_report_20260211_174905.pdf
```

**PDF Features:**
- 📄 Professional formatting with color-coded headers
- 📊 All analysis sections included (portfolio summary, Nifty 50 comparison, individual accounts)
- 📁 Saved in `reports/` folder with timestamps
- 💾 All reports preserved - no auto-deletion
- 📅 Auto-timestamped filenames ensure no overwriting
- 🖨️ Print-friendly layout

**Perfect for:**
- Tax filing and ITR documentation
- Sharing with financial advisors
- Investment record keeping
- Performance tracking

**Sample Report:**
- 📋 View [`reports/sample_report.pdf`](reports/sample_report.pdf) for an example of the generated report
- Shows multi-account analysis with Nifty 50 comparison

### Single Account Example

```
==================================================
  XIRR Calculator for Zerodha Portfolio
==================================================

Loading ledger: ledger-NBN208.csv
Found 163 fund additions (outflows)
Found 17 withdrawals (inflows)

==================================================
Enter current holdings value (₹): 500000
Enter current available cash (₹): 15000

==================================================
         Investment Analysis
==================================================

First investment date: 2023-05-19
Analysis date: 2026-02-11
Investment period: 997 days (2.73 years)

Total invested: ₹1,234,567.00
Total withdrawn: ₹567,890.00
Current value: ₹515,000.00
  - Holdings: ₹500,000.00
  - Cash: ₹15,000.00

Net gain/loss: ₹-152,677.00

**************************************************
  XIRR: 12.34%
**************************************************

------------------------------------------------------------
  NIFTY 50 BENCHMARK COMPARISON
------------------------------------------------------------

If you had invested the same amounts on the same dates in Nifty 50:
  Portfolio value: ₹480,000.00
  Units held: 234.56
  Current Nifty 50: 2046.78
  Nifty 50 XIRR: 10.25%

✓ Your portfolio OUTPERFORMED Nifty 50 by 2.09%
  Value difference: ₹35,000.00
```

## How It Works

1. **Reads the Zerodha Ledger CSV**: Parses the CSV file exported from Zerodha
2. **Identifies Cash Flows**:
   - **Outflows**: All "Funds added" transactions (money you invested)
   - **Inflows**:
     - "Payout" transactions (money you withdrew)
     - "Quarterly settlement" transactions (funds returned by Zerodha)
   - **Final Value**: Current holdings + available cash (as of today)
3. **Calculates XIRR**: Uses multiple optimization methods:
   - Newton-Raphson method (primary)
   - Brent's method (fallback for complex scenarios)
   - Grid search (for extreme cases)
   - Finds the annualized return rate that makes NPV = 0
4. **Nifty 50 Benchmark Comparison**:
   - Fetches historical Nifty 50 data from Yahoo Finance
   - Simulates buying Nifty 50 units on each investment date
   - Simulates selling proportional units on each withdrawal date
   - Calculates hypothetical portfolio value and XIRR
   - Compares your portfolio performance vs benchmark

## Output Sections

### For Single Account:
1. **Portfolio Summary**: Investment period, transaction counts
2. **Financial Metrics**: Total invested, withdrawn, current value
3. **Performance**: Net gain/loss, simple return, XIRR
4. **Nifty 50 Comparison**: Benchmark performance and outperformance metrics

### For Multiple Accounts:
1. **Individual Account Analysis**: Detailed breakdown per account
2. **Combined Portfolio Analysis**: Aggregate metrics across all accounts
3. **Nifty 50 Benchmark**: Comparison with index performance
4. **Summary Comparison Table**: Side-by-side comparison with gain/loss column
5. **PDF Export Option**: Save professional report with all comparisons

## Understanding Your Results

- **Positive XIRR**: Your investments have generated positive returns
- **Negative XIRR**: Your investments have lost value
- **High XIRR (>30%)**: Exceptional returns - verify your input values
- **Low XIRR (<5%)**: Consider comparing with index funds or other benchmarks

### XIRR vs Simple Returns

Simple Return = (Current Value - Total Invested) / Total Invested × 100

This doesn't account for:
- When you made each investment
- Withdrawals during the period
- Time value of money

XIRR provides a more accurate picture by considering all these factors.

## Troubleshooting

### General Issues

#### "No fund additions found in the ledger"
- Ensure your CSV file contains transactions with "Funds added" in the particulars column
- Verify you're using the correct Zerodha ledger format

#### "Could not converge to a solution"
- This usually happens with very irregular cash flows or extreme values
- Verify your current holdings and cash values are correct
- Ensure you have at least 2 transactions (deposits/withdrawals)

#### "File not found"
- Check that the CSV file path is correct
- Make sure the file is in the same directory or provide the full path

### Windows-Specific Issues

#### "Python is not recognized as an internal or external command"
- Python is not in your system PATH
- Reinstall Python and check "Add Python to PATH" during installation
- Or add Python to PATH manually: System Properties → Environment Variables → PATH

#### "Execution of scripts is disabled on this system" (PowerShell)
- PowerShell execution policy is preventing script execution
- Run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Alternative: Use the batch script (`run_xirr.bat`) instead

#### "Access is denied" or Permission errors
- Run Command Prompt or PowerShell as Administrator
- Or ensure you have write permissions in the directory

#### Virtual environment activation fails
- Close any Python processes or IDEs that might be using the venv
- Delete the `venv` folder and run the script again to recreate it

## Dependencies

The calculator automatically installs these Python packages:
- `pandas` - CSV parsing and data manipulation
- `numpy` - Numerical computations
- `scipy` - Optimization methods for XIRR calculation
- `reportlab` - PDF report generation
- `yfinance` - Fetching Nifty 50 historical data for benchmark comparison

All dependencies are installed automatically when using the startup scripts (`run_xirr.sh`, `run_xirr.bat`, or `run_xirr.ps1`).

## CSV Format

The tool expects a Zerodha ledger CSV with these columns:
- `particulars`: Transaction description (identifies fund additions, payouts, quarterly settlements)
- `posting_date`: Date of transaction (YYYY-MM-DD format)
- `credit`: Credit amount (used for fund additions)
- `debit`: Debit amount (used for payouts and settlements)

**Supported transaction types:**
- "Funds added" → Counted as investment (outflow)
- "Payout" → Counted as withdrawal (inflow)
- "quarterly settlement" → Counted as withdrawal (inflow)

## 🚀 Deploying to Streamlit Cloud

### Step 1: Prepare Repository
Your repository is already set up! The `streamlit_app.py` and required files are ready.

### Step 2: Deploy on Streamlit Cloud

1. **Go to [share.streamlit.io](https://share.streamlit.io)**

2. **Sign in with GitHub**

3. **Click "New app"**

4. **Configure deployment:**
   - Repository: `ankitjgd/xirrcalculator`
   - Branch: `main`
   - Main file path: `streamlit_app.py`

5. **Click "Deploy"**

That's it! Your app will be live in 2-3 minutes at:
```
https://ankitjgd-xirrcalculator.streamlit.app
```

### Step 3: Update README
Once deployed, update the web app link at the top of this README.

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## License

MIT License - Feel free to use and modify

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Disclaimer

This tool is for informational purposes only. Always verify calculations independently and consult with a financial advisor for investment decisions.
