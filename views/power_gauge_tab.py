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
        
        # Custom CSS for progress bars and layout
        st.markdown("""
        <style>
        .pg-card {
            background-color: #1e293b;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        }
        .pg-title {
            color: #e2e8f0;
            font-size: 1.2rem;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .pg-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .pg-label {
            color: #94a3b8;
            font-size: 0.9rem;
            width: 40%;
        }
        .pg-bar-container {
            width: 55%;
            background-color: #334155;
            height: 10px;
            border-radius: 5px;
            position: relative;
            overflow: hidden;
        }
        .pg-bar-fill {
            height: 100%;
            border-radius: 5px;
            transition: width 0.5s ease-in-out;
        }
        
        /* Gradients based on score */
        .color-green { background: linear-gradient(90deg, #ef4444 0%, #eab308 50%, #22c55e 100%); }
        .color-yellow { background: linear-gradient(90deg, #ef4444 0%, #eab308 100%); }
        .color-red { background: linear-gradient(90deg, #ef4444 100%, #ef4444 100%); }
        
        .expert-highlight .pg-title { color: #38bdf8; }
        .expert-highlight { border: 1px solid #0ea5e9; box-shadow: 0 0 10px rgba(14, 165, 233, 0.2); }
        </style>
        """, unsafe_allow_html=True)
        
        def render_category(col, title, data, highlight=False):
            highlight_class = "expert-highlight" if highlight else ""
            
            html = f"""
            <div class="pg-card {highlight_class}">
                <div class="pg-title">{title}</div>
            """
            
            for factor, score in data.items():
                # Determine color class
                if score >= 65: color_class = "color-green"
                elif score >= 35: color_class = "color-yellow"
                else: color_class = "color-red"
                
                # Special highlight for CMF
                label_display = factor
                if factor == "Chaikin Money Flow":
                    label_display = f'<span style="color: #22c55e; font-weight: bold;">{factor} (CMF)</span>'
                
                html += f"""
                <div class="pg-row">
                    <div class="pg-label">{label_display}</div>
                    <div class="pg-bar-container">
                        <div class="pg-bar-fill {color_class}" style="width: {score}%;"></div>
                    </div>
                </div>
                """
            html += "</div>"
            with col:
                st.markdown(html, unsafe_allow_html=True)
        
        render_category(c1, "💰 Financials", gauge['details']['Financials'])
        render_category(c2, "📈 Earnings", gauge['details']['Earnings'])
        render_category(c3, "🛠️ Technicals", gauge['details']['Technicals'])
        render_category(c4, "🧠 Experts (The Secret Sauce)", gauge['details']['Experts'], highlight=True)
    elif not gauge and ticker:
        st.warning(f"⚠️ Power Gauge data unavailable for {ticker}. Check connection or API limits.")
        if st.button("Retry Power Gauge", key="retry_power_gauge"):
             st.session_state.analysis_data = {'ticker': None} # Force reset
             st.rerun()
