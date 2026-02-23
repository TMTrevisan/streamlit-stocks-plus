import streamlit as st
from weinstein import get_weinstein_stage

def render_weinstein(ticker):
    st.header(f"📉 Weinstein Stage Analysis: {ticker}")
    st.caption("Weekly Chart Analysis using 30-Week SMA and Relative Strength.")
    
    with st.expander("Methodology: Weinstein Stage Analysis"):
        st.markdown("""
        **Stan Weinstein's 4 Stages:**
        1.  **Stage 1 (Basing)**: Price oscillates sideways. Moving Average (MA) flattens. Avoid.
        2.  **Stage 2 (Advancing)**: Breakout on high volume. Price > Rising 30-week MA. **Buy Zone.**
        3.  **Stage 3 (Topping)**: Momentum slows. Price chops around flat MA. Sell/Hold.
        4.  **Stage 4 (Declining)**: Price breaks below falling MA. **Avoid/Short.**
        """)
    
    # Check Session State First
    ad = st.session_state.get('analysis_data', {})
    w_data = None
    
    if ad.get('ticker') == ticker and ad.get('weinstein'):
        w_data = ad['weinstein']
        
    if not w_data:
        if st.button("Analyze Stage", key="run_weinstein"):
            with st.spinner("Analyzing Weekly Price Action..."):
                w_data = get_weinstein_stage(ticker)
            
    if w_data:
        # Top Result
        st.metric("Current Stage", w_data['stage'], delta=f"Slope: {w_data['slope']:.2%}")
        
        # Chart
        st.line_chart(w_data['data'][['Close', 'SMA30']])
        
        # Details
        st.subheader("Stage Criteria Check")
        for detail in w_data['details']:
            st.write(detail)
            
        st.info(f"Mansfield Relative Strength: {w_data['mansfield_rs']:.2f}")
    elif not w_data and ticker:
        st.warning(f"⚠️ Stage Analysis data unavailable for {ticker}.")
        if st.button("Retry Stage Analysis", key="retry_weinstein"):
             st.session_state.analysis_data = {'ticker': None} # Force reset
             st.rerun()
