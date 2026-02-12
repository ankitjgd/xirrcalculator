#!/usr/bin/env python3
"""
XIRR Calculator by Ankit Bhardwaj

Calculates the Extended Internal Rate of Return (XIRR) based on:
- Fund additions (outflows - money invested)
- Withdrawals/Payouts (inflows - money returned)
- Current portfolio value (holdings + cash)

Currently supports: Zerodha
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.optimize import newton, brentq
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import yfinance as yf
import pdfplumber


def calculate_xirr(cash_flows, dates, guess=0.1):
    """
    Calculate XIRR using multiple optimization methods.

    Args:
        cash_flows: List of cash flow amounts (negative for outflows, positive for inflows)
        dates: List of datetime objects corresponding to cash flows
        guess: Initial guess for IRR (default 0.1 = 10%)

    Returns:
        XIRR as a decimal (e.g., 0.1234 for 12.34%)
    """
    if len(cash_flows) != len(dates):
        raise ValueError("Cash flows and dates must have the same length")

    if len(cash_flows) < 2:
        raise ValueError("Need at least 2 cash flows to calculate XIRR")

    # Sort by date
    sorted_data = sorted(zip(dates, cash_flows))
    dates = [d for d, _ in sorted_data]
    cash_flows = [cf for _, cf in sorted_data]

    # Convert dates to years from first date (more stable than days)
    first_date = dates[0]
    years = [(date - first_date).days / 365.25 for date in dates]

    def xnpv(rate):
        """Calculate NPV with irregular periods"""
        # Clip rate to prevent overflow
        rate = np.clip(rate, -0.9999, 100)
        try:
            return sum(cf / (1 + rate) ** year for cf, year in zip(cash_flows, years))
        except (OverflowError, ZeroDivisionError):
            return float('inf') if rate > 0 else float('-inf')

    def xnpv_derivative(rate):
        """Calculate derivative of NPV for Newton-Raphson"""
        rate = np.clip(rate, -0.9999, 100)
        try:
            return sum(-cf * year / (1 + rate) ** (year + 1) for cf, year in zip(cash_flows, years))
        except (OverflowError, ZeroDivisionError):
            return 0

    # Try multiple methods in order of preference

    # Method 1: Newton-Raphson with multiple initial guesses
    for initial_guess in [0.1, 0.0, -0.5, 0.5, 1.0]:
        try:
            result = newton(
                func=xnpv,
                x0=initial_guess,
                fprime=xnpv_derivative,
                maxiter=100,
                tol=1e-6
            )
            # Verify the result
            if abs(xnpv(result)) < 1.0 and -0.99 < result < 10:
                return result
        except:
            continue

    # Method 2: Brent's method with wider range (more robust, doesn't need derivative)
    for lower_bound in [-0.999, -0.99, -0.95]:
        for upper_bound in [10, 5, 2]:
            try:
                # Check if there's a sign change (required for Brent's method)
                npv_lower = xnpv(lower_bound)
                npv_upper = xnpv(upper_bound)
                if npv_lower * npv_upper < 0:  # Sign change detected
                    result = brentq(xnpv, lower_bound, upper_bound, maxiter=200, xtol=1e-6)
                    if abs(xnpv(result)) < 1.0:
                        return result
            except:
                continue

    # Method 3: Fine grid search for approximate solution
    best_rate = None
    best_npv = float('inf')

    # First do coarse search
    for rate in np.linspace(-0.99, 5, 2000):
        try:
            npv = abs(xnpv(rate))
            if npv < best_npv:
                best_npv = npv
                best_rate = rate
        except:
            continue

    # If we found a reasonable approximation, refine it
    if best_rate is not None and best_npv < 100:
        # Fine search around the best rate
        fine_rates = np.linspace(max(-0.99, best_rate - 0.5), min(5, best_rate + 0.5), 1000)
        for rate in fine_rates:
            try:
                npv = abs(xnpv(rate))
                if npv < best_npv:
                    best_npv = npv
                    best_rate = rate
            except:
                continue

    if best_rate is not None and best_npv < 100:
        return best_rate

    # Check if NPV can ever be close to zero
    npv_at_minus_99 = abs(xnpv(-0.99))
    npv_at_plus_5 = abs(xnpv(5))
    min_possible_npv = min(npv_at_minus_99, npv_at_plus_5, best_npv if best_rate else float('inf'))

    if min_possible_npv > 1000:
        # NPV never gets close to zero - extreme loss scenario
        raise ValueError(
            "Cannot calculate XIRR: Net Present Value is always highly negative. "
            "This indicates extreme losses where no discount rate can reconcile the cash flows. "
            "The investment has lost significant value."
        )

    raise ValueError("Could not converge to a solution. This may indicate unusual cash flow patterns.")


def fetch_nifty50_data(start_date, end_date):
    """
    Fetch Nifty 50 historical data from Yahoo Finance.

    Args:
        start_date: Start date (datetime)
        end_date: End date (datetime)

    Returns:
        DataFrame with date and close price, or None if fetch fails
    """
    try:
        # Add buffer days to ensure we have data
        start_date_buffered = start_date - timedelta(days=10)
        end_date_buffered = end_date + timedelta(days=5)

        # Fetch Nifty 50 data (^NSEI is the Yahoo Finance ticker for Nifty 50)
        nifty = yf.download('^NSEI', start=start_date_buffered, end=end_date_buffered, progress=False)

        if nifty.empty:
            return None

        # Get close prices and reset index to make date a column
        nifty_data = nifty[['Close']].copy()
        nifty_data.reset_index(inplace=True)
        nifty_data.columns = ['date', 'close']

        # Convert date to datetime without timezone
        nifty_data['date'] = pd.to_datetime(nifty_data['date']).dt.tz_localize(None)

        return nifty_data

    except Exception as e:
        print(f"\nWarning: Could not fetch Nifty 50 data: {e}")
        return None


def calculate_nifty50_portfolio(outflows, inflows, nifty_data):
    """
    Calculate hypothetical portfolio value if invested in Nifty 50 on same dates.
    Tracks units bought on investments and units sold on withdrawals.

    Args:
        outflows: DataFrame with 'date' and 'amount' columns (negative values)
        inflows: DataFrame with 'date' and 'amount' columns (positive values)
        nifty_data: DataFrame with Nifty 50 historical prices

    Returns:
        dict with portfolio value and XIRR, or None if calculation fails
    """
    if nifty_data is None or nifty_data.empty:
        return None

    try:
        # Combine all transactions and sort by date
        transactions = []

        # Add investments (outflows - buying units)
        for _, row in outflows.iterrows():
            transactions.append({
                'date': pd.to_datetime(row['date']),
                'amount': row['amount'],  # negative
                'type': 'investment'
            })

        # Add withdrawals (inflows - selling units)
        for _, row in inflows.iterrows():
            transactions.append({
                'date': pd.to_datetime(row['date']),
                'amount': row['amount'],  # positive
                'type': 'withdrawal'
            })

        # Sort by date
        transactions = sorted(transactions, key=lambda x: x['date'])

        # Track units and invested amount
        total_units = 0
        total_invested_amount = 0

        # Process each transaction
        for trans in transactions:
            trans_date = trans['date']

            # Find closest Nifty 50 price (forward fill for weekends/holidays)
            nifty_price = None

            # Try exact date first
            exact_match = nifty_data[nifty_data['date'] == trans_date]
            if not exact_match.empty:
                nifty_price = exact_match.iloc[0]['close']
            else:
                # Find nearest future date (next trading day)
                future_dates = nifty_data[nifty_data['date'] > trans_date]
                if not future_dates.empty:
                    nifty_price = future_dates.iloc[0]['close']
                else:
                    # If no future date, use last available price
                    nifty_price = nifty_data.iloc[-1]['close']

            if nifty_price is None or nifty_price == 0:
                continue

            if trans['type'] == 'investment':
                # Buy units with this investment amount
                investment_amount = abs(trans['amount'])
                units_bought = investment_amount / nifty_price
                total_units += units_bought
                total_invested_amount += investment_amount

            elif trans['type'] == 'withdrawal':
                # Sell proportional units for this withdrawal
                withdrawal_amount = abs(trans['amount'])

                if total_units > 0:
                    # Calculate what percentage of portfolio we're withdrawing
                    current_portfolio_value = total_units * nifty_price

                    if current_portfolio_value > 0:
                        withdrawal_percentage = withdrawal_amount / current_portfolio_value
                        units_to_sell = total_units * withdrawal_percentage
                        total_units -= units_to_sell

                        # Ensure we don't go negative
                        if total_units < 0:
                            total_units = 0

        # Get latest Nifty 50 price for current value
        latest_price = nifty_data.iloc[-1]['close']
        current_value = total_units * latest_price

        # Calculate XIRR for Nifty 50 portfolio
        cash_flows = []
        dates = []

        # Add outflows (investments)
        for _, row in outflows.iterrows():
            dates.append(pd.to_datetime(row['date']))
            cash_flows.append(row['amount'])

        # Add inflows (withdrawals)
        for _, row in inflows.iterrows():
            dates.append(pd.to_datetime(row['date']))
            cash_flows.append(row['amount'])

        # Add current value
        dates.append(datetime.now())
        cash_flows.append(current_value)

        # Calculate XIRR
        nifty_xirr = None
        try:
            nifty_xirr_rate = calculate_xirr(cash_flows, dates)
            nifty_xirr = nifty_xirr_rate * 100
        except:
            nifty_xirr = None

        return {
            'current_value': current_value,
            'xirr_percentage': nifty_xirr,
            'units': total_units,
            'latest_price': latest_price
        }

    except Exception as e:
        print(f"\nWarning: Could not calculate Nifty 50 comparison: {e}")
        return None


def load_and_parse_groww_pdf(pdf_file, password=None):
    """
    Load Groww ledger PDF and extract relevant transactions.

    Returns:
        tuple: (outflows_df, inflows_df) where each is a DataFrame with 'date' and 'amount' columns
    """
    print(f"\nLoading Groww PDF ledger: {pdf_file}")

    try:
        # Try to open PDF with password if provided
        with pdfplumber.open(pdf_file, password=password or "") as pdf:
            all_deposits = []
            all_withdrawals = []

            # Extract tables from all pages
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()

                if not tables:
                    continue

                for table in tables:
                    # Skip if table is too small
                    if len(table) < 2:
                        continue

                    # Find column indices (header is usually first row)
                    header = table[0]

                    # Try to find relevant columns
                    date_col = None
                    segment_type_col = None
                    credit_col = None
                    debit_col = None

                    for i, col in enumerate(header):
                        if col and 'Transaction' in col and 'Date' in col:
                            date_col = i
                        elif col and 'Segment' in col and 'Type' in col:
                            segment_type_col = i
                        elif col and 'Credit' in col:
                            credit_col = i
                        elif col and 'Debit' in col:
                            debit_col = i

                    # Skip if we can't find required columns
                    if date_col is None or segment_type_col is None or credit_col is None or debit_col is None:
                        continue

                    # Process data rows (skip header)
                    for row in table[1:]:
                        if len(row) <= max(date_col, segment_type_col, credit_col, debit_col):
                            continue

                        transaction_date = row[date_col]
                        segment_type = row[segment_type_col]
                        credit_amount = row[credit_col]
                        debit_amount = row[debit_col]

                        # Skip empty rows
                        if not transaction_date or not segment_type:
                            continue

                        # Parse date (format: DD/MM/YYYY)
                        try:
                            date_str = transaction_date.strip()
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            date_formatted = date_obj.strftime('%Y-%m-%d')
                        except:
                            continue

                        # Extract deposits (RAZORPAY_DEPOSIT, etc.) - these are fund additions (outflows)
                        if 'DEPOSIT' in segment_type.upper() and credit_amount:
                            try:
                                amount = float(credit_amount.replace(',', '').strip())
                                if amount > 0:
                                    all_deposits.append({
                                        'date': date_formatted,
                                        'amount': -amount  # Make negative (outflow)
                                    })
                            except:
                                continue

                        # Extract withdrawals (GROWW_WITHDRAW) - these are payouts (inflows)
                        if 'WITHDRAW' in segment_type.upper() and debit_amount:
                            try:
                                amount = float(debit_amount.replace(',', '').strip())
                                if amount > 0:
                                    all_withdrawals.append({
                                        'date': date_formatted,
                                        'amount': amount  # Positive (inflow)
                                    })
                            except:
                                continue

            # Convert to DataFrames
            outflows_df = pd.DataFrame(all_deposits)
            inflows_df = pd.DataFrame(all_withdrawals)

            print(f"Found {len(outflows_df)} fund additions (deposits)")
            print(f"Found {len(inflows_df)} withdrawals")

            if len(outflows_df) == 0:
                print("Error: No fund additions found in the PDF ledger.")
                sys.exit(1)

            return outflows_df, inflows_df

    except Exception as e:
        if "password" in str(e).lower():
            print(f"Error: PDF is password-protected. Please provide the password.")
            print("Common passwords: Your PAN number (lowercase) or Date of Birth (DDMMYYYY)")
            sys.exit(1)
        else:
            print(f"Error reading PDF: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def load_and_parse_ledger(ledger_file, password=None):
    """
    Load ledger file (CSV or PDF) and extract relevant transactions.
    Automatically detects file type and routes to appropriate parser.

    Args:
        ledger_file: Path to ledger file (CSV or PDF)
        password: Optional password for PDF files

    Returns:
        tuple: (outflows_df, inflows_df) where each is a DataFrame with 'date' and 'amount' columns
    """
    # Detect file type
    file_extension = os.path.splitext(ledger_file)[1].lower()

    if file_extension == '.pdf':
        # Handle Groww PDF ledger
        return load_and_parse_groww_pdf(ledger_file, password)
    elif file_extension == '.csv':
        # Handle Zerodha CSV ledger
        return load_and_parse_zerodha_csv(ledger_file)
    else:
        print(f"Error: Unsupported file type '{file_extension}'. Supported types: .csv, .pdf")
        sys.exit(1)


def load_and_parse_zerodha_csv(csv_file):
    """
    Load Zerodha ledger CSV and extract relevant transactions.

    Returns:
        tuple: (outflows_df, inflows_df) where each is a DataFrame with 'date' and 'amount' columns
    """
    print(f"\nLoading Zerodha CSV ledger: {csv_file}")

    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        sys.exit(1)

    # Check for required columns
    required_cols = ['particulars', 'posting_date', 'credit', 'debit']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        sys.exit(1)

    # Extract fund additions (outflows - money going out from bank to trading account)
    fund_additions = df[df['particulars'].str.contains('Funds added', na=False)].copy()
    fund_additions = fund_additions[['posting_date', 'credit']].copy()
    fund_additions.columns = ['date', 'amount']
    fund_additions['amount'] = -fund_additions['amount']  # Make negative (outflow)
    fund_additions = fund_additions[fund_additions['date'].notna()]

    # Extract payouts/withdrawals (inflows - money coming back)
    payouts = df[df['particulars'].str.contains('Payout', na=False)].copy()
    payouts = payouts[['posting_date', 'debit']].copy()
    payouts.columns = ['date', 'amount']
    payouts = payouts[payouts['date'].notna()]

    # Extract quarterly settlements (inflows - money coming back)
    quarterly = df[df['particulars'].str.contains('quarterly settlement', case=False, na=False)].copy()
    quarterly = quarterly[['posting_date', 'debit']].copy()
    quarterly.columns = ['date', 'amount']
    quarterly = quarterly[quarterly['date'].notna()]

    # Combine all inflows
    all_inflows = pd.concat([payouts, quarterly], ignore_index=True)

    print(f"Found {len(fund_additions)} fund additions (outflows)")
    print(f"Found {len(payouts)} payouts (inflows)")
    print(f"Found {len(quarterly)} quarterly settlements (inflows)")
    print(f"Total inflows: {len(all_inflows)}")

    if len(fund_additions) == 0:
        print("Error: No fund additions found in the ledger.")
        sys.exit(1)

    return fund_additions, all_inflows


def get_user_inputs_for_account(account_name=None):
    """Get current portfolio value from user for a specific account."""
    if account_name:
        print("\n" + "="*60)
        print(f"  Portfolio Value for: {account_name}")
        print("="*60)
    else:
        print("\n" + "="*60)

    while True:
        try:
            holdings = float(input("Enter current holdings value (₹): ").strip())
            if holdings < 0:
                print("Please enter a positive value.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            cash = float(input("Enter current available cash (₹): ").strip())
            if cash < 0:
                print("Please enter a positive value.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    return holdings, cash


def format_currency(amount):
    """Format amount as Indian currency."""
    return f"₹{amount:,.2f}"


def format_currency_pdf(amount):
    """Format amount for PDF (without currency symbol to save space)."""
    return f"{amount:,.2f}"


def find_ledger_files(directory="ledger"):
    """Find all ledger files (CSV and PDF) in the given directory."""
    # Create ledger directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"\nCreated '{directory}/' folder. Please place your broker ledger files (CSV or PDF) there.")
        return []

    # Find both CSV and PDF files
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))

    # Combine and return sorted list
    all_files = csv_files + pdf_files
    all_files = [os.path.join(directory, os.path.basename(f)) for f in all_files]
    return sorted(all_files)


def select_ledger_files(ledger_files):
    """Let user select which ledger files to include in the analysis."""
    if len(ledger_files) == 0:
        print("Error: No ledger files found in the current directory.")
        sys.exit(1)

    if len(ledger_files) == 1:
        file_type = "CSV" if ledger_files[0].endswith('.csv') else "PDF"
        print(f"\nFound 1 {file_type} file: {ledger_files[0]}")
        return ledger_files

    print(f"\nFound {len(ledger_files)} ledger files:")
    for i, file in enumerate(ledger_files, 1):
        file_type = "CSV (Zerodha)" if file.endswith('.csv') else "PDF (Groww)"
        print(f"  {i}. {file} [{file_type}]")

    print("\nSelect files to include in XIRR calculation:")
    print("  - Enter numbers separated by commas (e.g., 1,2,3)")
    print("  - Enter 'all' to include all files")
    print("  - Press Enter to use all files")

    while True:
        selection = input("\nYour selection: ").strip().lower()

        if selection == '' or selection == 'all':
            return ledger_files

        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in selection.split(',')]

            # Validate indices
            if all(1 <= i <= len(ledger_files) for i in indices):
                selected_files = [ledger_files[i-1] for i in indices]
                return selected_files
            else:
                print(f"Please enter numbers between 1 and {len(ledger_files)}")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas or 'all'")


def calculate_portfolio_stats(outflows, inflows, current_value, file_name=""):
    """Calculate portfolio statistics for a given set of transactions."""
    today = datetime.now()

    total_invested = -outflows['amount'].sum()
    total_withdrawn = inflows['amount'].sum()

    if len(outflows) > 0:
        first_date = min(pd.to_datetime(outflows['date']))
        days_invested = (today - first_date).days
        years_invested = days_invested / 365.25
    else:
        first_date = today
        days_invested = 0
        years_invested = 0

    net_gain = current_value + total_withdrawn - total_invested
    simple_return = (net_gain / total_invested * 100) if total_invested > 0 else 0

    # Prepare cash flows for XIRR
    cash_flows = []
    dates = []

    # Add outflows
    for _, row in outflows.iterrows():
        dates.append(pd.to_datetime(row['date']))
        cash_flows.append(row['amount'])

    # Add inflows
    for _, row in inflows.iterrows():
        dates.append(pd.to_datetime(row['date']))
        cash_flows.append(row['amount'])

    # Add current value
    dates.append(today)
    cash_flows.append(current_value)

    # Calculate XIRR
    xirr_percentage = None
    xirr_error = None

    try:
        xirr_rate = calculate_xirr(cash_flows, dates)
        xirr_percentage = xirr_rate * 100
    except Exception as e:
        xirr_error = str(e)

    # Calculate Nifty 50 comparison
    nifty50_stats = None
    if len(outflows) > 0:
        try:
            # Fetch Nifty 50 data for the investment period
            nifty_data = fetch_nifty50_data(first_date, today)
            if nifty_data is not None:
                nifty50_stats = calculate_nifty50_portfolio(outflows, inflows, nifty_data)
        except Exception as e:
            print(f"\nNote: Nifty 50 comparison unavailable: {e}")
            nifty50_stats = None

    return {
        'file_name': file_name,
        'first_date': first_date,
        'days_invested': days_invested,
        'years_invested': years_invested,
        'total_invested': total_invested,
        'total_withdrawn': total_withdrawn,
        'current_value': current_value,
        'net_gain': net_gain,
        'simple_return': simple_return,
        'xirr_percentage': xirr_percentage,
        'xirr_error': xirr_error,
        'num_outflows': len(outflows),
        'num_inflows': len(inflows),
        'nifty50_stats': nifty50_stats
    }


def display_portfolio_stats(stats, title="Investment Analysis"):
    """Display portfolio statistics in a formatted way."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

    if stats['file_name']:
        print(f"\nFile: {stats['file_name']}")

    print(f"First investment date: {stats['first_date'].strftime('%Y-%m-%d')}")
    print(f"Investment period: {stats['days_invested']} days ({stats['years_invested']:.2f} years)")
    print(f"Transactions: {stats['num_outflows']} outflows, {stats['num_inflows']} inflows")

    print(f"\nTotal invested: {format_currency(stats['total_invested'])}")
    print(f"Total withdrawn: {format_currency(stats['total_withdrawn'])}")
    print(f"Current value: {format_currency(stats['current_value'])}")

    print(f"\nNet gain/loss: {format_currency(stats['net_gain'])}")
    print(f"Simple return: {stats['simple_return']:.2f}%")

    if stats['xirr_percentage'] is not None:
        print(f"\n{'*'*60}")
        print(f"  XIRR (Annualized): {stats['xirr_percentage']:.2f}%")
        print(f"{'*'*60}")

        if stats['xirr_percentage'] < 0:
            print("\nNote: Negative XIRR indicates a loss on investment.")
        elif stats['xirr_percentage'] > 50:
            print("\nNote: Very high XIRR - please verify input values.")
    else:
        print(f"\n{'*'*60}")
        print("  XIRR: Cannot be calculated")
        print(f"{'*'*60}")
        if stats['xirr_error']:
            print(f"\nReason: {stats['xirr_error']}")
            if "extreme losses" in stats['xirr_error'].lower():
                print("\nThe simple return percentage reflects the overall performance.")

    # Display Nifty 50 comparison if available
    if stats.get('nifty50_stats'):
        nifty_stats = stats['nifty50_stats']
        print(f"\n{'-'*60}")
        print("  NIFTY 50 BENCHMARK COMPARISON")
        print(f"{'-'*60}")

        print(f"\nIf you had invested the same amounts on the same dates in Nifty 50:")
        print(f"  Portfolio value: {format_currency(nifty_stats['current_value'])}")
        print(f"  Units held: {nifty_stats['units']:.2f}")
        print(f"  Current Nifty 50: {nifty_stats['latest_price']:.2f}")

        if nifty_stats['xirr_percentage'] is not None:
            print(f"  Nifty 50 XIRR: {nifty_stats['xirr_percentage']:.2f}%")

            if stats['xirr_percentage'] is not None:
                # Calculate outperformance
                outperformance = stats['xirr_percentage'] - nifty_stats['xirr_percentage']
                if outperformance > 0:
                    print(f"\n✓ Your portfolio OUTPERFORMED Nifty 50 by {outperformance:.2f}%")
                elif outperformance < 0:
                    print(f"\n✗ Your portfolio UNDERPERFORMED Nifty 50 by {abs(outperformance):.2f}%")
                else:
                    print(f"\n= Your portfolio matched Nifty 50 performance")

                # Calculate absolute difference in value
                value_diff = stats['current_value'] - nifty_stats['current_value']
                print(f"  Value difference: {format_currency(value_diff)}")
        else:
            print(f"  Nifty 50 XIRR: Could not be calculated")
    else:
        print(f"\n{'-'*60}")
        print("  Note: Nifty 50 comparison unavailable")
        print(f"{'-'*60}")


