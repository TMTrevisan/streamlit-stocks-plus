"""
Gamma & Volume Profile Tool - Streamlit Integration
Analyzes options chains to calculate Net Gamma Exposure (GEX) and volume profiles.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import streamlit as st
from services.logger import setup_logger
logger = setup_logger(__name__)


@st.cache_data(ttl=300)  # Cache for 5 minutes (options data changes frequently)
def get_cached_options_chain(symbol, max_expirations=10):
    """Cached wrapper for options chain fetching."""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        if not expirations:
            return None
        
        all_chains = []
        for exp_date in expirations[:max_expirations]:
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls.copy()
                calls['option_type'] = 'call'
                calls['expiration'] = exp_date
                puts = chain.puts.copy()
                puts['option_type'] = 'put'
                puts['expiration'] = exp_date
                all_chains.append(calls)
                all_chains.append(puts)
            except Exception:
                continue
        
        if not all_chains:
            return None
        
        df = pd.concat(all_chains, ignore_index=True)
        current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
        df['underlying_price'] = current_price if current_price else (df['bid'] + df['ask']) / 2
        return df
    except Exception:
        return None

def fetch_options_chain(symbol, max_expirations=10):
    """
    Fetches option chains using yfinance.
    Returns a DataFrame with all expirations combined.
    
    Args:
        symbol: Stock ticker symbol
        max_expirations: Maximum number of expiration dates to fetch
        
    Returns:
        DataFrame with all option contracts or None if error
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get all expiration dates
        expirations = ticker.options
        if not expirations:
            return None
        
        # Fetch chains and combine
        all_chains = []
        for exp_date in expirations[:max_expirations]:
            try:
                chain = ticker.option_chain(exp_date)
                
                # Process calls
                calls = chain.calls.copy()
                calls['option_type'] = 'call'
                calls['expiration'] = exp_date
                
                # Process puts
                puts = chain.puts.copy()
                puts['option_type'] = 'put'
                puts['expiration'] = exp_date
                
                all_chains.append(calls)
                all_chains.append(puts)
                
            except Exception:
                continue
        
        if not all_chains:
            return None
            
        # Combine all chains
        df = pd.concat(all_chains, ignore_index=True)
        
        # Get current price
        current_price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
        if current_price:
            df['underlying_price'] = current_price
        else:
            # Fallback to midpoint
            df['underlying_price'] = (df['bid'] + df['ask']) / 2
        
        return df
        
    except Exception as e:
        logger.info(f"Error fetching options data: {e}")
        return None


def approximate_gamma(df):
    """
    Approximate gamma using a simple heuristic when not available.
    Gamma is highest for ATM options and decreases as you move away.
    
    Args:
        df: DataFrame with strike and underlying_price columns
        
    Returns:
        Series with approximated gamma values
    """
    S = df['underlying_price']
    K = df['strike']
    
    # Moneyness (how far from ATM)
    moneyness = np.abs(K - S) / S
    
    # Gamma approximation: peaks at ATM, decays exponentially
    # Scale factor chosen for reasonable GEX values
    gamma = 0.01 * np.exp(-50 * moneyness**2)
    
    return gamma


