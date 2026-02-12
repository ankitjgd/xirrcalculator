#!/usr/bin/env python3
"""
XIRR Calculator by Ankit Bhardwaj - Streamlit Web App
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import io
import os

# Import calculation functions from the existing module
from xirr_calculator import (
    calculate_xirr,
    fetch_nifty50_data,
    calculate_nifty50_portfolio,
    calculate_portfolio_stats,
    generate_pdf_report,
    load_and_parse_ledger,
    format_currency
)

# Page configuration
st.set_page_config(
    page_title="XIRR Calculator by Ankit Bhardwaj",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem;
        border-radius: 0.3rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

def process_uploaded_file(uploaded_file, pdf_password=None):
    """Process an uploaded ledger file (CSV or PDF) and extract transactions."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Parse the ledger (automatically detects file type)
        outflows, inflows = load_and_parse_ledger(temp_path, pdf_password)

        # Clean up temp file
        os.remove(temp_path)

        return outflows, inflows, uploaded_file.name
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None, None, None

def display_portfolio_metrics(stats, title="Portfolio Summary"):
    """Display portfolio metrics in a nice format."""
    st.subheader(title)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Invested", format_currency(stats['total_invested']))
    with col2:
        st.metric("Total Withdrawn", format_currency(stats['total_withdrawn']))
    with col3:
        st.metric("Current Value", format_currency(stats['current_value']))
    with col4:
        st.metric("Net Gain/Loss", format_currency(stats['net_gain']))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Investment Period", f"{stats['years_invested']:.2f} years")
    with col2:
        st.metric("Simple Return", f"{stats['simple_return']:.2f}%")
    with col3:
        if stats['xirr_percentage'] is not None:
            st.metric("XIRR (Annualized)", f"{stats['xirr_percentage']:.2f}%")
        else:
            st.metric("XIRR", "N/A")
    with col4:
        st.metric("Transactions", f"{stats['num_outflows']} in, {stats['num_inflows']} out")

