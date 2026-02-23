import streamlit as st
from canslim import get_canslim_metrics

def render_canslim(ticker):
    st.header(f"🚀 CANSLIM Growth Strategy: {ticker}")
    st.caption("William O'Neil's 7-Factor Growth Model.")
    
    with st.expander("Methodology: CANSLIM Growth"):
        st.markdown("""
        **William O'Neil's Checklist:**
        - **C**urrent Earnings: EPS Growth > 25%?
        - **A**nnual Earnings: 3-5yr Growth > 25%?
        - **N**ew Highs/Products: Trading near 52w High?
        - **S**upply/Demand: Volume surges on accumulation?
        - **L**eader: Relative Strength > 80?
        - **I**nstitutional Sponsorship: Increasing ownership?
        - **M**arket Direction: Is the general market in an uptrend?
        """)
    
    # Check Session State First
    ad = st.session_state.get('analysis_data', {})
    c_data = None
    
    if ad.get('ticker') == ticker and ad.get('canslim'):
        c_data = ad['canslim']
        
    if not c_data:
        if st.button("Run CANSLIM Check", key="run_canslim"):
            with st.spinner("Checking Fundamental & Technical Growth Factors..."):
                c_data = get_canslim_metrics(ticker)
            
    if c_data:
        score = c_data['score']
        st.metric("CANSLIM Score", f"{score}/7", delta="Bullish" if score >= 5 else "Neutral/Bearish")
        
        if score >= 6:
            st.success("High Growth Potential (Watchlist Candidate)")
        elif score <= 2:
            st.error("Weak Growth Characteristics")
        
        st.divider()
        
        # Checklist UI
        col_c1, col_c2 = st.columns(2)
        
        checklist = c_data['checklist']
        items = list(checklist.items())
        mid = len(items) // 2
        
        for k, v in items[:mid]:
            with col_c1:
                st.checkbox(f"{k}: {v['value']}", value=v['pass'], key=k, disabled=True)
                
        for k, v in items[mid:]:
            with col_c2:
                st.checkbox(f"{k}: {v['value']}", value=v['pass'], key=k+"2", disabled=True)

    elif not c_data and ticker:
        st.warning(f"⚠️ CANSLIM data unavailable for {ticker}.")
        if st.button("Retry CANSLIM Check", key="retry_canslim"):
             st.session_state.analysis_data = {'ticker': None} # Force reset
             st.rerun()
