#!/usr/bin/env python3
"""
XIRR Calculator by Ankit Bhardwaj - Streamlit Web App with Step-by-Step Wizard
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
    initial_sidebar_state="collapsed"  # Hide sidebar for cleaner look
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
        # Returns: (outflows, inflows, account_id)
        outflows, inflows, account_id = load_and_parse_ledger(temp_path, pdf_password)

        # Clean up temp file
        os.remove(temp_path)

        return outflows, inflows, uploaded_file.name, account_id
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None, None, None, None

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
    # Initialize session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'pdf_password' not in st.session_state:
        st.session_state.pdf_password = None

    # Header
    st.markdown('<div class="main-header">📊 XIRR Calculator by Ankit Bhardwaj</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Calculate the Extended Internal Rate of Return (XIRR) for your trading portfolio.
    Compare your performance with the Nifty 50 index benchmark.
    
    **Supported brokers:** Zerodha (CSV) | Groww (PDF)
    """)
    
    # Progress indicator
    st.markdown("---")
    progress_cols = st.columns(4)
    steps = [
        ("1️⃣", "Download Guide"),
        ("2️⃣", "Upload Files"),
        ("3️⃣", "Enter Password"),
        ("4️⃣", "Analysis")
    ]
    
    for i, (icon, label) in enumerate(steps, 1):
        with progress_cols[i-1]:
            if i < st.session_state.step:
                st.success(f"{icon} ✓ {label}")
            elif i == st.session_state.step:
                st.info(f"**{icon} {label}**")
            else:
                st.text(f"{icon} {label}")
    
    st.markdown("---")
    
    # Step 1: Download Instructions
    if st.session_state.step == 1:
        st.header("📥 Step 1: How to Download Your Ledger Files")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🟦 Zerodha (CSV)")
            st.markdown("""
            1. Log in to [Zerodha Console](https://console.zerodha.com/)
            2. Go to **Funds** → **View Statement**
            3. Select **All segment category**
            4. Select date range (from first investment till now)
            5. Click **Download CSV**
            6. Save the file

            ✅ **File type:** CSV
            🔓 **Password:** Not required
            """)
        
        with col2:
            st.subheader("🟩 Groww (PDF)")
            st.markdown("""
            1. Log in to [Groww](https://groww.in/)
            2. Go to **Funds** → **All Transactions**
            3. Select date & year (max 1 year per PDF)
            4. Click **Download**
            5. **Repeat for ALL years** from first investment till now
            6. You'll have multiple PDFs (one per year)

            ✅ **File type:** PDF
            🔐 **Password:** Your PAN number (uppercase)

            ⚠️ **Important:** Download for entire investment period
            """)
        
        st.info("💡 **Tip:** You can upload multiple files from the same or different brokers. Files from the same account (same PAN) will be automatically combined!")
        
        st.markdown("##")
        if st.button("Next: Upload Files →", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    
    # Step 2: Upload Files
    elif st.session_state.step == 2:
        st.header("📤 Step 2: Upload Your Ledger Files")
        
        uploaded_files = st.file_uploader(
            "Drag and drop or click to browse",
            type=['csv', 'pdf'],
            accept_multiple_files=True,
            help="You can select multiple files at once",
            key="file_uploader"
        )
        
        if uploaded_files:
            st.success(f"✓ Successfully uploaded {len(uploaded_files)} file(s)!")
            
            st.markdown("#### Uploaded Files:")
            for file in uploaded_files:
                file_type = "📄 PDF (Groww)" if file.name.endswith('.pdf') else "📄 CSV (Zerodha)"
                file_size = f"{file.size / 1024:.1f} KB"
                st.write(f"{file_type} - **{file.name}** ({file_size})")
            
            st.session_state.uploaded_files = uploaded_files
            
            st.markdown("##")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.step = 1
                    st.rerun()
            with col2:
                has_pdfs = any(f.name.endswith('.pdf') for f in uploaded_files)
                button_text = "Next: Enter Password →" if has_pdfs else "Next: Analysis →"
                next_step = 3 if has_pdfs else 4
                
                if st.button(button_text, type="primary", use_container_width=True):
                    st.session_state.step = next_step
                    st.rerun()
        else:
            st.warning("⚠️ Please upload at least one file to continue")
            st.markdown("##")
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 1
                st.rerun()
    
    # Step 3: Password (only if PDFs uploaded)
    elif st.session_state.step == 3:
        st.header("🔐 Step 3: Enter PDF Password")
        
        st.info("🔒 Groww PDFs are password-protected. Enter your **PAN number in UPPERCASE** (e.g., ABCDE1234F)")
        
        pdf_password = st.text_input(
            "PDF Password",
            type="password",
            placeholder="Enter your PAN number",
            help="Usually your PAN number in uppercase letters",
            key="password_input"
        )
        
        st.session_state.pdf_password = pdf_password if pdf_password else None
        
        st.markdown("##")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
        
        with col2:
            if st.button("Skip (No Password)", use_container_width=True):
                st.session_state.pdf_password = None
                st.session_state.step = 4
                st.rerun()
        
        with col3:
            if st.button("Next: Analysis →", type="primary", use_container_width=True):
                if not pdf_password:
                    st.warning("⚠️ Please enter a password or click 'Skip'")
                else:
                    st.session_state.step = 4
                    st.rerun()
    
    # Step 4: Analysis
    elif st.session_state.step == 4:
        uploaded_files = st.session_state.uploaded_files
        pdf_password = st.session_state.pdf_password
        
        if not uploaded_files:
            st.error("❌ No files uploaded!")
            if st.button("← Back to Upload", use_container_width=True):
                st.session_state.step = 2
                st.rerun()
            return
        
        st.header("📈 Step 4: Portfolio Analysis")
        
        # Process files and group by account
        file_info = {}
        account_groups = {}
        
        with st.spinner("📂 Loading and analyzing files..."):
            for uploaded_file in uploaded_files:
                outflows, inflows, filename, account_id = process_uploaded_file(uploaded_file, pdf_password)
                
                if outflows is not None and inflows is not None:
                    if account_id is None:
                        account_id = filename
                    
                    file_info[filename] = {
                        'account_id': account_id,
                        'outflows': outflows,
                        'inflows': inflows
                    }
                    
                    if account_id not in account_groups:
                        account_groups[account_id] = []
                    account_groups[account_id].append(filename)
        
        # Display account grouping
        if len(account_groups) > 0:
            with st.expander("ℹ️ Account Grouping Information", expanded=True):
                for account_id, files in account_groups.items():
                    if len(files) > 1:
                        is_pan = account_id and len(account_id) == 10 and account_id[0].isalpha()
                        icon = "🏦" if is_pan else "📁"
                        st.success(f"{icon} **{account_id}** - Combined {len(files)} file(s) from same account")
                        for f in files:
                            st.write(f"  • {f}")
                    else:
                        st.write(f"📄 {account_id}")
        
        # Get portfolio values for each account
        accounts_data = []
        
        st.markdown("### 💰 Enter Current Portfolio Values")
        
        for account_id, files in account_groups.items():
            # Combine transactions
            combined_outflows = []
            combined_inflows = []
            
            for filename in files:
                info = file_info[filename]
                combined_outflows.append(info['outflows'])
                combined_inflows.append(info['inflows'])
            
            account_outflows = pd.concat(combined_outflows, ignore_index=True) if combined_outflows else pd.DataFrame()
            account_inflows = pd.concat(combined_inflows, ignore_index=True) if combined_inflows else pd.DataFrame()
            
            if len(account_outflows) == 0:
                st.warning(f"⚠️ No deposits found for {account_id}. Skipping...")
                continue
            
            # Display name
            is_pan = account_id and len(account_id) == 10 and account_id[0].isalpha()
            account_name = f"Groww Account (PAN: {account_id})" if is_pan else account_id
            
            with st.expander(f"💼 {account_name}", expanded=True):
                if len(files) > 1:
                    st.info(f"📊 Combined: {len(account_outflows)} deposits, {len(account_inflows)} withdrawals")
                else:
                    st.success(f"✓ {len(account_outflows)} deposits, {len(account_inflows)} withdrawals")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    holdings = st.number_input(
                        "Current Holdings Value (₹)",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        key=f"holdings_{account_id}",
                        help="Total market value of stocks/securities"
                    )
                
                with col2:
                    cash = st.number_input(
                        "Available Cash (₹)",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        key=f"cash_{account_id}",
                        help="Available cash balance"
                    )
                
                current_value = holdings + cash
                
                accounts_data.append({
                    'name': account_name,
                    'outflows': account_outflows,
                    'inflows': account_inflows,
                    'current_value': current_value
                })
        
        # Calculate and display results
        if accounts_data:
            if st.button("🔢 Calculate XIRR & Generate Report", type="primary", use_container_width=True):
                with st.spinner("🧮 Calculating XIRR and fetching Nifty 50 data..."):
                    
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
                    
                    # Display results
                    st.markdown("---")
                    st.header("📊 Results")
                    
                    if len(accounts_data) > 1:
                        st.subheader("Individual Account Analysis")
                        
                        for i, stats in enumerate(individual_stats):
                            with st.expander(f"Account: {stats['file_name']}", expanded=False):
                                display_portfolio_metrics(stats, f"Account {i+1}")
                                display_nifty_comparison(stats)
                    
                    # Combined analysis
                    st.subheader("Combined Portfolio Analysis")
                    
                    combined_outflows = pd.concat(all_outflows, ignore_index=True)
                    combined_inflows = pd.concat(all_inflows, ignore_index=True)
                    combined_value = sum(all_values)
                    
                    combined_stats = calculate_portfolio_stats(
                        combined_outflows,
                        combined_inflows,
                        combined_value,
                        "Combined Portfolio"
                    )
                    
                    display_portfolio_metrics(combined_stats, "Overall Performance")
                    display_nifty_comparison(combined_stats)
                    
                    # Summary table
                    if len(accounts_data) > 1:
                        st.subheader("📋 Summary Comparison")
                        
                        summary_data = []
                        for stats in individual_stats:
                            summary_data.append({
                                'Account': stats['file_name'],
                                'Invested': format_currency(stats['total_invested']),
                                'Withdrawn': format_currency(stats['total_withdrawn']),
                                'Current': format_currency(stats['current_value']),
                                'Gain/Loss': format_currency(stats['net_gain']),
                                'XIRR': f"{stats['xirr_percentage']:.2f}%" if stats['xirr_percentage'] else "N/A"
                            })
                        
                        summary_data.append({
                            'Account': 'COMBINED',
                            'Invested': format_currency(combined_stats['total_invested']),
                            'Withdrawn': format_currency(combined_stats['total_withdrawn']),
                            'Current': format_currency(combined_stats['current_value']),
                            'Gain/Loss': format_currency(combined_stats['net_gain']),
                            'XIRR': f"{combined_stats['xirr_percentage']:.2f}%" if combined_stats['xirr_percentage'] else "N/A"
                        })
                        
                        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
                    
                    # Generate PDF
                    st.markdown("---")
                    st.subheader("📄 Download Report")
                    
                    try:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        pdf_filename = f"xirr_report_{timestamp}.pdf"
                        temp_pdf = f"temp_{pdf_filename}"
                        
                        generate_pdf_report(individual_stats, combined_stats, temp_pdf)
                        
                        with open(temp_pdf, "rb") as f:
                            pdf_data = f.read()
                        
                        os.remove(temp_pdf)
                        
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=pdf_data,
                            file_name=pdf_filename,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                        
                        st.success("✓ PDF report ready for download!")
                        
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                    
                    # Start over button
                    st.markdown("##")
                    if st.button("🔄 Start Over", use_container_width=True):
                        # Clear all session state
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        # Reset to step 1
                        st.session_state.step = 1
                        st.session_state.uploaded_files = []
                        st.session_state.pdf_password = None
                        st.rerun()
        
        else:
            st.warning("Please enter portfolio values for at least one account")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ by Ankit Bhardwaj | <a href='https://github.com/ankitjgd/xirrcalculator' target='_blank'>View on GitHub</a></p>
        <p><small>This tool is for informational purposes only. Always verify calculations independently.</small></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
