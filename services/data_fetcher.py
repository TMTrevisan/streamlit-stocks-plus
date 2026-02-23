import streamlit as st
import yfinance as yf
import pandas as pd
from services.logger import setup_logger
logger = setup_logger(__name__)

@st.cache_data(ttl=300) # Cache for 5 minutes
def fetch_stock_history(symbol):
    try:
        # Use Ticker object for better reliability than download()
        stock = yf.Ticker(symbol)
        df = stock.history(period="2y", interval="1d")
        return df
    except Exception as e:
        logger.info(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        return stock.info
    except Exception as e:
        logger.info(f"Error fetching info for {symbol}: {e}")
        return {}

@st.cache_data(ttl=86400) # Cache for 24 hours
def get_ticker_options():
    # Common ETFs/Indices not in S&P 500 list
    etfs = [
        "SPY - SPDR S&P 500 ETF Trust",
        "QQQ - Invesco QQQ Trust",
        "IWM - iShares Russell 2000 ETF",
        "DIA - SPDR Dow Jones Industrial Average ETF",
        "GLD - SPDR Gold Shares",
        "SLV - iShares Silver Trust",
        "TLT - iShares 20+ Year Treasury Bond ETF",
        "VIX - CBOE Volatility Index", 
        "XLC - Communication Services Select Sector SPDR Fund",
        "XLY - Consumer Discretionary Select Sector SPDR Fund",
        "XLP - Consumer Staples Select Sector SPDR Fund",
        "XLE - Energy Select Sector SPDR Fund",
        "XLF - Financial Select Sector SPDR Fund",
        "XLV - Health Care Select Sector SPDR Fund",
        "XLI - Industrial Select Sector SPDR Fund",
        "XLB - Materials Select Sector SPDR Fund",
        "XLRE - Real Estate Select Sector SPDR Fund",
        "XLK - Technology Select Sector SPDR Fund",
        "XLU - Utilities Select Sector SPDR Fund",
        "SMH - VanEck Semiconductor ETF",
        "HYG - iShares iBoxx $ High Yield Corp Bond ETF",
        "LQD - iShares iBoxx $ Inv Grade Corp Bond ETF"
    ]
    
    try:
        # Load S&P 500 constituents
        df = pd.read_csv('tickers.csv')
        # Format: "AAPL - Apple Inc."
        stocks = (df['Symbol'] + " - " + df['Security']).tolist()
        return etfs + sorted(stocks)
    except Exception as e:
        logger.info(f"Error loading tickers list: {e}")
        return etfs # Fallback if csv missing

def calculate_mphinancial_mechanics(df):
    import numpy as np # Local import since it's only used here
    # 1. The EMA Stack (The mphinancial Core)
    for p in [8, 21, 34, 55, 89]:
        df[f'EMA{p}'] = df['Close'].ewm(span=p, adjust=False).mean()
    
    # 2. The 200 SMA (The Wind)
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # 3. ADX (Trend Strength) - Manual Calculation for Chromebook Compatibility
    n = 14
    h = df['High'].values.flatten()
    l = df['Low'].values.flatten()
    c = df['Close'].values.flatten()
    
    # Vectorized DM calculation
    plus_dm = np.insert(np.where((h[1:] - h[:-1]) > (l[:-1] - l[1:]), np.maximum(h[1:] - h[:-1], 0), 0), 0, 0)
    minus_dm = np.insert(np.where((l[:-1] - l[1:]) > (h[1:] - h[:-1]), np.maximum(l[:-1] - l[1:], 0), 0), 0, 0)
    tr = np.insert(np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1]))), 0, 0)
    
    # Ensure Series are 1D to prevent dimension errors
    atr_series = pd.Series(tr, index=df.index).rolling(window=n).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=n).mean() / atr_series)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=n).mean() / atr_series)
    
    # Handle division by zero/NaN for DX calculation
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di)).fillna(0)
    
    df['ADX'] = dx.rolling(window=n).mean()
    df['ATR'] = atr_series
    return df
