"""
Asbury 6 Market Health Metrics

Quantitative daily gauge of US equity market internal strength.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from services.logger import setup_logger
logger = setup_logger(__name__)


@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_ticker_data(ticker, start_date, end_date):
    """Fetches historical data for a given ticker."""
    return yf.download(ticker, start=start_date, end=end_date, progress=False)


def calculate_market_breadth(spy_data):
    """
    Market Breadth: Measures participation across the market.
    
    Uses SPY volume and price distribution as a proxy.
    Positive signal when recent volume is above average and price is making new highs.
    
    Args:
        spy_data: DataFrame with SPY historical data
        
    Returns:
        dict with name, value, status, and description
    """
    # Calculate 20-day average volume
    avg_volume_20 = spy_data['Volume'].rolling(window=20).mean().iloc[-1]
    current_volume = spy_data['Volume'].iloc[-1]
    
    # Check if we're near 20-day highs
    high_20 = spy_data['High'].rolling(window=20).max().iloc[-1]
    current_price = spy_data['Close'].iloc[-1]
    
    # Breadth is positive if volume is above average and price is near highs
    volume_ratio = current_volume / avg_volume_20
    price_ratio = current_price / high_20
    
    # Positive if volume > 100% of avg and price within 2% of 20-day high
    is_positive = volume_ratio > 1.0 and price_ratio > 0.98
    
    return {
        'name': 'Market Breadth',
        'value': f'{volume_ratio:.2f}x avg volume, {price_ratio*100:.1f}% of 20d high',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Strong participation' if is_positive else 'Narrow participation'
    }


def calculate_volume_strength(spy_data):
    """
    Volume: Tracks trading activity and conviction.
    
    High volume reflects strong conviction; low volume signals indecision.
    
    Args:
        spy_data: DataFrame with SPY historical data
        
    Returns:
        dict with name, value, status, and description
    """
    # Calculate 50-day average volume
    avg_volume_50 = spy_data['Volume'].rolling(window=50).mean().iloc[-1]
    recent_avg_volume_5 = spy_data['Volume'].rolling(window=5).mean().iloc[-1]
    
    volume_ratio = recent_avg_volume_5 / avg_volume_50
    
    # Positive if recent 5-day average is at least 110% of 50-day average
    is_positive = volume_ratio > 1.10
    
    return {
        'name': 'Volume',
        'value': f'{volume_ratio:.2f}x (5d avg / 50d avg)',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'High conviction' if is_positive else 'Low conviction'
    }


def calculate_relative_performance(spy_data, iwm_data):
    """
    Relative Performance: Compares small caps vs large caps.
    
    Outperformance by small caps (IWM vs SPY) suggests risk appetite.
    
    Args:
        spy_data: DataFrame with SPY historical data
        iwm_data: DataFrame with IWM historical data
        
    Returns:
        dict with name, value, status, and description
    """
    # Calculate 20-day returns for both
    spy_return = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-20] - 1) * 100
    iwm_return = (iwm_data['Close'].iloc[-1] / iwm_data['Close'].iloc[-20] - 1) * 100
    
    relative_performance = iwm_return - spy_return
    
    # Positive if IWM is outperforming SPY (suggests risk-on)
    is_positive = relative_performance > 0
    
    return {
        'name': 'Relative Performance',
        'value': f'IWM {iwm_return:+.1f}% vs SPY {spy_return:+.1f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Small caps leading (risk-on)' if is_positive else 'Large caps defensive'
    }


def calculate_asset_flows(spy_data, tlt_data):
    """
    Asset Flows: Reflects capital movement between stocks and bonds.
    
    Inflows to bonds (TLT outperforming) may signal risk-off sentiment.
    
    Args:
        spy_data: DataFrame with SPY historical data
        tlt_data: DataFrame with TLT historical data
        
    Returns:
        dict with name, value, status, and description
    """
    # Calculate 10-day returns for both
    spy_return = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-10] - 1) * 100
    tlt_return = (tlt_data['Close'].iloc[-1] / tlt_data['Close'].iloc[-10] - 1) * 100
    
    # Positive if stocks (SPY) outperforming bonds (TLT)
    is_positive = spy_return > tlt_return
    
    return {
        'name': 'Asset Flows',
        'value': f'SPY {spy_return:+.1f}% vs TLT {tlt_return:+.1f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Capital flowing to equities' if is_positive else 'Flight to safety (bonds)'
    }


def calculate_volatility(vix_data):
    """
    Volatility (VIX): Gauges expected market volatility and fear.
    
    Rising VIX typically indicates increased fear and uncertainty.
    Low VIX suggests complacency and stable conditions.
    
    Args:
        vix_data: DataFrame with VIX historical data
        
    Returns:
        dict with name, value, status, and description
    """
    current_vix = vix_data['Close'].iloc[-1]
    vix_20d_avg = vix_data['Close'].rolling(window=20).mean().iloc[-1]
    
    # Positive if VIX is below 20 and trending down
    is_positive = current_vix < 20 and current_vix < vix_20d_avg
    
    return {
        'name': 'Volatility (VIX)',
        'value': f'{current_vix:.2f} (20d avg: {vix_20d_avg:.2f})',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Low fear, stable market' if is_positive else 'Elevated uncertainty'
    }


def calculate_price_roc(spy_data):
    """
    Price Rate of Change: Measures momentum of price moves.
    
    Captures how fast price is changing over time (slope of trendline).
    
    Args:
        spy_data: DataFrame with SPY historical data
        
    Returns:
        dict with name, value, status, and description
    """
    # Calculate 20-day ROC
    roc_20 = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-20]) - 1) * 100
    
    # Also check if the trend is accelerating (10-day vs 20-day)
    roc_10 = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-10]) - 1) * 100
    
    # Positive if 20-day ROC is positive and accelerating
    is_positive = roc_20 > 0 and roc_10 > (roc_20 / 2)
    
    return {
        'name': 'Price ROC',
        'value': f'20d: {roc_20:+.2f}%, 10d: {roc_10:+.2f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Strong upward momentum' if is_positive else 'Weak or negative momentum'
    }


def get_asbury_6_signals():
    """
    Main orchestrator function that fetches all required market data 
    and calculates all six Asbury 6 signals.
    
    Returns:
        dict with:
            - 'metrics': list of 6 metric dicts
            - 'signal': 'BUY', 'CASH', or 'NEUTRAL'
            - 'positive_count': number of positive signals
            - 'negative_count': number of negative signals
            - 'timestamp': when the data was fetched
    """
    try:
        # Fetch required data using cached helper
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # Convert to strings for cache key
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        spy_data = fetch_ticker_data('SPY', start_str, end_str)
        iwm_data = fetch_ticker_data('IWM', start_str, end_str)
        tlt_data = fetch_ticker_data('TLT', start_str, end_str)
        vix_data = fetch_ticker_data('^VIX', start_str, end_str)
        
        # Flatten MultiIndex columns if present
        for df in [spy_data, iwm_data, tlt_data, vix_data]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        
        # Calculate all six metrics
        metrics = [
            calculate_market_breadth(spy_data),
            calculate_volume_strength(spy_data),
            calculate_relative_performance(spy_data, iwm_data),
            calculate_asset_flows(spy_data, tlt_data),
            calculate_volatility(vix_data),
            calculate_price_roc(spy_data)
        ]
        
        # Count positive and negative signals
        positive_count = sum(1 for m in metrics if m['status'] == 'Positive')
        negative_count = sum(1 for m in metrics if m['status'] == 'Negative')
        
        # Determine overall signal
        if positive_count >= 4:
            signal = 'BUY'
        elif negative_count >= 4:
            signal = 'CASH'
        else:
            signal = 'NEUTRAL'
        
        return {
            'metrics': metrics,
            'signal': signal,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    except Exception as e:
        # Return error state
        return {
            'error': str(e),
            'metrics': [],
            'signal': 'ERROR',
            'positive_count': 0,
            'negative_count': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


def get_asbury_6_historical(days=90):
    """
    Calculate historical Asbury 6 signals over a specified time period.
    Returns a DataFrame with dates, signal counts, and overall signal.
    
    Args:
        days: Number of days of history to calculate
        
    Returns:
        DataFrame with columns: Date, Positive_Count, Negative_Count, Signal
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 60)  # Extra buffer for calculations
        
        # Fetch all required data using cached helper
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        spy_data = fetch_ticker_data('SPY', start_str, end_str)
        iwm_data = fetch_ticker_data('IWM', start_str, end_str)
        tlt_data = fetch_ticker_data('TLT', start_str, end_str)
        vix_data = fetch_ticker_data('^VIX', start_str, end_str)
        
        # Flatten MultiIndex columns if present
        for df in [spy_data, iwm_data, tlt_data, vix_data]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        
        # Calculate signals for each day
        history = []
        
        # Start from a point where we have enough data for all calculations
        start_idx = 60
        
        for i in range(start_idx, len(spy_data)):
            date = spy_data.index[i]
            
            # Get subset of data up to this date for calculations
            spy_subset = spy_data.iloc[:i+1]
            iwm_subset = iwm_data.iloc[:i+1]
            tlt_subset = tlt_data.iloc[:i+1]
            vix_subset = vix_data.iloc[:i+1]
            
            # Calculate each metric
            try:
                metrics = [
                    calculate_market_breadth(spy_subset),
                    calculate_volume_strength(spy_subset),
                    calculate_relative_performance(spy_subset, iwm_subset),
                    calculate_asset_flows(spy_subset, tlt_subset),
                    calculate_volatility(vix_subset),
                    calculate_price_roc(spy_subset)
                ]
                
                positive_count = sum(1 for m in metrics if m['status'] == 'Positive')
                negative_count = sum(1 for m in metrics if m['status'] == 'Negative')
                
                if positive_count >= 4:
                    signal = 'BUY'
                elif negative_count >= 4:
                    signal = 'CASH'
                else:
                    signal = 'NEUTRAL'
                
                history.append({
                    'Date': date,
                    'Positive_Count': positive_count,
                    'Negative_Count': negative_count,
                    'Signal': signal,
                    'SPY_Close': spy_subset['Close'].iloc[-1]
                })
            except Exception as e:
                logger.info(f"Error calculating historical A6 on {date.date()}: {e}")
                continue
        
        return pd.DataFrame(history)
    
    except Exception as e:
        return pd.DataFrame()


if __name__ == '__main__':

    # Test the module
    result = get_asbury_6_signals()
    logger.info(f"\nAsbury 6 Market Health Check - {result['timestamp']}")
    logger.info(f"Overall Signal: {result['signal']} ({result['positive_count']} Positive, {result['negative_count']} Negative)\n")
    
    for metric in result['metrics']:
        status_icon = '✅' if metric['status'] == 'Positive' else '❌'
        logger.info(f"{status_icon} {metric['name']}: {metric['value']}")
        logger.info(f"   {metric['description']}\n")
