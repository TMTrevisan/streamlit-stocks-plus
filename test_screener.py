import logging
import time
import pandas as pd
from yahooquery import Ticker

# S&P 500 approx list (subset for speed test)
sp500_sample = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ",
    "XOM", "JPM", "PG", "V", "HD", "CVX", "MA", "ABBV", "PEP", "MRK",
    "LLY", "KO", "BAC", "PFE", "AVGO", "COST", "TMO", "DIS", "CSCO", "ACN"
] * 10 # 300 tickers

print(f"Testing data fetch for {len(sp500_sample)} tickers...")
start = time.time()

try:
    tickers = Ticker(sp500_sample, asynchronous=True)
    
    # Fetch key stats
    print("Fetching summary_detail...")
    summary = tickers.summary_detail
    
    # Fetch price 
    print("Fetching price...")
    price = tickers.price
    
    # Fetch key statistics (for beta, etc)
    print("Fetching key_statistics...")
    stats = tickers.key_stats
    
    duration = time.time() - start
    print(f"Fetch complete in {duration:.2f} seconds.")
    
    # Convert to DataFrame
    df = pd.DataFrame(summary).T
    print(f"DataFrame Shape: {df.shape}")
    print("Columns:", df.columns[:10])
    
    if 'dividendYield' in df.columns:
        print("\nDividend Yield Check (AAPL):", df.loc['AAPL'].get('dividendYield'))
        
except Exception as e:
    print(f"Error: {e}")
