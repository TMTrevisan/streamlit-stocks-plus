import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components

from asbury_metrics import get_asbury_6_signals, get_asbury_6_historical
from services.logger import setup_logger
logger = setup_logger(__name__)

def render_market_health(render_mini_chart_html, track_api_call):
    st.subheader("Market Snapshot")
    # Grid Layout for Indices
    mc1, mc2, mc3 = st.columns(3)
    with mc1:
        components.html(render_mini_chart_html("FOREXCOM:SPXUSD", "S&P 500"), height=220)
        components.html(render_mini_chart_html("FX:EURUSD", "EUR/USD"), height=220)
    with mc2:
        components.html(render_mini_chart_html("FOREXCOM:NSXUSD", "Nasdaq 100"), height=220)
        components.html(render_mini_chart_html("BITSTAMP:BTCUSD", "Bitcoin"), height=220)
    with mc3:
        components.html(render_mini_chart_html("FOREXCOM:DJI", "Dow 30"), height=220)
        components.html(render_mini_chart_html("CMCMARKETS:GOLD", "Gold"), height=220)
    
    st.divider()
    st.title("📊 Market Health Gauge (A6)")
    st.markdown("""
    The Asbury 6 is a quantitative, daily gauge of US equity market internal strength based on six key metrics.
    **Signal:** Buy SPY when 4+ components are green (Positive) • Move to cash when 4+ are red (Negative)
    """)
    
    with st.spinner("⏳ Loading market health data..."):
        track_api_call()  # Track API calls for Asbury 6
        asbury_data = get_asbury_6_signals()
        track_api_call()  # Track historical data
        historical_data = get_asbury_6_historical(days=90)
    
    if 'error' in asbury_data and asbury_data['signal'] == 'ERROR':
        st.error(f"⚠️ Error fetching Asbury 6 data: {asbury_data['error']}")
    else:
        # Overall Signal and Gauge
        signal = asbury_data['signal']
        pos_count = asbury_data['positive_count']
        neg_count = asbury_data['negative_count']
        
        # Create top section with Gauge, Signal, and VIX Term Structure
        top_col1, top_col2 = st.columns([1, 1])
        
        with top_col1:
            # Merged Gauge and Signal
            gauge_col, signal_col = st.columns([1, 1.5])
            
            with gauge_col:
                gauge_value = pos_count  # 0-6 scale
                gauge_color = 'green' if signal == 'BUY' else ('red' if signal == 'CASH' else 'yellow')
                
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=gauge_value,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "A6 Score", 'font': {'size': 14, 'color': 'white'}},
                    number={'font': {'size': 30, 'color': 'white'}},
                    gauge={
                        'axis': {'range': [None, 6], 'tickwidth': 1, 'tickcolor': "white"},
                        'bar': {'color': gauge_color},
                        'bgcolor': "rgba(0,0,0,0)",
                        'borderwidth': 2,
                        'bordercolor': "white",
                        'steps': [
                            {'range': [0, 3], 'color': 'rgba(255,0,0,0.3)'},
                            {'range': [3, 4], 'color': 'rgba(255,255,0,0.3)'},
                            {'range': [4, 6], 'color': 'rgba(0,255,0,0.3)'}
                        ],
                        'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': 4}
                    }
                ))
                fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                                      font={'color': "white"}, height=160, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_gauge, width="stretch")
            
            with signal_col:
                if signal == 'BUY':
                    st.success("### 🟢 BUY SIGNAL")
                    st.markdown(f"**{pos_count}/6 Positive**")
                    st.markdown("Recomm: **Increase Equity**")
                elif signal == 'CASH':
                    st.error("### 🔴 CASH SIGNAL")
                    st.markdown(f"**{neg_count}/6 Negative**")
                    st.markdown("Recomm: **Move to Cash**")
                else:
                    st.warning("### 🟡 NEUTRAL")
                    st.markdown(f"**{pos_count} Pos / {neg_count} Neg**")
                    st.markdown("Recomm: **Hold/Wait**")
                
                st.caption(f"Updated: {asbury_data['timestamp']}")

        with top_col2:
            # Inline VIX Term Structure
            try:
                import yfinance as yf
                vix_spot = yf.download('^VIX', period='1d', progress=False)['Close'].iloc[-1]
                if hasattr(vix_spot, "item"): vix_spot = vix_spot.item()
                
                vix3m = yf.download('^VIX3M', period='1d', progress=False)['Close'].iloc[-1]
                if hasattr(vix3m, "item"): vix3m = vix3m.item()
                
                spread = float(vix3m) - float(vix_spot)
                
                structure_color = "#1a4d2e" if spread > 0 else "#4d1a1a"
                structure_text = "Contango (Bullish)" if spread > 0 else "Backwardation (Bearish)"
                
                st.markdown(f"""
                <div style='background-color: {structure_color}; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #4b5563;'>
                    <h5 style='color: #e5e7eb; margin: 0;'>VIX Term Structure</h5>
                    <div style='display: flex; justify-content: space-around; margin-top: 5px;'>
                        <div><span style='color:#9ca3af; font-size:0.8em'>Spot</span><br><b>{float(vix_spot):.2f}</b></div>
                        <div><span style='color:#9ca3af; font-size:0.8em'>3M Future</span><br><b>{float(vix3m):.2f}</b></div>
                        <div><span style='color:#9ca3af; font-size:0.8em'>Spread</span><br><b>{spread:+.2f}</b></div>
                    </div>
                    <p style='margin: 5px 0 0 0; font-weight: bold; color: white;'>{structure_text}</p>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                logger.info(f"Error rendering VIX term structure: {e}")
                st.caption("VIX data unavailable")
        
        st.divider()
        
        # Historical Chart with SPX
        if not historical_data.empty:
            st.subheader("📈 A6 Signal History vs SPX Performance")
            
            # Normalize SPY price for comparison (set first value to 100)
            historical_data['SPY_Normalized'] = (historical_data['SPY_Close'] / historical_data['SPY_Close'].iloc[0]) * 100
            
            # Create subplot with two y-axes
            fig_history = make_subplots(
                rows=2, cols=1,
                row_heights=[0.7, 0.3],
                subplot_titles=("SPX Price (Normalized to 100)", "A6 Signal Count"),
                vertical_spacing=0.1
            )
            
            # SPY price line
            fig_history.add_trace(
                go.Scatter(
                    x=historical_data['Date'],
                    y=historical_data['SPY_Normalized'],
                    name='SPX',
                    line=dict(color='cyan', width=2),
                    hovertemplate='Date: %{x}<br>SPX: %{y:.1f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Add background shading for BUY/CASH signals
            for i in range(len(historical_data)-1):
                row = historical_data.iloc[i]
                next_row = historical_data.iloc[i+1]
                
                if row['Signal'] == 'BUY':
                    color = 'rgba(0,255,0,0.1)'
                elif row['Signal'] == 'CASH':
                    color = 'rgba(255,0,0,0.1)'
                else:
                    color = 'rgba(255,255,0,0.05)'
                
                fig_history.add_vrect(
                    x0=row['Date'], x1=next_row['Date'],
                    fillcolor=color, layer="below", line_width=0,
                    row=1, col=1
                )
            
            # A6 positive count area chart
            fig_history.add_trace(
                go.Scatter(
                    x=historical_data['Date'],
                    y=historical_data['Positive_Count'],
                    name='Positive Signals',
                    fill='tozeroy',
                    line=dict(color='lime', width=1),
                    hovertemplate='Date: %{x}<br>Positive: %{y}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Add reference line at 4 (signal threshold)
            fig_history.add_hline(y=4, line_dash="dash", line_color="white", opacity=0.5, row=2, col=1)
            
            fig_history.update_xaxes(title_text="Date", row=2, col=1)
            fig_history.update_yaxes(title_text="Normalized Price", row=1, col=1)
            fig_history.update_yaxes(title_text="Count", range=[0, 6], row=2, col=1)
            
            fig_history.update_layout(
                template="plotly_dark",
                height=300,  # Reduced height
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig_history, width="stretch")
        
        st.divider()
        
        # Metric Cards in 3x2 Grid with better styling
        st.subheader("Six Market Health Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        for idx, metric in enumerate(asbury_data['metrics']):
            # Distribute metrics across columns
            if idx % 3 == 0:
                col = col1
            elif idx % 3 == 1:
                col = col2
            else:
                col = col3
            
            with col:
                status_color = "🟢" if metric['status'] == 'Positive' else "🔴"
                status_bg = "#1a4d2e" if metric['status'] == 'Positive' else "#4d1a1a"
                
                # Styled container with better contrast
                # Compact Styled Container
                st.markdown(f"""
                <div style='background-color: {status_bg}; padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid {"#4ade80" if metric["status"] == "Positive" else "#ef4444"}'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <h5 style='margin: 0; color: white; font-size: 0.95em;'>{status_color} {metric['name']}</h5>
                        <span style='font-size: 0.8em; color: #e5e7eb; font-weight: bold;'>{metric['status']}</span>
                    </div>
                    <p style='margin: 2px 0; color: #d1d5db; font-size: 0.8em;'>{metric['value']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()