def display_nifty_comparison(stats):
    """Display Nifty 50 comparison."""
    if stats.get('nifty50_stats'):
        nifty = stats['nifty50_stats']

        st.subheader("📊 Nifty 50 Benchmark Comparison")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Nifty 50 Portfolio Value", format_currency(nifty['current_value']))
        with col2:
            st.metric("Nifty 50 XIRR", f"{nifty['xirr_percentage']:.2f}%")
        with col3:
            st.metric("Nifty 50 Units Held", f"{nifty['units']:.2f}")

        if stats['xirr_percentage'] is not None and nifty['xirr_percentage'] is not None:
            diff = stats['xirr_percentage'] - nifty['xirr_percentage']
            value_diff = stats['current_value'] - nifty['current_value']

            if diff > 0:
                st.markdown(f"""
                <div class="success-box">
                    <strong>✓ OUTPERFORMED</strong> Nifty 50 by <strong>{diff:.2f}%</strong><br>
                    Value difference: <strong>{format_currency(value_diff)}</strong>
                </div>
                """, unsafe_allow_html=True)
            elif diff < 0:
                st.markdown(f"""
                <div class="error-box">
                    <strong>✗ UNDERPERFORMED</strong> Nifty 50 by <strong>{abs(diff):.2f}%</strong><br>
                    Value difference: <strong>{format_currency(value_diff)}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="warning-box">
                    <strong>= MATCHED</strong> Nifty 50 performance
                </div>
                """, unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">📊 XIRR Calculator by Ankit Bhardwaj</div>', unsafe_allow_html=True)

    st.markdown("""
    Calculate the Extended Internal Rate of Return (XIRR) for your trading portfolio.
    Compare your performance with the Nifty 50 index benchmark.

    **Supported brokers:** Zerodha (CSV) | Groww (PDF)
    """)

    # Sidebar
    with st.sidebar:
        st.header("📁 Upload Ledger Files")
        st.markdown("""
        Upload ledger files from your broker:
        - **Zerodha**: CSV files
        - **Groww**: PDF files (password-protected)
        """)

        uploaded_files = st.file_uploader(
            "Choose ledger file(s)",
            type=['csv', 'pdf'],
            accept_multiple_files=True,
            help="You can upload multiple files for multi-account analysis"
        )

        # PDF password input
        pdf_password = None
        if uploaded_files and any(f.name.endswith('.pdf') for f in uploaded_files):
            st.markdown("---")
            st.markdown("**PDF Password** (for Groww ledgers)")
            pdf_password = st.text_input(
                "Enter PDF password",
                type="password",
                help="Usually your PAN number (uppercase)"
            )

        st.markdown("---")
        st.markdown("""
        ### About XIRR
        XIRR accounts for:
        - Timing of each investment
        - Withdrawals during the period
        - Time value of money

        More accurate than simple returns!
        """)

    if not uploaded_files:
        st.info("👈 Please upload your broker ledger file(s) from the sidebar to begin.")

        # Show sample data info
        with st.expander("ℹ️ How to get your broker ledger"):
            st.markdown("""
            **Zerodha (CSV):**
            1. Log in to [Zerodha Console](https://console.zerodha.com/)
            2. Go to **Reports** → **Ledger**
            3. Select date range
            4. Click **Download** and choose CSV format
            5. Upload the downloaded CSV file(s) here

            **Groww (PDF):**
            1. Log in to [Groww](https://groww.in/)
            2. Go to **Profile** → **Reports & Statements**
            3. Select **Ledger Statement**
            4. Select date range (max 1 year per PDF)
            5. Download the PDF file(s)
            6. Upload the PDF file(s) here with your PAN as password
            """)

        with st.expander("📊 View Sample Report"):
            st.markdown("""
            Want to see what the output looks like?

            Check out our [sample report](https://github.com/ankitjgd/xirrcalculator/blob/main/reports/sample_report.pdf)
            to understand the analysis and metrics provided.
            """)

        return

    # Process uploaded files
    st.header("📈 Portfolio Analysis")

    accounts_data = []

    for uploaded_file in uploaded_files:
        with st.expander(f"📄 {uploaded_file.name}", expanded=True):
            outflows, inflows, filename = process_uploaded_file(uploaded_file, pdf_password)

            if outflows is not None and inflows is not None:
                st.success(f"✓ Found {len(outflows)} investments and {len(inflows)} withdrawals")

                # Get portfolio value inputs
                col1, col2 = st.columns(2)

                with col1:
                    holdings = st.number_input(
                        f"Current Holdings Value (₹)",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        key=f"holdings_{filename}",
                        help="Total market value of all stocks/securities"
                    )

                with col2:
                    cash = st.number_input(
                        f"Available Cash (₹)",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        key=f"cash_{filename}",
                        help="Available cash balance in trading account"
                    )

                current_value = holdings + cash

                if current_value > 0:
                    accounts_data.append({
                        'name': filename,
                        'outflows': outflows,
                        'inflows': inflows,
                        'current_value': current_value
                    })

    # Calculate and display results
    if accounts_data:
        if st.button("🔢 Calculate XIRR", type="primary"):
            with st.spinner("Calculating XIRR and fetching Nifty 50 data..."):

                # Calculate stats for each account
                individual_stats = []
                all_outflows = []
                all_inflows = []
                all_values = []

                for account in accounts_data:
                    stats = calculate_portfolio_stats(
                        account['outflows'],
                        account['inflows'],
                        account['current_value'],
                        account['name']
                    )
                    individual_stats.append(stats)
                    all_outflows.append(account['outflows'])
                    all_inflows.append(account['inflows'])
                    all_values.append(account['current_value'])

                # Display individual account results
                if len(accounts_data) > 1:
                    st.header("📊 Individual Account Analysis")

                    for i, stats in enumerate(individual_stats):
                        with st.expander(f"Account: {stats['file_name']}", expanded=False):
                            display_portfolio_metrics(stats, f"Account {i+1}")
                            display_nifty_comparison(stats)

                # Calculate combined stats
                st.header("📈 Combined Portfolio Analysis")

                combined_outflows = pd.concat(all_outflows, ignore_index=True)
                combined_inflows = pd.concat(all_inflows, ignore_index=True)
                combined_value = sum(all_values)

                combined_stats = calculate_portfolio_stats(
                    combined_outflows,
                    combined_inflows,
                    combined_value,
                    "Combined Portfolio"
                )

                display_portfolio_metrics(combined_stats, "Overall Portfolio Performance")
                display_nifty_comparison(combined_stats)

                # Summary table for multiple accounts
                if len(accounts_data) > 1:
                    st.subheader("📋 Summary Comparison Table")

                    summary_data = []
                    for stats in individual_stats:
                        summary_data.append({
                            'Account': stats['file_name'],
                            'Invested': format_currency(stats['total_invested']),
                            'Withdrawn': format_currency(stats['total_withdrawn']),
                            'Current Value': format_currency(stats['current_value']),
                            'Gain/Loss': format_currency(stats['net_gain']),
                            'XIRR': f"{stats['xirr_percentage']:.2f}%" if stats['xirr_percentage'] else "N/A"
                        })

                    # Add combined row
                    summary_data.append({
                        'Account': 'COMBINED',
                        'Invested': format_currency(combined_stats['total_invested']),
                        'Withdrawn': format_currency(combined_stats['total_withdrawn']),
                        'Current Value': format_currency(combined_stats['current_value']),
                        'Gain/Loss': format_currency(combined_stats['net_gain']),
                        'XIRR': f"{combined_stats['xirr_percentage']:.2f}%" if combined_stats['xirr_percentage'] else "N/A"
                    })

                    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

                # Generate PDF report
                st.header("📄 Download Report")

                try:
                    # Generate PDF in memory
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    pdf_filename = f"xirr_report_{timestamp}.pdf"

                    # Create a temporary file for PDF
                    temp_pdf = f"temp_{pdf_filename}"
                    generate_pdf_report(individual_stats, combined_stats, temp_pdf)

                    # Read PDF file
                    with open(temp_pdf, "rb") as f:
                        pdf_data = f.read()

                    # Clean up temp file
                    os.remove(temp_pdf)

                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_data,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        type="primary"
                    )

                    st.success("✓ PDF report ready for download!")

                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ | <a href='https://github.com/ankitjgd/xirrcalculator'>View on GitHub</a></p>
        <p><small>This tool is for informational purposes only. Always verify calculations independently.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
