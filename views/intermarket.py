import streamlit as st
from macro_analysis import (
    fetch_macro_data, 
    get_yield_curve_data, 
    get_asset_performance, 
    render_yield_curve_chart, 
    render_intermarket_chart
)

def render_intermarket(track_api_call):
    st.title("🌐 Macro & Intermarket Intelligence")
    st.markdown("""
    **The Big Picture:** Analyzing relationships between bonds, commodities, currencies, and equities.
    """)
    
    with st.spinner("🌍 Loading macro indicators..."):
        track_api_call()
        macro_data = fetch_macro_data()
        
    if not macro_data.empty:
        # --- Top Level Metrics ---
        # Latest values
        try:
            # Safely access data handling both MultiIndex and standard structures
            closes = macro_data['Close'] if 'Close' in macro_data else macro_data
            
            # Helper to get last valid value
            def get_last(ticker):
                if ticker in closes:
                    return closes[ticker].dropna().iloc[-1]
                return 0
            
            us10y = get_last('^TNX')
            oil = get_last('CL=F')
            gold = get_last('GC=F')
            dxy = get_last('DX-Y.NYB')
            btc = get_last('BTC-USD')
            
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            
            m_col1.metric("US 10Y Yield", f"{us10y:.2f}%")
            m_col2.metric("Crude Oil", f"${oil:.2f}")
            m_col3.metric("Gold", f"${gold:,.0f}")
            m_col4.metric("Dollar Index", f"{dxy:.2f}")
            m_col5.metric("Bitcoin", f"${btc:,.0f}")
            
        except Exception as e:
            st.error(f"Error displaying metrics: {e}")
            
        st.divider()
        
        # --- Yield Curve Section ---
        st.subheader("Yield Curve Dynamics")
        yield_data = get_yield_curve_data(macro_data)
        
        if yield_data is not None:
            fig_yield = render_yield_curve_chart(yield_data)
            st.plotly_chart(fig_yield, width="stretch")
            
            last_spread = yield_data['Spread'].dropna().iloc[-1]
            if last_spread < 0:
                st.error(f"🚨 **Yield Curve Inverted ({last_spread:.2f} bps)**: Historical precursor to recession.")
            else:
                st.success(f"✅ **Normal Yield Curve (+{last_spread:.2f} bps)**: Healthy lending environment.")
        
        st.divider()
        
        # --- Intermarket Performance ---
        st.subheader("Asset Class Performance (1 Year)")
        perf_df = get_asset_performance(macro_data)
        
        if perf_df is not None:
            fig_perf = render_intermarket_chart(perf_df)
            st.plotly_chart(fig_perf, width="stretch")
            
            # Correlation Quick Check
            st.info("""
            **Intermarket Insights:**
            - **Strong Dollar** usually pressures Gold & Equities.
            - **Rising Yields** typically hurt Growth Stocks & Gold.
            - **Oil Spikes** can signal inflationary pressure (bad for bonds).
            """)
            
    else:
        st.warning("Unable to load macro data. Please check connection.")
    
    st.markdown("---")