def calculate_gamma_exposure(df):
    """
    Calculates Net Gamma Exposure (GEX) and Volume Profile by Strike.
    
    GEX Interpretation:
    - Positive GEX (Call-heavy): Dealers long gamma → stabilizing (buy dips, sell rips)
    - Negative GEX (Put-heavy): Dealers short gamma → volatizing (sell dips, buy rips)
    
    Args:
        df: DataFrame with options chain data
        
    Returns:
        Tuple of (gex_by_strike, volume_by_strike, spot_price, stats_dict)
    """
    # Map yfinance column names
    column_mapping = {
        'openInterest': 'open_interest',
        'impliedVolatility': 'implied_volatility'
    }
    df = df.rename(columns=column_mapping)
    
    # Check required columns
    required = ['strike', 'option_type', 'open_interest', 'volume', 'underlying_price']
    if not all(c in df.columns for c in required):
        return None
    
    # Add gamma if not present
    if 'gamma' not in df.columns:
        df['gamma'] = approximate_gamma(df)
    
    # Fill NAs
    df['gamma'] = df['gamma'].fillna(0)
    df['open_interest'] = df['open_interest'].fillna(0)
    df['volume'] = df['volume'].fillna(0)
    
    # Get spot price
    spot_price = df['underlying_price'].iloc[0]
    
    # Calculate GEX
    # GEX = Gamma * OI * 100 * Spot
    # Calls are positive (dealer long gamma), Puts are negative (dealer short gamma)
    df['gex'] = df['gamma'] * df['open_interest'] * 100 * spot_price
    
    # Apply sign based on option type
    df['signed_gex'] = df.apply(
        lambda x: x['gex'] if x['option_type'] == 'call' else -x['gex'], 
        axis=1
    )
    
    # Aggregate by strike
    gex_by_strike = df.groupby('strike')['signed_gex'].sum().sort_index()
    vol_by_strike = df.groupby(['strike', 'option_type'])['volume'].sum().unstack(fill_value=0).sort_index()
    
    # Filter for relevant range (+/- 20% of spot)
    lower_bound = spot_price * 0.8
    upper_bound = spot_price * 1.2
    
    gex_filtered = gex_by_strike[
        (gex_by_strike.index >= lower_bound) & 
        (gex_by_strike.index <= upper_bound)
    ]
    vol_filtered = vol_by_strike[
        (vol_by_strike.index >= lower_bound) & 
        (vol_by_strike.index <= upper_bound)
    ]
    
    # Calculate key statistics
    max_gex_strike = gex_filtered.idxmax() if len(gex_filtered) > 0 else None
    max_gex_value = gex_filtered.max() if len(gex_filtered) > 0 else 0
    
    net_gex = gex_filtered.sum()
    
    # Find zero-gamma level (where GEX crosses zero)
    zero_gamma_level = None
    if len(gex_filtered) > 0:
        # Find the strike closest to where GEX = 0
        gex_cumsum = gex_filtered.sort_index().cumsum()
        zero_cross = gex_cumsum[gex_cumsum.abs() == gex_cumsum.abs().min()]
        if len(zero_cross) > 0:
            zero_gamma_level = zero_cross.index[0]
    
    stats = {
        'spot_price': spot_price,
        'net_gex': net_gex,
        'max_gex_strike': max_gex_strike,
        'max_gex_value': max_gex_value,
        'zero_gamma_level': zero_gamma_level,
        'total_call_volume': vol_filtered.get('call', pd.Series([0])).sum(),
        'total_put_volume': vol_filtered.get('put', pd.Series([0])).sum()
    }
    
    return gex_filtered, vol_filtered, spot_price, stats


def get_gamma_profile(symbol):
    """
    Main function to get gamma profile data for a symbol.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        dict with 'gex', 'volume', 'spot', 'stats', and 'error' keys
    """
    try:
        # Fetch options data using cached function
        df = get_cached_options_chain(symbol)
        if df is None or df.empty:
            return {'error': f'No options data available for {symbol}'}
        
        # Calculate GEX and volume profile
        result = calculate_gamma_exposure(df)
        if result is None:
            return {'error': 'Failed to calculate gamma exposure'}
        
        gex_series, vol_df, spot_price, stats = result
        
        if gex_series.empty:
            return {'error': 'No valid strikes in range'}
        
        return {
            'gex': gex_series,
            'volume': vol_df,
            'spot': spot_price,
            'stats': stats,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        return {'error': str(e)}


if __name__ == '__main__':
    # Test the module
    result = get_gamma_profile('SPY')
    
    if 'error' in result:
        logger.info(f"Error: {result['error']}")
    else:
        logger.info(f"\nGamma Profile for SPY - {result['timestamp']}")
        logger.info(f"Spot Price: ${result['spot']:.2f}")
        logger.info(f"\nKey Statistics:")
        for key, value in result['stats'].items():
            logger.info(f"  {key}: {value}")
