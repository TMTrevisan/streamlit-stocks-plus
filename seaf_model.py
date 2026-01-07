"""
SEAF Model (Sector ETF Asset Flows)

A quantitative sector rotation model that ranks the 11 Select Sector SPDR ETFs
based on asset flows across four timeframes to identify long/overweight opportunities.

The model "follows the money" by analyzing capital flows into and out of each sector.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_sector_data(ticker, start_date, end_date):
    """Cached data fetching for sector ETFs."""
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


# 11 Select Sector SPDR ETFs
SECTOR_ETFS = {
    'XLK': 'Technology',
    'XLF': 'Financials',
    'XLV': 'Health Care',
    'XLE': 'Energy',
    'XLY': 'Consumer Discretionary',
    'XLP': 'Consumer Staples',
    'XLI': 'Industrials',
    'XLB': 'Materials',
    'XLRE': 'Real Estate',
    'XLU': 'Utilities',
    'XLC': 'Communication Services'
}

# Timeframe definitions (in trading days)
TIMEFRAMES = {
    'Trading': 20,      # ~1 month
    'Tactical': 60,     # ~3 months
    'Strategic': 120,   # ~6 months
    'Long-term': 252    # ~1 year
}


def calculate_asset_flow_score(sector_data, spy_data, period):
    """
    Calculate composite asset flow score for a sector over a given period.
    
    Combines:
    1. Volume-weighted price momentum (captures actual money flow)
    2. Relative strength vs SPY (performance comparison)
    
    Higher score = stronger inflows
    
    Args:
        sector_data: DataFrame with sector ETF historical data
        spy_data: DataFrame with SPY historical data (benchmark)
        period: Number of days to analyze
        
    Returns:
        float: Composite asset flow score
    """
    try:
        # Ensure we have enough data
        if len(sector_data) < period or len(spy_data) < period:
            return 0
        
        # Get recent data
        recent_sector = sector_data.iloc[-period:]
        recent_spy = spy_data.iloc[-period:]
        
        # 1. Volume-weighted price momentum
        # Calculate daily returns weighted by volume
        price_change = recent_sector['Close'].pct_change()
        volume_norm = recent_sector['Volume'] / recent_sector['Volume'].mean()
        vwpm = (price_change * volume_norm).sum()
        
        # 2. Relative strength vs SPY
        sector_return = (recent_sector['Close'].iloc[-1] / recent_sector['Close'].iloc[0] - 1)
        spy_return = (recent_spy['Close'].iloc[-1] / recent_spy['Close'].iloc[0] - 1)
        relative_strength = sector_return - spy_return
        
        # Composite score (equal weight to both components)
        composite_score = (vwpm * 0.5) + (relative_strength * 0.5)
        
        return composite_score
    
    except Exception as e:
        return 0


def rank_sectors_by_flow(sector_scores):
    """
    Rank sectors based on asset flow scores.
    
    Args:
        sector_scores: dict of {ticker: score}
        
    Returns:
        dict of {ticker: rank} where 1 = highest flows, 11 = lowest flows
    """
    # Sort by score descending (highest flows first)
    sorted_sectors = sorted(sector_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Assign ranks
    ranks = {}
    for rank, (ticker, score) in enumerate(sorted_sectors, start=1):
        ranks[ticker] = rank
    
    return ranks


def get_seaf_model():
    """
    Calculate the complete SEAF Model with rankings across all timeframes.
    
    Returns:
        DataFrame with columns: Ticker, Sector, Trading, Tactical, Strategic, 
        Long-term, Total_Score, Category, and flow scores for each timeframe
    """
    try:
        # Fetch data for all sectors plus SPY benchmark
        end_date = datetime.now()
        start_date = end_date - timedelta(days=400)  # Extra buffer for 1-year calculation
        
        # Convert dates to strings for cache key
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        sector_data = {}
        
        # Download all sector ETFs using cached function
        for ticker in SECTOR_ETFS.keys():
            sector_data[ticker] = fetch_sector_data(ticker, start_str, end_str)
        
        # Download SPY benchmark
        spy_data = fetch_sector_data('SPY', start_str, end_str)
        
        # Calculate asset flow scores and ranks for each timeframe
        results = []
        
        for ticker, sector_name in SECTOR_ETFS.items():
            row = {
                'Ticker': ticker,
                'Sector': sector_name
            }
            
            # Calculate scores for each timeframe
            for tf_name, tf_days in TIMEFRAMES.items():
                score = calculate_asset_flow_score(
                    sector_data[ticker], 
                    spy_data, 
                    tf_days
                )
                row[f'{tf_name}_Score'] = score
            
            results.append(row)
        
        df = pd.DataFrame(results)
        
        # Rank sectors for each timeframe
        for tf_name in TIMEFRAMES.keys():
            scores = dict(zip(df['Ticker'], df[f'{tf_name}_Score']))
            ranks = rank_sectors_by_flow(scores)
            df[tf_name] = df['Ticker'].map(ranks)
        
        # Calculate total score (sum of all ranks)
        # Lower score = better (more inflows across timeframes)
        rank_columns = list(TIMEFRAMES.keys())
        df['Total_Score'] = df[rank_columns].sum(axis=1)
        
        # Categorize based on total score
        # With 4 timeframes: range is 4-44
        # Favored: 4-20, Neutral: 21-32, Avoid: 33-44
        df['Category'] = df['Total_Score'].apply(lambda x: 
            'Favored' if x <= 20 else ('Neutral' if x <= 32 else 'Avoid')
        )
        
        # Sort by total score (best first)
        df = df.sort_values('Total_Score').reset_index(drop=True)
        
        # Add overall rank
        df['Rank'] = range(1, len(df) + 1)
        
        return df
    
    except Exception as e:
        print(f"Error in SEAF calculation: {e}")
        return pd.DataFrame()


def get_top_3_sectors(seaf_df):
    """
    Get the top 3 sectors for allocation based on SEAF rankings.
    
    Args:
        seaf_df: DataFrame from get_seaf_model()
        
    Returns:
        DataFrame with top 3 sectors
    """
    return seaf_df.head(3)


if __name__ == '__main__':
    # Test the module
    print("\nSEAF Model - Sector ETF Asset Flows")
    print("=" * 60)
    
    seaf_results = get_seaf_model()
    
    if not seaf_results.empty:
        print("\n📊 SEAF Rankings (Top to Bottom by Total Score):\n")
        
        # Display table
        display_cols = ['Rank', 'Ticker', 'Sector', 'Trading', 'Tactical', 
                       'Strategic', 'Long-term', 'Total_Score', 'Category']
        print(seaf_results[display_cols].to_string(index=False))
        
        print("\n" + "=" * 60)
        print("\n🎯 TOP 3 SECTORS FOR ALLOCATION:\n")
        
        top_3 = get_top_3_sectors(seaf_results)
        for idx, row in top_3.iterrows():
            print(f"{row['Rank']}. {row['Ticker']} - {row['Sector']}")
            print(f"   Total Score: {row['Total_Score']} ({row['Category']})")
            print()
    else:
        print("Error: Could not calculate SEAF rankings")
