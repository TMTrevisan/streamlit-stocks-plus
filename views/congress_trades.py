import streamlit as st
import pandas as pd
import re
from congress_tracker import fetch_congress_members, fetch_stock_disclosures, get_top_traded_tickers, get_active_traders, check_watchlist_overlap

def render_congress_trades(track_api_call):
    st.title("🏛️ Congressional Trading Tracker")
    
    # API Verification
    api_key = st.session_state.get('user_congress_key') or st.secrets.get("congress_api_key")
    
    if not api_key:
        st.warning("⚠️ **API Config Required:** Please enter your [Congress.gov API Key](https://api.congress.gov/sign-up/) in the sidebar settings ⚙️ to enable live tracking. Showing mock data below.")
        members = pd.DataFrame()
    else:
        # Verify connectivity (Visual indicator)
        with st.spinner("Connecting to Congress.gov..."):
            members = fetch_congress_members(api_key=api_key)
            if members.empty:
                st.warning("⚠️ Could not connect to Congress.gov API. Showing mock data.")
            else:
                st.caption(f"✅ Connected: Tracking {len(members)} active members")

    st.markdown("""
    Track stock trades disclosed by members of Congress under the STOCK Act.
    Congress members must disclose trades within 45 days of execution.
    
    > **Note: The trade data presented below is currently a static MOCK dataset for demonstration purposes.**
    """)
    
    with st.spinner("🏛️ Loading Congressional trades..."):
        track_api_call()  # Track Congress API call
        trades_df = fetch_stock_disclosures()
    
    if trades_df.empty:
        st.error("Could not fetch Congressional trading data")
    else:
        # Summary metrics
        st.subheader("Recent Activity Summary")
        
        sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
        
        purchases = len(trades_df[trades_df['transaction'] == 'Purchase'])
        sales = len(trades_df[trades_df['transaction'] == 'Sale'])
        unique_tickers = trades_df['ticker'].nunique()
        unique_traders = trades_df['member'].nunique()
        
        sum_col1.markdown(f"""
        <div style='background-color: #1a4d2e; padding: 15px; border-radius: 8px; text-align: center;'>
            <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Purchases</p>
            <h2 style='color: white; margin: 5px 0;'>{purchases}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        sum_col2.markdown(f"""
        <div style='background-color: #4d1a1a; padding: 15px; border-radius: 8px; text-align: center;'>
            <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Sales</p>
            <h2 style='color: white; margin: 5px 0;'>{sales}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        sum_col3.markdown(f"""
        <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
            <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Unique Tickers</p>
            <h2 style='color: white; margin: 5px 0;'>{unique_tickers}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        sum_col4.markdown(f"""
        <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
            <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Active Traders</p>
            <h2 style='color: white; margin: 5px 0;'>{unique_traders}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Two columns: Recent Trades and Top Tickers
        trade_col, ticker_col = st.columns([2, 1])
        
        with trade_col:
            st.subheader("Recent Trades")
            
            # Style the trades table
            display_trades = trades_df[['date', 'member', 'party', 'ticker', 'transaction', 'amount']].copy()
            display_trades.columns = ['Date', 'Member', 'Party', 'Ticker', 'Type', 'Amount']
            
            def color_transaction(val):
                if val == 'Purchase':
                    return 'background-color: #1a4d2e; color: white'
                elif val == 'Sale':
                    return 'background-color: #4d1a1a; color: white'
                return ''
            
            def color_party(val):
                if val == 'D':
                    return 'background-color: #1e3a5f; color: white'
                elif val == 'R':
                    return 'background-color: #5f1e1e; color: white'
                return ''
            
            styled_trades = display_trades.style.applymap(
                color_transaction, subset=['Type']
            ).applymap(
                color_party, subset=['Party']
            )
            
            st.dataframe(styled_trades, width="stretch", hide_index=True)
        
        with ticker_col:
            st.subheader("Most Traded Tickers")
            
            top_tickers = get_top_traded_tickers(trades_df, n=5)
            
            if not top_tickers.empty:
                for _, row in top_tickers.iterrows():
                    st.markdown(f"""
                    <div style='background-color: #1e3a5f; padding: 10px; border-radius: 5px; margin-bottom: 8px;'>
                        <h4 style='margin: 0; color: white;'>{row['ticker']}</h4>
                        <p style='margin: 0; color: #94a3b8; font-size: 0.85em;'>{row['trade_count']} trade(s)</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # Active Traders
        st.subheader("Most Active Traders")
        
        active_traders = get_active_traders(trades_df, n=5)
        
        if not active_traders.empty:
            trader_cols = st.columns(len(active_traders))
            
            for col, (_, trader) in zip(trader_cols, active_traders.iterrows()):
                party_color = "#1e3a5f" if trader['party'] == 'D' else "#5f1e1e"
                with col:
                    st.markdown(f"""
                    <div style='background-color: {party_color}; padding: 15px; border-radius: 8px; text-align: center;'>
                        <h4 style='margin: 0; color: white; font-size: 0.9em;'>{trader['member']}</h4>
                        <p style='margin: 5px 0; color: #94a3b8;'>{trader['party']} - {trader['state']}</p>
                        <h3 style='margin: 0; color: #4ade80;'>{trader['trade_count']} trades</h3>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        # Watchlist Overlap
        st.subheader("Check Your Watchlist")
        
        watchlist_input = st.text_input(
            "Enter tickers (comma-separated):",
            placeholder="e.g., NVDA, AAPL, TSLA, META"
        )
        if watchlist_input:
            # Sanitize each ticker individually while keeping commas
            watchlist_input = ','.join([re.sub(r'[^A-Z0-9-]', '', t.upper().strip()) for t in watchlist_input.split(',')])
        
        if watchlist_input:
            watchlist = [t.strip().upper() for t in watchlist_input.split(',')]
            overlap = check_watchlist_overlap(trades_df, watchlist)
            
            if not overlap.empty:
                st.success(f"Found {len(overlap)} Congressional trade(s) matching your watchlist!")
                st.dataframe(overlap[['date', 'member', 'party', 'ticker', 'transaction', 'amount']], 
                            width="stretch", hide_index=True)
            else:
                st.info("No Congressional trades match your watchlist tickers.")
        
        # Disclaimer
        st.divider()
        st.caption("""
        **Disclaimer:** Congressional trading data is subject to 45-day disclosure delays. 
        This information is for educational purposes only and should not be considered investment advice.
        Past Congressional trades do not guarantee future performance.
        """)
