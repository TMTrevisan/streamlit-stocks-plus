import streamlit as st
import plotly.graph_objects as go
from gamma_profile import get_gamma_profile
from options_flow import get_volatility_analysis, get_daily_flow_snapshot, analyze_flow_sentiment
from services.data_fetcher import fetch_stock_history

def render_options_intelligence(ticker, track_api_call):
    st.title("🌪️ Options Flow & Gamma Profile")
    
    if ticker:
         # --- ΓAMMA & VOLUME PROFILE ---
        st.subheader(f"📊 Gamma Profile: {ticker}")
        
        with st.spinner(f"Fetching options data for {ticker}..."):
            track_api_call()  # Track options chain fetch
            gamma_data = get_gamma_profile(ticker)
        
        if 'error' in gamma_data:
            st.warning(f"⚠️ {gamma_data['error']}")
            st.caption("Note: Gamma profile requires active options trading on the ticker")
        else:
            # Key metrics
            stats = gamma_data['stats']
            spot = gamma_data['spot']
            
            # Metrics row with better visibility
            st.markdown("### Options Metrics")
            gm1, gm2, gm3, gm4 = st.columns(4)
            
            # Custom styled metrics for better visibility
            net_gex_val = stats['net_gex'] / 1e6
            gex_color_bg = "#1a4d2e" if net_gex_val > 0 else "#4d1a1a"
            gex_emoji = "🟢" if net_gex_val > 0 else "🔴"
            
            gm1.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Spot Price</p>
                <h2 style='color: white; margin: 5px 0;'>${spot:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            gm2.markdown(f"""
            <div style='background-color: {gex_color_bg}; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Net GEX</p>
                <h2 style='color: white; margin: 5px 0;'>{gex_emoji} ${net_gex_val:.1f}M</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Fix max GEX strike display
            max_gex_display = f"${stats['max_gex_strike']:.2f}" if stats['max_gex_strike'] is not None else "N/A"
            
            gm3.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Max GEX Strike</p>
                <h2 style='color: white; margin: 5px 0;'>{max_gex_display}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            put_call_ratio = stats['total_put_volume'] / max(stats['total_call_volume'], 1)
            gm4.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Put/Call Vol</p>
                <h2 style='color: white; margin: 5px 0;'>{put_call_ratio:.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"Last updated: {gamma_data['timestamp']}")
            
            st.divider()
            
            # Enhanced interpretation with analysis
            if net_gex_val > 0:
                st.info("""📌 **Positive Net GEX**: Dealers are long gamma → **Stabilizing Environment**
                
**What this means:**
- Market makers will buy dips and sell rallies to maintain delta-neutral hedges
- Price tends to revert toward high-GEX strikes (acts as magnet)
- Lower volatility expected as hedging dampens price swings
- Breakouts require stronger momentum to overcome dealer resistance""")
            else:
                st.warning("""📌 **Negative Net GEX**: Dealers are short gamma → **Volatizing Environment**
                
**What this means:**
- Market makers will sell dips and buy rallies (amplifying moves)
- Price can accelerate through strikes with negative GEX
- Higher volatility expected as hedging exacerbates price swings  
- Trends can develop more easily without dealer resistance""")
            
            # Additional analysis
            st.markdown("""**Key Observations:**""")
            analysis_points = []
            
            if stats['max_gex_strike']:
                distance_to_max = ((stats['max_gex_strike'] - spot) / spot) * 100
                analysis_points.append(f"• Max GEX at ${stats['max_gex_strike']:.2f} ({distance_to_max:+.1f}% from spot) - this level acts as a price magnet")
            
            if put_call_ratio > 1.5:
                analysis_points.append(f"• High put/call ratio ({put_call_ratio:.2f}) suggests defensive positioning or bearish sentiment")
            
            for point in analysis_points:
                st.markdown(point)
                
            # Charts
            col_gamma, col_vol = st.columns(2)
            
            with col_gamma:
                st.subheader("Gamma Exposure by Strike")
                gex = gamma_data['gex']
                fig_gamma = go.Figure()
                fig_gamma.add_trace(go.Bar(
                    x=gex.index,
                    y=gex.values / 1e6,
                    name='Total Gamma',
                    marker_color=['#4ade80' if val > 0 else '#ef4444' for val in gex.values]
                ))
                fig_gamma.update_layout(template="plotly_dark", height=400)
                # Update axis titles
                fig_gamma.update_layout(showlegend=False)
                fig_gamma.update_yaxes(title_text="Gamma ($M)")
                fig_gamma.update_xaxes(title_text="Strike Price ($)")
                
                # Add spot line
                fig_gamma.add_vline(x=spot, line_dash="dash", line_color="white", annotation_text="Spot")
                
                st.plotly_chart(fig_gamma, width="stretch")
            
            with col_vol:
                st.subheader("Volume Profile")
                vol = gamma_data['volume']
                fig_vol = go.Figure()
                if 'call' in vol.columns:
                    fig_vol.add_trace(go.Bar(
                        x=vol.index,
                        y=vol['call'],
                        name='Call Vol',
                        marker_color='#4ade80'
                    ))
                if 'put' in vol.columns:
                    fig_vol.add_trace(go.Bar(
                        x=vol.index,
                        y=vol['put'],
                        name='Put Vol',
                        marker_color='#ef4444'
                    ))
                fig_vol.update_layout(template="plotly_dark", height=400, barmode='stack')
                fig_vol.update_yaxes(title_text="Volume")
                fig_vol.update_xaxes(title_text="Strike Price ($)")
                fig_vol.add_vline(x=spot, line_dash="dash", line_color="white", annotation_text="Spot")
                
                st.plotly_chart(fig_vol, width="stretch")

        
        # --- OPTIONS FLOW ANALYSIS ---
        st.divider()
        st.subheader(f"🌊 Options Flow Analysis: {ticker}")
        
        # --- VOLATILITY ANALYSIS ---
        data = fetch_stock_history(ticker)
            
        vol_metrics = get_volatility_analysis(ticker, data)
        
        if vol_metrics and 'hv_20' in vol_metrics:
            st.markdown("### 🛡️ Options Strategy Intelligence")
            
            v_col1, v_col2, v_col3, v_col4 = st.columns(4)
            
            iv = vol_metrics.get('iv_current')
            hv20 = vol_metrics.get('hv_20')
            hv252 = vol_metrics.get('hv_252')
            
            v_col1.metric("Implied Volatility (IV)", f"{iv:.1f}%" if iv else "N/A", 
                         help="Current IV derived from option chain." if iv else "No options data")
            v_col2.metric("Hist. Volatility (20D)", f"{hv20:.1f}%", help="Realized volatility over past 20 days.")
            v_col3.metric("Hist. Volatility (1Y)", f"{hv252:.1f}%", help="Realized volatility over past year.")
            
            rank_text = "N/A"
            if iv and hv252:
                 diff = iv - hv252
                 rank_text = "High Prem" if diff > 0 else "Low Prem"
                 
            v_col4.metric("IV vs HV", rank_text, delta=f"{iv-hv252:.1f}%" if iv and hv252 else None)
            
            # Earnings & Dividends
            with st.expander("📅 Event Risk & Income"):
                e_col1, e_col2 = st.columns(2)
                e_col1.write(f"**Earnings:** {vol_metrics.get('earnings_date', 'N/A')}")
                e_col2.write(f"**Ex-Dividend:** {vol_metrics.get('ex_div_date', 'N/A')} ({vol_metrics.get('div_rate', 0)}/yr)")
                
                st.info("💡 **Strategy Tip**: Selling Puts is favorable when IV > HV and price is near technical support (e.g. Asbury 6 Positive). Selling Calls is risky near Earnings.")

        st.divider()
        
        with st.spinner("Fetching daily flow data..."):
            flow_data = get_daily_flow_snapshot(ticker)
        
        if not flow_data:
            st.warning("No flow data available.")
        elif 'error' in flow_data:
            st.warning(f"Could not retrieve options flow: {flow_data.get('error')}")
        else:
            # Metrics
            f1, f2, f3 = st.columns(3)
            
            # Net Premium Color
            net_prem = flow_data['net_premium']
            prem_color = "#1a4d2e" if net_prem > 0 else "#4d1a1a"
            prem_emoji = "🐂" if net_prem > 0 else "🐻"
            
            f1.markdown(f"""
            <div style='background-color: {prem_color}; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Net Premium</p>
                <h2 style='color: white; margin: 5px 0;'>{prem_emoji} ${net_prem:,.0f}</h2>
                <p style='color: #d1d5db; font-size: 0.8em; margin: 0;'>Diff: Call $ - Put $</p>
            </div>
            """, unsafe_allow_html=True)
            
            f2.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>P/C Premium Ratio</p>
                <h2 style='color: white; margin: 5px 0;'>{flow_data['pc_premium_ratio']:.2f}</h2>
                <p style='color: #d1d5db; font-size: 0.8em; margin: 0;'>Bearish > 1.0</p>
            </div>
            """, unsafe_allow_html=True)
            
            f3.markdown(f"""
            <div style='background-color: #1e3a5f; padding: 15px; border-radius: 8px; text-align: center;'>
                <p style='color: #94a3b8; margin: 0; font-size: 0.9em;'>Unusual Contracts</p>
                <h2 style='color: white; margin: 5px 0;'>{len(flow_data['unusual_calls']) + len(flow_data['unusual_puts'])}</h2>
                <p style='color: #d1d5db; font-size: 0.8em; margin: 0;'>Vol > 2x OI</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Sentiment Logic
            sentiment = analyze_flow_sentiment(flow_data)
            if 'error' in sentiment:
                st.info(f"**Flow Sentiment Error:** {sentiment['error']}")
            else:
                st.info(f"**Flow Sentiment: {sentiment.get('sentiment', 'UNKNOWN')}**\n\n"
                        f"_{sentiment.get('description', '')}_\n\n"
                        f"**Bias:** {sentiment.get('volume_bias', '')} Volume, {sentiment.get('premium_bias', '')} Premium")
            
            st.markdown("---")
            
            # Unusual Activity
            st.markdown("### 🔥 Unusual Activity (Vol > 2x OI)")
            tab_calls, tab_puts = st.tabs(["Unusual Calls", "Unusual Puts"])
            
            with tab_calls:
                if not flow_data['unusual_calls'].empty:
                    unusual_calls_display = flow_data['unusual_calls'][['strike', 'expiration', 'volume', 'openInterest', 'premium']].copy()
                    unusual_calls_display['premium'] = unusual_calls_display['premium'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(unusual_calls_display, width="stretch", hide_index=True)
                else:
                    st.caption("None detected")
            
            with tab_puts:
                if not flow_data['unusual_puts'].empty:
                    unusual_puts_display = flow_data['unusual_puts'][['strike', 'expiration', 'volume', 'openInterest', 'premium']].copy()
                    unusual_puts_display['premium'] = unusual_puts_display['premium'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(unusual_puts_display, width="stretch", hide_index=True)
                else:
                    st.caption("None detected")
            
            # Top Contracts
            with st.expander("View Top Contracts by Premium"):
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("Top Calls")
                    if not flow_data['top_calls'].empty:
                        top_calls_display = flow_data['top_calls'].copy()
                        top_calls_display['premium'] = top_calls_display['premium'].apply(lambda x: f"${x:,.0f}")
                        st.dataframe(top_calls_display, width="stretch", hide_index=True)
                    else:
                        st.caption("No data")
                
                with c2:
                    st.subheader("Top Puts")
                    if not flow_data['top_puts'].empty:
                        top_puts_display = flow_data['top_puts'].copy()
                        top_puts_display['premium'] = top_puts_display['premium'].apply(lambda x: f"${x:,.0f}")
                        st.dataframe(top_puts_display, width="stretch", hide_index=True)
                    else:
                        st.caption("No data")
                
            st.caption("""
            **Educational Note:** 
            - **Net Premium**: The total premium spent on Calls minus Puts. Positive = Bullish flow.
            - **Unusual Activity**: Contracts where today's volume is significantly higher than existing Open Interest, suggesting fresh positioning.
            - *Note: This is retail-access data (delayed/aggregated) and not comparable to institutional feeds like Bloomberg.*
            """)
    else:
        st.info("Enter a ticker in the sidebar to view options intelligence.")
