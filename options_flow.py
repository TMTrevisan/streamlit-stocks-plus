"""
Options Flow Analysis - Flowtopia-Inspired Indicators
Daily proxy indicators for institutional options positioning using yfinance data.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_flow_data(symbol):
    """Cached fetching of options chain for flow analysis."""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        
        if not expirations:
            return None, None, None
        
        stock_info = ticker.info
        current_price = stock_info.get('currentPrice') or stock_info.get('regularMarketPrice')
        
        target_date = datetime.now() + timedelta(days=90)
        relevant_exps = [exp for exp in expirations if datetime.strptime(exp, '%Y-%m-%d') <= target_date]
        
        all_calls = []
        all_puts = []
        
        for exp_date in relevant_exps[:10]:
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls.copy()
                calls['expiration'] = exp_date
                calls['option_type'] = 'call'
                all_calls.append(calls)
                
                puts = chain.puts.copy()
                puts['expiration'] = exp_date
                puts['option_type'] = 'put'
                all_puts.append(puts)
            except Exception:
                continue
        
        calls_df = pd.concat(all_calls, ignore_index=True) if all_calls else pd.DataFrame()
        puts_df = pd.concat(all_puts, ignore_index=True) if all_puts else pd.DataFrame()
        
        return calls_df, puts_df, current_price
    except Exception:
        return None, None, None

def calculate_contract_premium(option_data):
    """
    Calculate total premium (dollar volume) for option contracts.
    Premium = Last Price × Volume × 100 (contract multiplier)
    
    Args:
        option_data: DataFrame with option contract data
        
    Returns:
        DataFrame with premium column added
    """
    df = option_data.copy()
    
    # Use last price if available, otherwise midpoint
    if 'lastPrice' in df.columns:
        price = df['lastPrice']
    else:
        price = (df['bid'] + df['ask']) / 2
    
    df['premium'] = price * df['volume'] * 100
    
    return df


def get_daily_flow_snapshot(symbol, days_back=5):
    """
    Get multi-day options flow data for a symbol.
    
    Args:
        symbol: Stock ticker
        days_back: Number of days of history to analyze
        
    Returns:
        dict with flow data or error
    """
    try:
        # Use cached fetch function
        calls_df, puts_df, current_price = fetch_flow_data(symbol)
        
        if calls_df is None and puts_df is None:
            return {'error': f'No options data for {symbol}'}
        
        if calls_df.empty and puts_df.empty:
            return {'error': 'Could not fetch options data'}
        
        # Add premium calculation to cached data
        if not calls_df.empty:
            calls_df = calculate_contract_premium(calls_df)
        if not puts_df.empty:
            puts_df = calculate_contract_premium(puts_df)
        
        # Calculate metrics
        total_call_premium = calls_df['premium'].sum() if not calls_df.empty else 0
        total_put_premium = puts_df['premium'].sum() if not puts_df.empty else 0
        
        total_call_volume = calls_df['volume'].sum() if not calls_df.empty else 0
        total_put_volume = puts_df['volume'].sum() if not puts_df.empty else 0
        
        net_premium = total_call_premium - total_put_premium
        
        # Put/Call ratios
        pc_volume_ratio = total_put_volume / max(total_call_volume, 1)
        pc_premium_ratio = total_put_premium / max(total_call_premium, 1)
        
        # Unusual activity (Volume > 2x Open Interest)
        unusual_calls = calls_df[calls_df['volume'] > 2 * calls_df['openInterest']] if not calls_df.empty else pd.DataFrame()
        unusual_puts = puts_df[puts_df['volume'] > 2 * puts_df['openInterest']] if not puts_df.empty else pd.DataFrame()
        
        # Top contracts by premium
        top_calls = calls_df.nlargest(5, 'premium')[['strike', 'expiration', 'volume', 'openInterest', 'premium']] if not calls_df.empty else pd.DataFrame()
        top_puts = puts_df.nlargest(5, 'premium')[['strike', 'expiration', 'volume', 'openInterest', 'premium']] if not puts_df.empty else pd.DataFrame()
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'total_call_premium': total_call_premium,
            'total_put_premium': total_put_premium,
            'net_premium': net_premium,
            'total_call_volume': total_call_volume,
            'total_put_volume': total_put_volume,
            'pc_volume_ratio': pc_volume_ratio,
            'pc_premium_ratio': pc_premium_ratio,
            'unusual_calls_count': len(unusual_calls),
            'unusual_puts_count': len(unusual_puts),
            'unusual_calls': unusual_calls,
            'unusual_puts': unusual_puts,
            'top_calls': top_calls,
            'top_puts': top_puts,
            'calls_df': calls_df,
            'puts_df': puts_df,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        return {'error': str(e)}


def analyze_flow_sentiment(flow_data):
    """
    Analyze flow data and provide interpretation.
    
    Args:
        flow_data: dict from get_daily_flow_snapshot
        
    Returns:
        dict with sentiment analysis
    """
    if 'error' in flow_data:
        return {'error': flow_data['error']}
    
    net_premium = flow_data['net_premium']
    pc_premium_ratio = flow_data['pc_premium_ratio']
    pc_volume_ratio = flow_data['pc_volume_ratio']
    
    # Determine overall sentiment
    if net_premium > 0:
        if pc_premium_ratio < 0.7:
            sentiment = 'STRONGLY BULLISH'
            description = 'Heavy call buying with significant net premium flow to calls'
        else:
            sentiment = 'BULLISH'
            description = 'Positive net premium flow favoring calls'
    else:
        if pc_premium_ratio > 1.5:
            sentiment = 'STRONGLY BEARISH'
            description = 'Heavy put buying with significant net premium flow to puts'
        else:
            sentiment = 'BEARISH'
            description = 'Negative net premium flow favoring puts'
    
    # Check for unusual activity
    unusual_total = flow_data['unusual_calls_count'] + flow_data['unusual_puts_count']
    has_unusual = unusual_total > 0
    
    # Directional bias
    if pc_volume_ratio > 1.2:
        vol_bias = 'Put-heavy'
    elif pc_volume_ratio < 0.8:
        vol_bias = 'Call-heavy'
    else:
        vol_bias = 'Balanced'
    
    return {
        'sentiment': sentiment,
        'description': description,
        'has_unusual_activity': has_unusual,
        'unusual_count': unusual_total,
        'volume_bias': vol_bias,
        'premium_bias': 'Put-heavy' if pc_premium_ratio > 1 else 'Call-heavy'
    }


if __name__ == '__main__':
    # Test the module
    print("\nOptions Flow Analysis Test")
    print("=" * 60)
    
    result = get_daily_flow_snapshot('SPY')
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['symbol']} @ ${result['current_price']:.2f}")
        print(f"Timestamp: {result['timestamp']}")
        print("\nFlow Metrics:")
        print(f"  Total Call Premium: ${result['total_call_premium']:,.0f}")
        print(f"  Total Put Premium: ${result['total_put_premium']:,.0f}")
        print(f"  Net Premium: ${result['net_premium']:,.0f}")
        print(f"\nRatios:")
        print(f"  Put/Call Volume: {result['pc_volume_ratio']:.2f}")
        print(f"  Put/Call Premium: {result['pc_premium_ratio']:.2f}")
        print(f"\nUnusual Activity:")
        print(f"  Unusual Calls: {result['unusual_calls_count']}")
        print(f"  Unusual Puts: {result['unusual_puts_count']}")
        
        # Get sentiment
        sentiment = analyze_flow_sentiment(result)
        print(f"\nSentiment: {sentiment['sentiment']}")
        print(f"  {sentiment['description']}")
        print(f"  Volume Bias: {sentiment['volume_bias']}")
        print(f"  Premium Bias: {sentiment['premium_bias']}")
