
import streamlit as st
import pandas as pd
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from power_gauge import calculate_power_gauge
from weinstein import get_weinstein_stage
from canslim import get_canslim_metrics

def test_analysis_modules(ticker="AAPL"):
    print(f"🔬 Testing Analysis Modules for {ticker}...")
    
    # 1. Power Gauge
    print("\n⚡ Testing Power Gauge...")
    try:
        pg = calculate_power_gauge(ticker)
        if pg:
            print(f"✅ Power Gauge Success: Rating={pg['rating']}, Score={pg['score']:.2f}")
        else:
            print("❌ Power Gauge Failed (Returned None)")
    except Exception as e:
        print(f"❌ Power Gauge Exception: {e}")

    # 2. Weinstein Stage
    print("\n📉 Testing Weinstein Stage...")
    try:
        w = get_weinstein_stage(ticker)
        if w:
            print(f"✅ Weinstein Success: Stage={w['stage']}")
        else:
            print("❌ Weinstein Failed (Returned None)")
    except Exception as e:
        print(f"❌ Weinstein Exception: {e}")

    # 3. CANSLIM
    print("\n🚀 Testing CANSLIM...")
    try:
        c = get_canslim_metrics(ticker)
        if c:
            print(f"✅ CANSLIM Success: Score={c['score']}/7")
        else:
            print("❌ CANSLIM Failed (Returned None)")
    except Exception as e:
        print(f"❌ CANSLIM Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1]
    else:
        ticker = "AAPL"
    
    test_analysis_modules(ticker)
