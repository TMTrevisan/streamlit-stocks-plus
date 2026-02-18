
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import streamlit as st

@st.cache_data(ttl=3600*24)
def get_canslim_metrics(ticker):
    """
    Computes metrics for William O'Neil's CANSLIM Strategy.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        
        # --- C: Current Quarterly Earnings (EPS > 25% Growth) ---
        # yfinance often lacks quarterly history easily, use 'earningsQuarterlyGrowth'
        c_score = False
        q_growth = info.get('earningsQuarterlyGrowth', None)
        if q_growth and q_growth > 0.25:
            c_score = True
            
        # --- A: Annual Earnings Growth (3-5 years > 25%) ---
        a_score = False
        a_growth = info.get('earningsGrowth', None) # Closest proxy for now
        if a_growth and a_growth > 0.25:
            a_score = True
            
        # --- N: New Product / New Highs ---
        # Check if Price is within 15% of 52-Week High
        n_score = False
        price = info.get('currentPrice', 0)
        high52 = info.get('fiftyTwoWeekHigh', 0)
        if high52 > 0 and price >= (high52 * 0.85):
            n_score = True
            
        # --- S: Supply and Demand (Volume / Float) ---
        # Look for Volume > Avg Volume
        s_score = False
        vol = info.get('volume', 0)
        avg_vol = info.get('averageVolume', 1)
        if vol > avg_vol:
            s_score = True
            
        # --- L: Leader or Laggard (Relative Strength > 80) ---
        # We need to compute RS Rating (mock 0-99 percentile vs Market)
        # Simplified: Is 1-year return > SPY return?
        l_score = False
        try:
             # Fetch 1y Data
            hist = t.history(period="1y")
            if not hist.empty:
                ret_1y = (hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1
                # Benchmark (Static 10% assumption or fetch SPY)
                # Let's be better, fetch SPY briefly?
                # Optimization: Assume 10% annual market return or use a fixed threshold > 20%
                if ret_1y > 0.2: 
                    l_score = True
        except:
            pass

        # --- I: Institutional Sponsorship ---
        # Can't reliably get this from free yfinance. 
        # Proxy: Institutional Holder % > 30%?
        i_score = False
        inst_hold = info.get('heldPercentInstitutions', 0)
        if inst_hold and inst_hold > 0.3:
            i_score = True
            
        # --- M: Market Direction ---
        # User input or global check. We'll default to True if SPY > SMA200 (checked elsewhere)
        # For this function, let's assume Neutral/Bullish unless passed in.
        m_score = True 

        # --- Aggregate Score ---
        checklist = {
            "C (Current Earnings)": {"pass": c_score, "value": f"{q_growth:.1%}" if q_growth else "N/A"},
            "A (Annual Earnings)": {"pass": a_score, "value": f"{a_growth:.1%}" if a_growth else "N/A"},
            "N (New Highs)": {"pass": n_score, "value": f"${price} vs ${high52}"},
            "S (Supply/Demand)": {"pass": s_score, "value": f"Vol: {vol/avg_vol:.1f}x Avg"},
            "L (Leader)": {"pass": l_score, "value": "Strong RS"},
            "I (Institutions)": {"pass": i_score, "value": f"{inst_hold:.1%} Owned"},
            "M (Market Direction)": {"pass": m_score, "value": "Uptrend (Assumed)"}
        }
        
        score = sum([1 for k, v in checklist.items() if v['pass']])
        
        return {
            "score": score,
            "checklist": checklist
        }

    except Exception as e:
        print(f"CANSLIM Error: {e}")
        return None
