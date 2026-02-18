
import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import datetime

@st.cache_data(ttl=3600*24) # Cache for 24 hours
def get_weinstein_stage(ticker):
    """
    Analyzes a ticker for Stan Weinstein's Stage Analysis.
    Focuses on 30-week SMA (approx 150-day) and Relative Strength vs SPY.
    """
    try:
        # Fetch Weekly Data for Ticker and SPY (Benchmark)
        # Weinstein uses weekly charts primarily
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(weeks=104) # 2 years for context
        
        # Batch fetch if possible? Ticker object handles it.
        # We need weekly data.
        data = yf.download([ticker, "SPY"], start=start_date, end=end_date, interval="1wk", group_by='ticker', progress=False, threads=True)
        
        if data.empty:
            return None
            
        # Handle MultiIndex
        try:
            df_t = data[ticker].copy()
            df_spy = data["SPY"].copy()
        except KeyError:
            # Fallback for single ticker download structure if it varies
            # But with list it should be MultiIndex
            return None
            
        if df_t.empty or len(df_t) < 30:
            return None

        # --- 1. 30-Week SMA (The Weinstein Standard) ---
        df_t['SMA30'] = df_t['Close'].rolling(window=30).mean()
        
        # --- 2. Stage Identification Logic ---
        # Current Price vs SMA30
        current_price = df_t['Close'].iloc[-1]
        current_sma = df_t['SMA30'].iloc[-1]
        
        # Slope of SMA30 (over last 4 weeks)
        # Is it rising or falling?
        sma_slope_4wk = (df_t['SMA30'].iloc[-1] - df_t['SMA30'].iloc[-5]) / df_t['SMA30'].iloc[-5] if len(df_t) > 34 else 0
        
        # --- 3. Mansfield Relative Strength (RS) ---
        # Formula: ((Stock / Index) / MA(Stock/Index, 52))
        # Or simpler Weinstein method: Ratio of Stock/SPY
        rs_ratio = df_t['Close'] / df_spy['Close']
        df_t['RS_Ratio'] = rs_ratio
        df_t['RS_SMA52'] = rs_ratio.rolling(window=52).mean()
        # Mansfield RS is usually (RS / SMA(RS) - 1)
        df_t['Mansfield_RS'] = (df_t['RS_Ratio'] / df_t['RS_SMA52']) - 1
        
        current_rs = df_t['Mansfield_RS'].iloc[-1]
        
        # --- Determine Stage ---
        stage = "Unknown"
        details = []
        
        # Stage 2 (Advancing) Criteria:
        # 1. Price above 30-week SMA
        # 2. 30-week SMA is rising
        # 3. RS is improving/positive
        if current_price > current_sma and sma_slope_4wk > 0.01:
            stage = "Stage 2 (Advancing)"
            details.append("✅ Price > 30-week SMA")
            details.append("✅ 30-week SMA is Rising")
        
        # Stage 4 (Declining) Criteria:
        # 1. Price below 30-week SMA
        # 2. 30-week SMA is falling
        elif current_price < current_sma and sma_slope_4wk < -0.01:
            stage = "Stage 4 (Declining)"
            details.append("❌ Price < 30-week SMA")
            details.append("❌ 30-week SMA is Falling")
            
        # Stage 1 (Basing) Criteria:
        # 1. Price oscillating around flat SMA
        elif abs(sma_slope_4wk) <= 0.01:
            if current_price >= current_sma:
                stage = "Stage 1 (Basing/Accumulation)"
            else:
                stage = "Stage 4/1 (Bottoming?)"
            details.append("➖ 30-week SMA is Flat")
            
        # Stage 3 (Topping) Criteria:
        # 1. Price chopping, SMA flattening after rise
        # This is hard to distinguish from Stage 1 without history context, 
        # but usually Stage 3 follows a Stage 2.
        # Simplified: If Price < SMA but SMA is still flat/rising
        elif current_price < current_sma and sma_slope_4wk > -0.01:
             stage = "Stage 3 (Topping)"
             details.append("⚠️ Price broken below SMA")
             details.append("⚠️ SMA still flat/rising")
             
        return {
            "stage": stage,
            "current_price": current_price,
            "sma_30": current_sma,
            "slope": sma_slope_4wk,
            "mansfield_rs": current_rs,
            "details": details,
            "data": df_t # Return dataframe for plotting
        }
        
    except Exception as e:
        print(f"Weinstein Analysis Error: {e}")
        return None
