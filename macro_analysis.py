"""
Macro & Intermarket Analysis Module
Analyzes yields, commodities, and currencies to determine broader market context.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import streamlit as st

# Macro Tickers
MACRO_TICKERS = {
    '10Y Yield': '^TNX',
    '5Y Yield': '^FVX',
    '3M Yield': '^IRX',
    'Dollar Index': 'DX-Y.NYB',
    'Gold': 'GC=F',
    'Oil': 'CL=F',
    'Bitcoin': 'BTC-USD',
    'SP500': '^GSPC'
}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_macro_data(period="1y"):
    """Fetch historical data for all macro indicators."""
    try:
        tickers = list(MACRO_TICKERS.values())
        data = yf.download(tickers, period=period, progress=False)
        
        # Flatten MultiIndex if present
        if isinstance(data.columns, pd.MultiIndex):
            # We need to handle this carefully to keep ticker association
            # The structure is usually [Price][Ticker] e.g. ['Close']['^TNX']
            pass # yfinance structure is fine, we'll access via data['Close'][ticker]
            
        return data
    except Exception as e:
        print(f"Error fetching macro data: {e}")
        return pd.DataFrame()


def get_yield_curve_data(data):
    """Extract and calculate yield curve metrics."""
    if data.empty:
        return None
        
    try:
        closes = data['Close']
        
        # Calculate Spread (10Y - 3M)
        # Note: Yahoo data for TNX/FVX/IRX is usually in percentage points (e.g. 4.12)
        ten_year = closes[MACRO_TICKERS['10Y Yield']]
        three_month = closes[MACRO_TICKERS['3M Yield']]
        
        spread = ten_year - three_month
        
        df = pd.DataFrame({
            '10Y': ten_year,
            '3M': three_month,
            'Spread': spread
        })
        
        return df
    except KeyError as e:
        print(f"Missing yield data: {e}")
        return None


def get_asset_performance(data):
    """Calculate normalized performance for comparison."""
    if data.empty:
        return None
        
    try:
        closes = data['Close']
        
        assets = {
            'Stocks (SPX)': MACRO_TICKERS['SP500'],
            'Gold': MACRO_TICKERS['Gold'],
            'Oil': MACRO_TICKERS['Oil'],
            'Dollar (DXY)': MACRO_TICKERS['Dollar Index'],
            'Bitcoin': MACRO_TICKERS['Bitcoin']
        }
        
        perf_df = pd.DataFrame()
        
        for name, ticker in assets.items():
            if ticker in closes:
                # Normalize to 0% start
                series = closes[ticker]
                normalized = ((series / series.iloc[0]) - 1) * 100
                perf_df[name] = normalized
                
        return perf_df
    except Exception as e:
        print(f"Error calculating performance: {e}")
        return None


def render_yield_curve_chart(yield_df):
    """Create yield curve visualization."""
    if yield_df is None:
        return None
        
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.08, row_heights=[0.6, 0.4],
                        subplot_titles=("Treasury Yields", "10Y-3M Spread (Recession Indicator)"))
    
    # Yields
    fig.add_trace(go.Scatter(x=yield_df.index, y=yield_df['10Y'], name="10Y Yield", 
                            line=dict(color='#3b82f6', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=yield_df.index, y=yield_df['3M'], name="3M Yield", 
                            line=dict(color='#fbbf24', width=2)), row=1, col=1)
    
    # Spread (Bar Chart for cleaner positive/negative distinction)
    colors = ['#4ade80' if val >= 0 else '#ef4444' for val in yield_df['Spread']]
    
    fig.add_trace(go.Bar(
        x=yield_df.index, 
        y=yield_df['Spread'], 
        name="Spread",
        marker_color=colors,
        marker_line_width=0
    ), row=2, col=1)
    
    # Zero line for spread
    fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1, row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark", 
        height=500, 
        margin=dict(l=0, r=0, t=30, b=0),
        bargap=0.1
    )
    
    fig.update_yaxes(title_text="Yield (%)", row=1, col=1)
    fig.update_yaxes(title_text="Diff (bps)", row=2, col=1)
    
    return fig


def render_intermarket_chart(perf_df):
    """Create intermarket performance comparison chart."""
    if perf_df is None:
        return None
        
    fig = go.Figure()
    
    colors = {
        'Stocks (SPX)': '#3b82f6', # Blue
        'Gold': '#fbbf24',         # Yellow
        'Oil': '#ef4444',          # Red
        'Dollar (DXY)': '#94a3b8', # Grey
        'Bitcoin': '#f97316'       # Orange
    }
    
    for col in perf_df.columns:
        fig.add_trace(go.Scatter(
            x=perf_df.index, 
            y=perf_df[col], 
            name=col,
            line=dict(color=colors.get(col, 'white'))
        ))
        
    fig.update_layout(
        template="plotly_dark",
        height=450,
        title="Asset Class Performance (1 Year Normalized)",
        yaxis_title="% Return",
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0.5, xanchor="center")
    )
    
    return fig


if __name__ == '__main__':
    # Test module
    print("Testing Macro Analysis...")
    data = fetch_macro_data()
    print("Data Fetched:", data.shape)
    
    yields = get_yield_curve_data(data)
    if yields is not None:
        print("\nYield Curve Data:")
        print(yields.tail())
        
    perf = get_asset_performance(data)
    if perf is not None:
        print("\nPerformance Data:")
        print(perf.tail())
