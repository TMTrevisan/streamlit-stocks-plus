import streamlit as st
import pandas as pd
from power_gauge import calculate_power_gauge

def render_power_gauge(ticker):
    st.header(f"⚡ Power Gauge Rating: {ticker}")
    st.caption("A 20-Factor Model analyzing Financials, Earnings, Technicals, and Experts.")
    
    with st.expander("Methodology: Power Gauge Analysis"):
        st.markdown("""
        **20-Factor Weighted Model:**
        - **Financials**: Debt/Equity, ROE, Price/Book, FCF Yield.
        - **Earnings**: 5yr Growth, Estimates, EPS Surprises, Trend.
        - **Technicals**: Relative Strength, Price Trend, Moving Averages.
        - **Experts**: Insider Transactions, Short Interest, Analyst Ratings.
        """)
    
    # Check Session State First
    ad = st.session_state.get('analysis_data', {})
    gauge = None
    
    if ad.get('ticker') == ticker and ad.get('power_gauge'):
        gauge = ad['power_gauge']
    
    # Fallback Button (or "Run Analysis" if not triggered automatically)
    if not gauge:
        if st.button("Generate Power Report", key="run_power_gauge"):
            with st.spinner(f"Analyzing {ticker} across 20 data points..."):
                gauge = calculate_power_gauge(ticker)
    
    if gauge:
        # Top Level Result
        col_g1, col_g2 = st.columns([1, 2])
        
        with col_g1:
            st.metric("Power Rating", gauge['rating'], delta=f"{gauge['score']:.1f}/100")
            
            # Simple Gauge Visual (Progress Bar)
            st.progress(int(gauge['score']))
            if gauge['rating'] == "BULLISH":
                st.success("Strong Buy Signal")
            elif gauge['rating'] == "BEARISH":
                st.error("Avoid / Sell Signal")
            else:
                st.warning("Neutral / Hold")
                
        with col_g2:
            # Radar Chart or Bar Chart of Categories
            cat_df = pd.DataFrame.from_dict(gauge['categories'], orient='index', columns=['Score'])
            st.bar_chart(cat_df)
        
        st.divider()
        
        # Detailed Breakdown (4 Quadrants)
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        
        def render_category(col, title, data):
            with col:
                st.subheader(title)
                for factor, score in data.items():
                    st.write(f"**{factor}**")
                    st.progress(int(score))
        
        render_category(c1, "💰 Financials", gauge['details']['Financials'])
        render_category(c2, "📈 Earnings", gauge['details']['Earnings'])
        render_category(c3, "🛠️ Technicals", gauge['details']['Technicals'])
        render_category(c4, "🧠 Experts", gauge['details']['Experts'])
    elif not gauge and ticker:
        st.warning(f"⚠️ Power Gauge data unavailable for {ticker}. Check connection or API limits.")
        if st.button("Retry Power Gauge", key="retry_power_gauge"):
             st.session_state.analysis_data = {'ticker': None} # Force reset
             st.rerun()
