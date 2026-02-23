import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

from seaf_model import get_seaf_model, get_top_3_sectors, fetch_sector_data, SECTOR_ETFS

def render_sector_rotation(track_api_call):
    st.title("📈 SEAF Sector Rotation Model")
    st.markdown("""
    **SEAF (Sector ETF Asset Flows)** - A quantitative sector rotation model that ranks the 11 Select Sector SPDR ETFs 
    by "following the money" across four timeframes. Always fully invested in the top 3 ranked sectors.
    """)
    
    with st.spinner("🔄 Loading sector rankings..."):
        track_api_call()  # Track SEAF API call
        seaf_data = get_seaf_model()
    
    if seaf_data.empty:
        st.error("⚠️ Error calculating SEAF rankings")
    else:
        # Top 3 Allocation Banner
        top_3 = get_top_3_sectors(seaf_data)
        
        st.subheader("🎯 Current Top 3 Allocation")
        
        top_col1, top_col2, top_col3 = st.columns(3)
        
        for idx, (col, (_, row)) in enumerate(zip([top_col1, top_col2, top_col3], top_3.iterrows())):
            with col:
                category_color = "#1a4d2e" if row['Category'] == 'Favored' else ("#4d4d1a" if row['Category'] == 'Neutral' else "#4d1a1a")
                st.markdown(f"""
                <div style='background-color: {category_color}; padding: 20px; border-radius: 10px; text-align: center; border: 3px solid #4ade80;'>
                    <h2 style='margin: 0; color: white;'>#{row['Rank']} {row['Ticker']}</h2>
                    <h4 style='margin: 5px 0; color: #e5e7eb;'>{row['Sector']}</h4>
                    <p style='margin: 5px 0; color: #d1d5db; font-size: 0.9em;'>Score: {row['Total_Score']}</p>
                    <p style='margin: 0; color: #4ade80; font-weight: bold;'>{row['Category']}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.caption("Equal allocation across these 3 sectors")
        
        # --- TOP 3 SECTOR CHARTS ---
        st.divider()
        st.subheader("Price Performance - Top 3 Sectors")
        
        chart_col1, chart_col2, chart_col3 = st.columns(3)
        
        # Fetch price data for top 3 sectors
        end_str = datetime.now().strftime('%Y-%m-%d')
        start_str = (datetime.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
        
        for col, (_, row) in zip([chart_col1, chart_col2, chart_col3], top_3.iterrows()):
            with col:
                sector_ticker = row['Ticker']
                sector_data = fetch_sector_data(sector_ticker, start_str, end_str)
                
                if not sector_data.empty:
                    # Calculate return
                    first_close = sector_data['Close'].iloc[0]
                    last_close = sector_data['Close'].iloc[-1]
                    pct_return = ((last_close - first_close) / first_close) * 100
                    
                    # Create mini chart
                    fig_mini = go.Figure()
                    fig_mini.add_trace(go.Scatter(
                        x=sector_data.index,
                        y=sector_data['Close'],
                        mode='lines',
                        fill='tozeroy',
                        fillcolor='rgba(74, 222, 128, 0.2)' if pct_return > 0 else 'rgba(239, 68, 68, 0.2)',
                        line=dict(color='#4ade80' if pct_return > 0 else '#ef4444', width=2),
                        hovertemplate='%{x}<br>$%{y:.2f}<extra></extra>'
                    ))
                    
                    fig_mini.update_layout(
                        template='plotly_dark',
                        height=200,
                        margin=dict(l=0, r=0, t=30, b=0),
                        title=dict(
                            text=f"{sector_ticker}: {pct_return:+.1f}%",
                            font=dict(size=14, color='#4ade80' if pct_return > 0 else '#ef4444')
                        ),
                        xaxis=dict(showticklabels=False, showgrid=False),
                        yaxis=dict(showticklabels=True, showgrid=False),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_mini, width="stretch")
                else:
                    st.caption(f"{sector_ticker}: No data")
        
        st.caption("90-day price performance")
        st.divider()
        
        # Rankings Table
        st.subheader("📊 Complete Sector Rankings")
        
        # Prepare display dataframe
        display_df = seaf_data[['Rank', 'Ticker', 'Sector', 'Trading', 'Tactical', 
                                 'Strategic', 'Long-term', 'Total_Score', 'Category']].copy()
        
        # Style the dataframe
        def color_category(val):
            if val == 'Favored':
                return 'background-color: #1a4d2e; color: white'
            elif val == 'Neutral':
                return 'background-color: #4d4d1a; color: white'
            else:
                return 'background-color: #4d1a1a; color: white'
        
        styled_df = display_df.style.map(color_category, subset=['Category'])
        
        # Rankings Table (Compacted into Expander)
        with st.expander("📊 View Complete Sector Rankings Table", expanded=False):
            st.dataframe(styled_df, width="stretch", hide_index=True)
            
            st.caption("""
            **How to Read Rankings:**
            - Lower rank numbers (1-3) = strongest asset inflows → Allocate here
            - Each timeframe ranks sectors 1-11 based on asset flows
            - Total Score = sum of all timeframe ranks (lower is better)
            - **Favored** (score ≤20) • **Neutral** (21-32) • **Avoid** (≥33)
            """)
        
        st.divider()
        
        # Scores Visualization
        st.subheader("📈 SEAF Scores Chart")
        
        # Create bar chart
        fig_seaf = go.Figure()
        
        # Color bars by category
        colors = seaf_data['Category'].map({
            'Favored': '#4ade80',
            'Neutral': '#fbbf24',
            'Avoid': '#ef4444'
        })
        
        fig_seaf.add_trace(go.Bar(
            x=seaf_data['Ticker'],
            y=seaf_data['Total_Score'],
            marker_color=colors,
            text=seaf_data['Total_Score'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Score: %{y}<br>%{customdata}<extra></extra>',
            customdata=seaf_data['Sector']
        ))
        
        # Add reference lines
        fig_seaf.add_hline(y=20, line_dash="dash", line_color="green", 
                          annotation_text="Favored Threshold", opacity=0.5)
        fig_seaf.add_hline(y=32, line_dash="dash", line_color="yellow", 
                          annotation_text="Neutral Threshold", opacity=0.5)
        
        fig_seaf.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_title="Sector ETF",
            yaxis_title="Total Score (Lower = Better)",
            yaxis=dict(autorange="reversed"),  # Reverse so lower scores are at top
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0)
        )
        
        st.plotly_chart(fig_seaf, width="stretch")
        
        # Timeframe breakdown with color coding
        with st.expander("📋 View Timeframe Breakdown"):
            st.markdown("**Individual timeframe rankings and asset flow scores:**")
            
            breakdown_df = seaf_data[['Ticker', 'Sector', 
                                     'Trading', 'Trading_Score',
                                     'Tactical', 'Tactical_Score', 
                                     'Strategic', 'Strategic_Score',
                                     'Long-term', 'Long-term_Score']].copy()
            
            # Color code function for rankings (1-3 green, 4-8 yellow, 9-11 red)
            def color_rank(val):
                if isinstance(val, (int, float)):
                    if val <= 3:
                        return 'background-color: #1a4d2e; color: white'
                    elif val <= 8:
                        return 'background-color: #4d4d1a; color: white'
                    else:
                        return 'background-color: #4d1a1a; color: white'
                return ''
            
            # Color code function for scores (positive green, negative red)
            def color_score(val):
                if isinstance(val, (int, float)):
                    if val > 0:
                        return 'background-color: #1a4d2e; color: white'
                    else:
                        return 'background-color: #4d1a1a; color: white'
                return ''
            
            # Apply styling
            styled_breakdown = breakdown_df.style.map(
                color_rank, 
                subset=['Trading', 'Tactical', 'Strategic', 'Long-term']
            ).map(
                color_score,
                subset=['Trading_Score', 'Tactical_Score', 'Strategic_Score', 'Long-term_Score']
            )
            
            st.dataframe(styled_breakdown, width="stretch", hide_index=True)
            
            st.caption("""
            **Timeframes:**
            - **Trading**: 20 days (~1 month)
            - **Tactical**: 60 days (~3 months)
            - **Strategic**: 120 days (~6 months)
            - **Long-term**: 252 days (~1 year)
            """)
    
    st.divider()
    
    # --- SECTOR CORRELATION HEATMAP ---
    with st.expander("View Sector Correlation Matrix"):
        st.markdown("**60-day correlation between sector ETFs:**")
        
        try:
            # Fetch 60-day data for all sectors
            end_str = datetime.now().strftime('%Y-%m-%d')
            start_str = (datetime.now() - pd.Timedelta(days=90)).strftime('%Y-%m-%d')
            
            sector_closes = {}
            for sector_ticker_key in SECTOR_ETFS.keys():
                data = fetch_sector_data(sector_ticker_key, start_str, end_str)
                if not data.empty:
                    sector_closes[sector_ticker_key] = data['Close'].iloc[-60:]
            
            if sector_closes:
                close_df = pd.DataFrame(sector_closes)
                corr_matrix = close_df.pct_change().dropna().corr()
                
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.index,
                    colorscale='RdYlGn',
                    zmin=-1, zmax=1,
                    text=np.round(corr_matrix.values, 2),
                    texttemplate='%{text}',
                    textfont={"size": 10},
                    hovertemplate='%{x} vs %{y}: %{z:.2f}<extra></extra>'
                ))
                
                fig_corr.update_layout(
                    template='plotly_dark',
                    height=400,
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig_corr, width="stretch")
                
                st.caption("""
                **How to interpret:**
                - **Green (close to 1)**: Sectors move together
                - **Red (close to -1)**: Sectors move opposite
                - **Diversification tip**: Pair sectors with lower correlation
                """)
        except Exception as e:
            st.caption(f"Correlation matrix unavailable: {e}")
    
    st.markdown("---")
