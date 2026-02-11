# XIRR Calculator for Zerodha Portfolio

A Python CLI tool to calculate the Extended Internal Rate of Return (XIRR) for your Zerodha trading account.

## What is XIRR?

XIRR (Extended Internal Rate of Return) is the most accurate way to measure investment performance when you have irregular cash flows (deposits and withdrawals at different times). Unlike simple returns, XIRR accounts for:
- The timing of each deposit and withdrawal
- The time value of money
- Multiple transactions over time

## Features

- **Multi-Account Support**: Analyze multiple Zerodha accounts simultaneously
  - Individual XIRR calculation for each account
  - Combined portfolio XIRR across all accounts
  - Enter portfolio values separately for each account
- **Automatic CSV Detection**: Scans directory and lets you select which accounts to analyze
- **Comprehensive Transaction Parsing**:
  - Fund additions (deposits)
  - Payouts (withdrawals)
  - Quarterly settlements
- **Robust XIRR Calculation**: Uses multiple optimization methods for accuracy
- **Detailed Investment Summary**:
  - Total amount invested and withdrawn per account
  - Current portfolio value
  - Net gain/loss
  - Simple return percentage
  - Annualized XIRR percentage
- **Smart Error Handling**: Gracefully handles extreme loss scenarios where XIRR cannot be calculated

## Quick Start

### Single Account

1. Export your Zerodha ledger as a CSV file from Zerodha Console
2. Place the CSV file in this directory
3. Run the startup script:

```bash
./run_xirr.sh your-ledger.csv
```

4. Enter your current holdings value and available cash when prompted

### Multiple Accounts

1. Export ledgers for all your Zerodha accounts as CSV files
2. Place all CSV files in this directory
3. Run without specifying a file:

```bash
./run_xirr.sh
```

4. Select which accounts to include and how to distribute current value
5. Get individual and combined XIRR results

The script will automatically:
- Create a virtual environment (first run only)
- Install all dependencies (first run only)
- Detect and let you select CSV files
- Run the calculator

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

### Method 1: Using the Startup Script (Recommended)

No manual installation needed! The `run_xirr.sh` script handles everything automatically.

### Method 2: Manual Installation

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

## Usage

### Using the Startup Script (Easiest)

```bash
# With default CSV file (ledger-NBN208.csv)
./run_xirr.sh

# With custom CSV file
./run_xirr.sh path/to/your-ledger.csv
```

### Direct Python Execution

If you've manually installed dependencies in a virtual environment:

```bash
source venv/bin/activate
python xirr_calculator.py ledger-NBN208.csv
```

### Input Required

When prompted, enter:
- **Current holdings value**: Total market value of all stocks/securities in your portfolio
- **Current available cash**: Available cash balance in your trading account

### Multi-Account Analysis

If you have multiple Zerodha accounts (or want to analyze ledgers from different periods separately):

1. Place all CSV files in the same directory
2. Run the calculator without specifying a file:
   ```bash
   ./run_xirr.sh
   ```
3. The calculator will:
   - Detect all CSV files
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
════════════════════════════════════════════════════════════
Account                    Invested       Current      XIRR
ledger-GZW478.csv      ₹46,73,336.00  ₹15,50,000.00  -18.5%
ledger-NBN208.csv      ₹50,88,820.00  ₹20,30,000.00   2.41%
COMBINED               ₹97,62,156.00  ₹35,80,000.00  -8.2%
```

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
```

## How It Works

1. **Reads the Zerodha Ledger CSV**: Parses the CSV file exported from Zerodha
2. **Identifies Cash Flows**:
   - **Outflows**: All "Funds added" transactions (money you invested)
   - **Inflows**: All "Payout" transactions (money you withdrew)
   - **Final Value**: Current holdings + available cash (as of today)
3. **Calculates XIRR**: Uses the Newton-Raphson method to find the annualized return rate that makes the Net Present Value (NPV) of all cash flows equal to zero

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

### "No fund additions found in the ledger"
- Ensure your CSV file contains transactions with "Funds added" in the particulars column
- Verify you're using the correct Zerodha ledger format

### "Could not converge to a solution"
- This usually happens with very irregular cash flows or extreme values
- Verify your current holdings and cash values are correct
- Ensure you have at least 2 transactions (deposits/withdrawals)

### "File not found"
- Check that the CSV file path is correct
- Make sure the file is in the same directory or provide the full path

## CSV Format

The tool expects a Zerodha ledger CSV with these columns:
- `particulars`: Transaction description
- `posting_date`: Date of transaction (YYYY-MM-DD)
- `credit`: Credit amount (for fund additions)
- `debit`: Debit amount (for payouts)

## License

MIT License - Feel free to use and modify

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Disclaimer

This tool is for informational purposes only. Always verify calculations independently and consult with a financial advisor for investment decisions.