def generate_pdf_report(individual_stats, combined_stats, filename="xirr_report.pdf"):
    """Generate a PDF report with XIRR analysis results."""
    doc = SimpleDocTemplate(filename, pagesize=A4,
                           rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=18)

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#283593'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )

    # Title
    title = Paragraph("XIRR Calculator Report", title_style)
    elements.append(title)

    subtitle = Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 20))

    # Combined Portfolio Summary
    elements.append(Paragraph("Portfolio Summary", heading_style))

    summary_data = [
        ['Metric', 'Value'],
        ['First Investment Date', combined_stats['first_date'].strftime('%B %d, %Y')],
        ['Investment Period', f"{combined_stats['days_invested']} days ({combined_stats['years_invested']:.2f} years)"],
        ['Total Transactions', f"{combined_stats['num_outflows']} investments, {combined_stats['num_inflows']} withdrawals"],
        ['Total Invested', format_currency_pdf(combined_stats['total_invested'])],
        ['Total Withdrawn', format_currency_pdf(combined_stats['total_withdrawn'])],
        ['Current Portfolio Value', format_currency_pdf(combined_stats['current_value'])],
        ['Net Gain/Loss', format_currency_pdf(combined_stats['net_gain'])],
        ['Simple Return', f"{combined_stats['simple_return']:.2f}%"],
    ]

    if combined_stats['xirr_percentage'] is not None:
        summary_data.append(['XIRR (Annualized)', f"{combined_stats['xirr_percentage']:.2f}%"])
    else:
        summary_data.append(['XIRR (Annualized)', 'Cannot be calculated'])

    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Nifty 50 Benchmark Comparison
    if combined_stats.get('nifty50_stats'):
        nifty_stats = combined_stats['nifty50_stats']
        elements.append(Paragraph("Nifty 50 Benchmark Comparison", heading_style))

        nifty_data = [
            ['Metric', 'Your Portfolio', 'Nifty 50'],
            ['Current Value', format_currency_pdf(combined_stats['current_value']),
             format_currency_pdf(nifty_stats['current_value'])],
        ]

        # Track which rows need special formatting
        performance_row = -1
        value_diff_row = -1

        if combined_stats['xirr_percentage'] is not None and nifty_stats['xirr_percentage'] is not None:
            nifty_data.append(['XIRR (Annualized)',
                              f"{combined_stats['xirr_percentage']:.2f}%",
                              f"{nifty_stats['xirr_percentage']:.2f}%"])

            outperformance = combined_stats['xirr_percentage'] - nifty_stats['xirr_percentage']
            if outperformance > 0:
                performance_text = f"OUTPERFORMED by {outperformance:.2f}%"
                perf_color = colors.HexColor('#d4edda')  # Light green
            elif outperformance < 0:
                performance_text = f"UNDERPERFORMED by {abs(outperformance):.2f}%"
                perf_color = colors.HexColor('#f8d7da')  # Light red
            else:
                performance_text = "Matched performance"
                perf_color = colors.HexColor('#fff3cd')  # Light yellow

            performance_row = len(nifty_data)
            nifty_data.append(['Performance vs Nifty 50', performance_text, ''])

            value_diff = combined_stats['current_value'] - nifty_stats['current_value']
            value_diff_row = len(nifty_data)
            nifty_data.append(['Value Difference', format_currency_pdf(value_diff), ''])

        nifty_data.append(['Nifty 50 Units Held', '', f"{nifty_stats['units']:.2f}"])
        nifty_data.append(['Current Nifty 50 Price', '', f"{nifty_stats['latest_price']:.2f}"])

        nifty_table = Table(nifty_data, colWidths=[2*inch, 2*inch, 2*inch])

        # Base table style
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00897b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]

        # Span performance and value difference rows across columns
        if performance_row >= 0:
            table_style.extend([
                ('SPAN', (1, performance_row), (2, performance_row)),
                ('BACKGROUND', (0, performance_row), (-1, performance_row), perf_color),
                ('FONTNAME', (0, performance_row), (-1, performance_row), 'Helvetica-Bold'),
                ('ALIGN', (1, performance_row), (2, performance_row), 'CENTER'),
            ])

        if value_diff_row >= 0:
            table_style.extend([
                ('SPAN', (1, value_diff_row), (2, value_diff_row)),
                ('BACKGROUND', (0, value_diff_row), (-1, value_diff_row), colors.HexColor('#e3f2fd')),
                ('FONTNAME', (0, value_diff_row), (-1, value_diff_row), 'Helvetica-Bold'),
                ('ALIGN', (1, value_diff_row), (2, value_diff_row), 'CENTER'),
            ])

        nifty_table.setStyle(TableStyle(table_style))

        elements.append(nifty_table)
        elements.append(Spacer(1, 12))

        # Add explanation
        explanation = Paragraph(
            "<i>Note: This comparison shows how your portfolio would have performed if you had invested "
            "the same amounts on the same dates in the Nifty 50 index. Withdrawals are also accounted for.</i>",
            styles['Normal']
        )
        elements.append(explanation)
        elements.append(Spacer(1, 20))

    # Individual Account Analysis (if multiple accounts)
    if len(individual_stats) > 1:
        elements.append(PageBreak())
        elements.append(Paragraph("Individual Account Analysis", heading_style))
        elements.append(Spacer(1, 12))

        for stats in individual_stats:
            elements.append(Paragraph(f"Account: {stats['file_name']}", styles['Heading3']))

            account_data = [
                ['Metric', 'Value'],
                ['Total Invested', format_currency_pdf(stats['total_invested'])],
                ['Total Withdrawn', format_currency_pdf(stats['total_withdrawn'])],
                ['Current Value', format_currency_pdf(stats['current_value'])],
                ['Net Gain/Loss', format_currency_pdf(stats['net_gain'])],
                ['Simple Return', f"{stats['simple_return']:.2f}%"],
            ]

            if stats['xirr_percentage'] is not None:
                account_data.append(['XIRR (Annualized)', f"{stats['xirr_percentage']:.2f}%"])
            else:
                account_data.append(['XIRR (Annualized)', 'N/A'])

            account_table = Table(account_data, colWidths=[2.5*inch, 2.5*inch])
            account_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5c6bc0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))

            elements.append(account_table)
            elements.append(Spacer(1, 15))

        # Comparison table
        elements.append(Paragraph("Account Comparison", styles['Heading3']))

        comparison_data = [['Account', 'Invested', 'Withdrawn', 'Current', 'Gain/Loss']]

        for stats in individual_stats:
            comparison_data.append([
                stats['file_name'],
                format_currency_pdf(stats['total_invested']),
                format_currency_pdf(stats['total_withdrawn']),
                format_currency_pdf(stats['current_value']),
                format_currency_pdf(stats['net_gain'])
            ])

        # Add combined row
        comparison_data.append([
            'COMBINED',
            format_currency_pdf(combined_stats['total_invested']),
            format_currency_pdf(combined_stats['total_withdrawn']),
            format_currency_pdf(combined_stats['current_value']),
            format_currency_pdf(combined_stats['net_gain'])
        ])

        comparison_table = Table(comparison_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        comparison_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3f51b5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#c5cae9')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))

        elements.append(comparison_table)

    # Footer
    elements.append(Spacer(1, 30))
    footer = Paragraph(
        "Generated by XIRR Calculator | https://github.com/ankitjgd/xirrcalculator",
        styles['Normal']
    )
    elements.append(footer)

    # Build PDF
    doc.build(elements)
    return filename


def main():
    print("="*60)
    print("  XIRR Calculator by Ankit Bhardwaj")
    print("="*60)

    # Find all ledger files or use command line argument
    if len(sys.argv) > 1:
        # If specific file provided, use only that file
        ledger_files = [sys.argv[1]]
        print(f"\nUsing specified file: {ledger_files[0]}")
    else:
        # Scan ledger directory for both CSV and PDF files
        ledger_files = find_ledger_files("ledger")
        if not ledger_files:
            print("\nNo ledger files found in 'ledger/' folder.")
            print("Please place your broker ledger files (CSV or PDF) in the 'ledger/' folder and run again.")
            print("Supported formats:")
            print("  - Zerodha: CSV files")
            print("  - Groww: PDF files")
            sys.exit(0)
        ledger_files = select_ledger_files(ledger_files)

    print(f"\n{'='*60}")
    print(f"Selected {len(ledger_files)} file(s) for analysis")
    print(f"{'='*60}")

    # Check if any PDF files need password
    pdf_password = None
    has_pdfs = any(f.endswith('.pdf') for f in ledger_files)
    if has_pdfs:
        print("\nNote: Groww PDFs are usually password-protected.")
        print("Common passwords: Your PAN number (uppercase) or Date of Birth (DDMMYYYY)")
        pdf_password = input("Enter PDF password (or press Enter to skip): ").strip()
        if not pdf_password:
            pdf_password = None

    # Process each file and get portfolio values
    file_data = []
    all_outflows = []
    all_inflows = []
    file_current_values = []
    total_holdings = 0
    total_cash = 0

    for ledger_file in ledger_files:
        print(f"\n[Processing: {ledger_file}]")
        outflows, inflows = load_and_parse_ledger(ledger_file, pdf_password)

        # Store for combined calculation
        all_outflows.append(outflows)
        all_inflows.append(inflows)

        # Get portfolio value for this account
        holdings, cash = get_user_inputs_for_account(ledger_file)
        current_value = holdings + cash
        file_current_values.append(current_value)
        total_holdings += holdings
        total_cash += cash

        print(f"  - Holdings: {format_currency(holdings)}")
        print(f"  - Cash: {format_currency(cash)}")
        print(f"  - Total: {format_currency(current_value)}")

        # Store file info
        file_data.append({
            'name': ledger_file,
            'outflows': outflows,
            'inflows': inflows
        })

    # Show combined summary if multiple accounts
    if len(ledger_files) > 1:
        print(f"\n{'='*60}")
        print("  Combined Portfolio Summary")
        print(f"{'='*60}")
        print(f"Total Holdings: {format_currency(total_holdings)}")
        print(f"Total Cash: {format_currency(total_cash)}")
        print(f"Total Value: {format_currency(total_holdings + total_cash)}")

    # Calculate individual stats for each file
    individual_stats = []
    for i, fd in enumerate(file_data):
        stats = calculate_portfolio_stats(
            fd['outflows'],
            fd['inflows'],
            file_current_values[i],
            fd['name']
        )
        individual_stats.append(stats)

    # Display individual results
    if len(ledger_files) > 1:
        print("\n\n" + "#"*60)
        print("  INDIVIDUAL ACCOUNT ANALYSIS")
        print("#"*60)

        for stats in individual_stats:
            display_portfolio_stats(stats, f"Account: {stats['file_name']}")

    # Calculate combined stats
    print("\n\n" + "#"*60)
    if len(ledger_files) > 1:
        print("  COMBINED PORTFOLIO ANALYSIS")
    else:
        print("  PORTFOLIO ANALYSIS")
    print("#"*60)

    # Combine all transactions
    combined_outflows = pd.concat(all_outflows, ignore_index=True)
    combined_inflows = pd.concat(all_inflows, ignore_index=True)
    combined_current_value = sum(file_current_values)

    combined_stats = calculate_portfolio_stats(
        combined_outflows,
        combined_inflows,
        combined_current_value,
        "Combined Portfolio" if len(ledger_files) > 1 else ""
    )

    display_portfolio_stats(combined_stats, "Combined Portfolio" if len(ledger_files) > 1 else "Portfolio Summary")

    # Summary table for multiple files
    if len(ledger_files) > 1:
        print("\n\n" + "="*75)
        print("  SUMMARY TABLE")
        print("="*75)
        print(f"\n{'Account':<20} {'Invested':>13} {'Withdrawn':>13} {'Current':>13} {'Gain/Loss':>13}")
        print("-" * 75)

        for stats in individual_stats:
            print(f"{stats['file_name']:<20} "
                  f"{format_currency(stats['total_invested']):>13} "
                  f"{format_currency(stats['total_withdrawn']):>13} "
                  f"{format_currency(stats['current_value']):>13} "
                  f"{format_currency(stats['net_gain']):>13}")

        print("-" * 75)
        print(f"{'COMBINED':<20} "
              f"{format_currency(combined_stats['total_invested']):>13} "
              f"{format_currency(combined_stats['total_withdrawn']):>13} "
              f"{format_currency(combined_stats['current_value']):>13} "
              f"{format_currency(combined_stats['net_gain']):>13}")

    # Ask if user wants to save PDF report
    print("\n" + "="*60)
    save_pdf = input("Would you like to save this report as PDF? (y/n): ").strip().lower()

    if save_pdf in ['y', 'yes']:
        # Create reports directory if it doesn't exist
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
            print(f"\nCreated '{reports_dir}/' folder for PDF reports.")

        # Generate default filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"xirr_report_{timestamp}.pdf"

        custom_name = input(f"Enter filename (press Enter for '{default_filename}'): ").strip()

        if custom_name:
            # If user provides custom name, ensure it has timestamp
            if not custom_name.endswith('.pdf'):
                custom_name += '.pdf'
            # Add timestamp if not already in filename
            if not any(char.isdigit() for char in custom_name):
                base_name = custom_name.replace('.pdf', '')
                pdf_filename = f"{base_name}_{timestamp}.pdf"
            else:
                pdf_filename = custom_name
        else:
            pdf_filename = default_filename

        # Full path with reports directory
        pdf_filepath = os.path.join(reports_dir, pdf_filename)

        try:
            print(f"\nGenerating PDF report...")
            generate_pdf_report(individual_stats, combined_stats, pdf_filepath)
            print(f"✓ PDF report saved successfully: {pdf_filepath}")
        except Exception as e:
            print(f"✗ Error generating PDF: {e}")

    print("\n")


if __name__ == "__main__":
    main()
