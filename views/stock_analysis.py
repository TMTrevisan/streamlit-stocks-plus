import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components

# Import direct dependencies
from services.data_fetcher import fetch_stock_history, fetch_stock_info
from fundamental_metrics import fetch_fundamental_data, format_large_number
from services.logger import setup_logger
logger = setup_logger(__name__)

def render_stock_analysis(ticker, track_api_call, run_analysis_pipeline, calculate_mphinancial_mechanics, get_tv_symbol):
    st.title("📉 Stock Analysis (Mphinancial Engine)")
    
    # --- CONSOLIDATED STRATEGY DASHBOARD ---
    # Retrieve Data
    ad = st.session_state.get('analysis_data', {})
    
    if ticker and ad.get('ticker') == ticker:
        st.markdown("### 🧭 Strategy Dashboard")
        adb1, adb2, adb3 = st.columns(3)
        
        with adb1:
            if ad.get('power_gauge'):
                pg = ad['power_gauge']
                st.metric("⚡ Power Gauge", pg['rating'], delta=f"{pg['score']:.1f}/100")
            else:
                st.metric("⚡ Power Gauge", "N/A")
                
        with adb2:
            if ad.get('weinstein'):
                ws = ad['weinstein']
                # Parse short stage name
                try:
                    stage_name = ws['stage'].split(' (')[0]
                except Exception as e:
                    logger.info(f"Error parsing Weinstein stage string: {e}")
                    stage_name = ws['stage']
                st.metric("📉 Weinstein Stage", stage_name, delta=f"Slope: {ws['slope']:.2%}")
            else:
                 st.metric("📉 Weinstein Stage", "N/A")
    
        with adb3:
            if ad.get('canslim'):
                cs = ad['canslim']
                st.metric("🚀 CANSLIM Score", f"{cs['score']}/7", delta="Growth")
            else:
                st.metric("🚀 CANSLIM Score", "N/A")
        
        # Add Retry/Run Button if any data is missing
        if not ad.get('power_gauge') or not ad.get('weinstein') or not ad.get('canslim'):
            if st.button("🔄 Run Full Strategy Analysis", key="btn_run_full_analysis"):
                with st.spinner(f"Running multi-strategy analysis for {ticker}..."):
                    run_analysis_pipeline(ticker)
                    st.rerun()
        
        st.divider()

    if ticker:
        # Use 2y to ensure 200 SMA has enough data to stabilize
        track_api_call()  # Track stock data fetch
        data = fetch_stock_history(ticker)
        info = fetch_stock_info(ticker)
        
        if not data.empty and len(data) > 200:

            # Flatten MultiIndex columns if present (common with newer yfinance)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = calculate_mphinancial_mechanics(data)
            
            # Pull latest scalars correctly using .item() or float() to avoid Series ambiguity
            last_row = data.iloc[-1]
            price = float(last_row['Close'])
            sma200 = float(last_row['SMA200'])
            adx_val = float(last_row['ADX']) if not pd.isna(last_row['ADX']) else 0.0
            ema21 = float(last_row['EMA21'])
            atr = float(last_row['ATR']) if not pd.isna(last_row['ATR']) else 0.0
            
            # --- HEADER SECTION ---
            st.markdown("### Key Metrics")
            col_m1, col_m2, col_m3 = st.columns(3)
        
            # Use custom HTML for better visibility
            col_m1.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Current Price</p>
                <h2 style='color: white; margin: 5px 0;'>${price:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col_m2.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>ADX Strength</p>
                <h2 style='color: white; margin: 5px 0;'>{adx_val:.1f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            col_m3.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>ATR (Volatility)</p>
                <h2 style='color: white; margin: 5px 0;'>${atr:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            if info:
                # --- FUNDAMENTALS ROW ---
                st.markdown("### Fundamentals")
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                
                mkt_cap = info.get('marketCap', 0)
                pe_ratio = info.get('trailingPE', 0)
                div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                sector = info.get('sector', 'N/A')
                industry = info.get('industry', 'N/A')
                
                # Removed local format_large_number and using the imported one directly
                
                f_col1.metric("Market Cap", format_large_number(mkt_cap))
                f_col2.metric("P/E Ratio", f"{pe_ratio:.2f}" if pe_ratio else "N/A")
                f_col3.metric("Div Yield", f"{div_yield:.2f}%")
                f_col4.metric("Sector", sector)
                
                with st.expander(f"🏢 Company Profile: {info.get('longName', ticker)}"):
                    st.write(f"**Industry:** {industry}")
                    st.write(f"**Website:** {info.get('website', 'N/A')}")
                    st.write(info.get('longBusinessSummary', 'No description available.'))
            
            st.divider()

            # --- MAIN CONTENT ---
            chart_col, audit_col = st.columns([2, 1])

            with chart_col:
                st.subheader(f"📊 {ticker} Visual Audit")
                fig = go.Figure(data=[go.Candlestick(
                    x=data.index, open=data['Open'], high=data['High'], 
                    low=data['Low'], close=data['Close'], name="Price")])
                
                # Add the EMA Stack to the chart
                colors = ['#00ffcc', '#00ccff', '#3366ff', '#6633ff', '#ff33cc']
                for i, p in enumerate([8, 21, 34, 55, 89]):
                    fig.add_trace(go.Scatter(x=data.index, y=data[f'EMA{p}'], 
                                             name=f'EMA{p}', line=dict(color=colors[i], width=1.5)))
                
                # Add the Wind (200 SMA)
                fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], 
                                         name='SMA 200 (The Wind)', line=dict(color='white', width=3, dash='dash')))
                
                fig.update_layout(template="plotly_dark", height=600, margin=dict(l=0, r=0, t=0, b=0))
                # Explicit key to force re-render when ticker changes
                st.caption(f"Displaying data for: **{ticker}**")
                st.plotly_chart(fig, width="stretch", key=f"main_chart_{ticker}")

            with audit_col:
                st.subheader("⚙️ Mechanics Check")
                
                # 1. Trend (The Wind)
                if price > sma200:
                    st.success("✅ SAILING WITH THE WIND: Price is above 200 SMA.")
                else:
                    st.error("❌ STAGNANT WATER: Price is below 200 SMA. No Long setup.")

                # 2. The Stack - FIXED: Individual comparisons to avoid "truth value of Series" error
                e8, e21, e34, e55, e89 = (float(last_row['EMA8']), float(last_row['EMA21']), 
                                          float(last_row['EMA34']), float(last_row['EMA55']), float(last_row['EMA89']))
                
                is_stacked = (e8 > e21) and (e21 > e34) and (e34 > e55) and (e55 > e89)
                
                if is_stacked:
                    st.success("✅ BULLISH STACK: EMAs are in perfect alignment.")
                else:
                    st.warning("⚠️ DISORDERED STACK: Trend lacks momentum.")
                
                # Display Raw EMA List
                with st.expander("View Raw EMA Stack Data"):
                    for p in [8, 21, 34, 55, 89]:
                        st.write(f"**EMA {p}:** ${float(last_row[f'EMA{p}']):.2f}")

                # 3. The Buy Zone (ATR logic)
                dist_to_21 = abs(price - ema21)
                in_buy_zone = dist_to_21 <= atr
                
                if in_buy_zone:
                    st.info("🎯 IN THE BUY ZONE: Price is within 1 ATR of the 21 EMA.")
                else:
                    st.warning(f"⌛ OVEREXTENDED: Price is > 1 ATR ({atr:.2f}) from 21 EMA. Wait for pullback.")

                # --- THE FINAL VERDICT ---
                st.divider()
                # Added ADX check to the final verdict logic
                if price > sma200 and is_stacked and adx_val >= 20 and in_buy_zone:
                    # Balloons removed per user request
                    st.markdown("### 🏆 HIGH QUALITY SETUP")
                    st.write("All Phinancial mechanics are aligned for an entry.")
                else:
                    st.markdown("### 🔍 MONITORING MODE")
                    st.write("Wait for all mechanical criteria to align.")
            
            
            # --- FUNDAMENTAL HEALTH (ROIC.AI STYLE) ---
            st.divider()
            st.subheader(f"📊 Fundamental Health: {ticker}")
            
            track_api_call()  # Track Fundamental Data Fetch
            fund_data = fetch_fundamental_data(ticker)
            
            if fund_data:
                # Row 1: The "Quality" Metrics (ROIC focus)
                f_col1, f_col2, f_col3, f_col4 = st.columns(4)
                
                # Helper for consistent styling
                def metric_box(label, value, subtext="", color="#1e3a5f"):
                    st.markdown(f"""
                    <div style='background-color: {color}; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #374151;'>
                        <p style='color: #94a3b8; margin: 0; font-size: 0.85em; text-transform: uppercase;'>{label}</p>
                        <h3 style='color: white; margin: 4px 0; font-size: 1.4em;'>{value}</h3>
                        <p style='color: #d1d5db; margin: 0; font-size: 0.75em;'>{subtext}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with f_col1:
                    metric_box("ROIC (Est)", f"{fund_data['roic']*100:.1f}%", "Return on Capital", "#1a4d2e" if fund_data['roic'] > 0.15 else "#1e3a5f")
                with f_col2:
                    metric_box("Op Margin", f"{fund_data['operating_margin']*100:.1f}%", "Operational Efficiency")
                with f_col3:
                    metric_box("Free Cash Flow", format_large_number(fund_data['fcf']), "Cash Generation")
                with f_col4:
                    metric_box("ROE", f"{fund_data['roe']*100:.1f}%", "Return on Equity")
                
                # Row 2: Valuation & Growth
                st.markdown("")
                v_col1, v_col2, v_col3, v_col4 = st.columns(4)
                
                with v_col1:
                    metric_box("P/E Ratio", f"{fund_data['pe_ratio']:.1f}", "Trailing 12m")
                with v_col2:
                    metric_box("Rev Growth", f"{fund_data['revenue_growth']*100:.1f}%", "Year over Year", "#1a4d2e" if fund_data['revenue_growth'] > 0.1 else "#1e3a5f")
                with v_col3:
                    metric_box("Total Cash", format_large_number(fund_data['total_cash']), "Balance Sheet")
                with v_col4:
                    metric_box("Total Debt", format_large_number(fund_data['total_debt']), "Balance Sheet")
                
                st.divider()
                st.subheader("📚 Advanced Financials (TradingView)")
                
                # Check for Equity type (Financials not available for ETFs/Crypto usually)
                q_type = fund_data.get('quote_type', '').upper() if fund_data else ''
                
                if 'EQUITY' in q_type:
                    tv_symbol = get_tv_symbol(ticker)
                    components.html(f"""
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-financials.js" async>
  {{
  "symbol": "{tv_symbol}",
  "colorTheme": "dark",
  "isTransparent": false,
  "displayMode": "regular",
  "width": "100%",
  "height": "100%",
  "locale": "en"
}}
  </script>
</div>
                    """, height=1400)
                else:
                    st.info(f"Financials widget is typically available for Equities. Current asset type: {q_type or 'Unknown'}")
                    
            else:
                st.warning("Could not fetch fundamental data.")
        elif not data.empty:
            st.warning(f"Insufficient historical data for {ticker} (need at least 200 days).")
    else:
        st.info("Enter a ticker in the sidebar to begin analysis")
