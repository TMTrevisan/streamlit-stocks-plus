import pandas as pd
from screener_engine import fetch_screener_data, apply_strategy

def test_screener_logic():
    # Test with a small list of tickers to verify batching logic (even if batch > list)
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "INTC", "CSCO"]
    
    print(f"Fetching data for {len(tickers)} tickers (limit=5)...")
    df = fetch_screener_data(tickers, limit=5)
    
    if df.empty:
        print("❌ No data returned.")
        return

    print(f"✅ Data fetched for {len(df)} tickers.")
    print("Columns:", df.columns.tolist())
    
    # Test Strategy Application
    print("\nTesting 'Safe Long' Strategy...")
    safe_longs = apply_strategy(df, "Safe Long")
    print(f"Safe Long Candidates: {len(safe_longs)}")
    if not safe_longs.empty:
        print(safe_longs[['Price', 'DivYield', 'Beta']].head())

if __name__ == "__main__":
    test_screener_logic()
