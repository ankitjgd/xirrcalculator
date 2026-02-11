#!/usr/bin/env python3
"""
XIRR Calculator for Zerodha Trading Account

Calculates the Extended Internal Rate of Return (XIRR) based on:
- Fund additions (outflows - money invested)
- Withdrawals/Payouts (inflows - money returned)
- Current portfolio value (holdings + cash)
"""

import sys
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.optimize import newton, brentq


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


def load_and_parse_ledger(csv_file):
    """
    Load Zerodha ledger CSV and extract relevant transactions.

    Returns:
        tuple: (outflows_df, inflows_df) where each is a DataFrame with 'date' and 'amount' columns
    """
    print(f"\nLoading ledger: {csv_file}")

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


def find_csv_files(directory="."):
    """Find all CSV files in the given directory."""
    csv_files = glob.glob(os.path.join(directory, "*.csv"))
    # Get just the filenames, not full paths
    csv_files = [os.path.basename(f) for f in csv_files]
    return sorted(csv_files)


def select_csv_files(csv_files):
    """Let user select which CSV files to include in the analysis."""
    if len(csv_files) == 0:
        print("Error: No CSV files found in the current directory.")
        sys.exit(1)

    if len(csv_files) == 1:
        print(f"\nFound 1 CSV file: {csv_files[0]}")
        return csv_files

    print(f"\nFound {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files, 1):
        print(f"  {i}. {file}")

    print("\nSelect files to include in XIRR calculation:")
    print("  - Enter numbers separated by commas (e.g., 1,2,3)")
    print("  - Enter 'all' to include all files")
    print("  - Press Enter to use all files")

    while True:
        selection = input("\nYour selection: ").strip().lower()

        if selection == '' or selection == 'all':
            return csv_files

        try:
            # Parse comma-separated numbers
            indices = [int(x.strip()) for x in selection.split(',')]

            # Validate indices
            if all(1 <= i <= len(csv_files) for i in indices):
                selected_files = [csv_files[i-1] for i in indices]
                return selected_files
            else:
                print(f"Please enter numbers between 1 and {len(csv_files)}")
        except ValueError:
            print("Invalid input. Please enter numbers separated by commas or 'all'")


def get_fiscal_year(date):
    """
    Get fiscal year for a given date.
    Indian fiscal year: April 1 to March 31
    FY 2023-24 means April 1, 2023 to March 31, 2024
    """
    if date.month >= 4:  # April or later
        return f"FY {date.year}-{str(date.year + 1)[2:]}"
    else:  # January to March
        return f"FY {date.year - 1}-{str(date.year)[2:]}"


def calculate_yearwise_summary(outflows, inflows):
    """Calculate fiscal year-wise transaction summary."""
    # Combine all transactions
    all_transactions = []

    for _, row in outflows.iterrows():
        all_transactions.append({
            'date': pd.to_datetime(row['date']),
            'amount': row['amount'],  # negative for outflows
            'type': 'investment'
        })

    for _, row in inflows.iterrows():
        all_transactions.append({
            'date': pd.to_datetime(row['date']),
            'amount': row['amount'],  # positive for inflows
            'type': 'withdrawal'
        })

    if not all_transactions:
        return []

    # Create DataFrame and extract fiscal year
    df = pd.DataFrame(all_transactions)
    df['fiscal_year'] = df['date'].apply(get_fiscal_year)

    # Group by fiscal year
    yearly_summary = []
    for fy in sorted(df['fiscal_year'].unique()):
        year_data = df[df['fiscal_year'] == fy]
        invested = -year_data[year_data['type'] == 'investment']['amount'].sum()
        withdrawn = year_data[year_data['type'] == 'withdrawal']['amount'].sum()

        yearly_summary.append({
            'year': fy,
            'invested': invested,
            'withdrawn': withdrawn,
            'net_flow': withdrawn - invested
        })

    return yearly_summary


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

    # Calculate fiscal year-wise summary
    yearly_summary = calculate_yearwise_summary(outflows, inflows)

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
        'yearly_summary': yearly_summary
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

    # Display fiscal year-wise summary
    if stats['yearly_summary']:
        print(f"\n{'-'*78}")
        print("  Fiscal Year-wise Transaction Summary")
        print(f"{'-'*78}")
        print(f"{'Fiscal Year':<12} {'Invested':>14} {'Withdrawn':>14} {'Net Flow':>14} {'Cumulative':>14}")
        print(f"{'':12} {'':14} {'':14} {'':14} {'Invested':>14}")
        print("-" * 78)

        cumulative_invested = 0
        cumulative_withdrawn = 0

        for year_data in stats['yearly_summary']:
            cumulative_invested += year_data['invested']
            cumulative_withdrawn += year_data['withdrawn']

            print(f"{year_data['year']:<12} "
                  f"{format_currency(year_data['invested']):>14} "
                  f"{format_currency(year_data['withdrawn']):>14} "
                  f"{format_currency(year_data['net_flow']):>14} "
                  f"{format_currency(cumulative_invested):>14}")

        print("-" * 78)
        print(f"{'Total':<12} "
              f"{format_currency(cumulative_invested):>14} "
              f"{format_currency(cumulative_withdrawn):>14} "
              f"{format_currency(cumulative_withdrawn - cumulative_invested):>14} "
              f"{'':>14}")


def main():
    print("="*60)
    print("  XIRR Calculator for Zerodha Portfolio")
    print("="*60)

    # Find all CSV files or use command line argument
    if len(sys.argv) > 1:
        # If specific file provided, use only that file
        csv_files = [sys.argv[1]]
        print(f"\nUsing specified file: {csv_files[0]}")
    else:
        # Scan directory for CSV files
        csv_files = find_csv_files(".")
        csv_files = select_csv_files(csv_files)

    print(f"\n{'='*60}")
    print(f"Selected {len(csv_files)} file(s) for analysis")
    print(f"{'='*60}")

    # Process each file and get portfolio values
    file_data = []
    all_outflows = []
    all_inflows = []
    file_current_values = []
    total_holdings = 0
    total_cash = 0

    for csv_file in csv_files:
        print(f"\n[Processing: {csv_file}]")
        outflows, inflows = load_and_parse_ledger(csv_file)

        # Store for combined calculation
        all_outflows.append(outflows)
        all_inflows.append(inflows)

        # Get portfolio value for this account
        holdings, cash = get_user_inputs_for_account(csv_file)
        current_value = holdings + cash
        file_current_values.append(current_value)
        total_holdings += holdings
        total_cash += cash

        print(f"  - Holdings: {format_currency(holdings)}")
        print(f"  - Cash: {format_currency(cash)}")
        print(f"  - Total: {format_currency(current_value)}")

        # Store file info
        file_data.append({
            'name': csv_file,
            'outflows': outflows,
            'inflows': inflows
        })

    # Show combined summary if multiple accounts
    if len(csv_files) > 1:
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
    if len(csv_files) > 1:
        print("\n\n" + "#"*60)
        print("  INDIVIDUAL ACCOUNT ANALYSIS")
        print("#"*60)

        for stats in individual_stats:
            display_portfolio_stats(stats, f"Account: {stats['file_name']}")

    # Calculate combined stats
    print("\n\n" + "#"*60)
    if len(csv_files) > 1:
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
        "Combined Portfolio" if len(csv_files) > 1 else ""
    )

    display_portfolio_stats(combined_stats, "Combined Portfolio" if len(csv_files) > 1 else "Portfolio Summary")

    # Summary table for multiple files
    if len(csv_files) > 1:
        print("\n\n" + "="*60)
        print("  SUMMARY TABLE")
        print("="*60)
        print(f"\n{'Account':<25} {'Invested':>12} {'Current':>12} {'XIRR':>8}")
        print("-" * 60)

        for stats in individual_stats:
            xirr_str = f"{stats['xirr_percentage']:.2f}%" if stats['xirr_percentage'] is not None else "N/A"
            print(f"{stats['file_name']:<25} {format_currency(stats['total_invested']):>12} {format_currency(stats['current_value']):>12} {xirr_str:>8}")

        print("-" * 60)
        xirr_str = f"{combined_stats['xirr_percentage']:.2f}%" if combined_stats['xirr_percentage'] is not None else "N/A"
        print(f"{'COMBINED':<25} {format_currency(combined_stats['total_invested']):>12} {format_currency(combined_stats['current_value']):>12} {xirr_str:>8}")

    print("\n")


if __name__ == "__main__":
    main()
