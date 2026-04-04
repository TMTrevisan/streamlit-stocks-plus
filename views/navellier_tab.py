import streamlit as st
from navellier import calculate_navellier_grader, get_color_for_grade

def render_navellier(ticker):
    st.markdown("### 🎓 Louis Navellier Portfolio Grader")
    st.caption("A data-driven methodology identifying stocks with high growth potential based on Fundamental and Quantitative factors.")
    
    if not ticker:
        st.warning("Please enter a ticker symbol to view its Navellier Grade.")
        return
        
    with st.spinner(f"Calculating Navellier Grade for {ticker}..."):
        grader_data = calculate_navellier_grader(ticker)
        
    if not grader_data:
        st.error(f"Could not calculate grades for {ticker}. The ticker may be invalid or missing fundamental data.")
        if st.button("Retry Navellier Grade", key="retry_nav"):
            st.rerun()
        return

    # Total Grade Header
    total_grade = grader_data['total_grade']
    total_score = grader_data['total_score']
    t_color = get_color_for_grade(total_grade)
    
    st.markdown(f"""
        <div style='background-color: #1e293b; padding: 25px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid {t_color}; text-align: center;'>
            <h2 style='margin:0; font-size: 1.5rem; color: #cbd5e1;'>Overall Portfolio Grade</h2>
            <h1 style='margin:0; font-size: 3rem; color: {t_color};'>{total_grade}</h1>
            <p style='margin:0; font-size: 1rem; color: #94a3b8;'>Composite Score: {total_score:.1f} / 100</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fund = grader_data['fundamental_grade']
        f_color = get_color_for_grade(fund['grade'])
        st.markdown(f"""
            <div style='background-color: #0f172a; padding: 15px; border-radius: 8px; border-top: 3px solid {f_color};'>
                <h3 style='margin:0; font-size: 1.2rem; color: #e2e8f0;'>Fundamental Grade</h3>
                <h2 style='margin:0; font-size: 2rem; color: {f_color};'>{fund['grade']}</h2>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for metric, data in fund['metrics'].items():
            val = data['value']
            score = data['score']
            try:
                # Format smartly based on typical ranges
                if metric in ['Analyst Revisions']:
                    val_str = f"{val:.2f}" if val is not None else "N/A"
                elif metric in ['Earnings Momentum']:
                    val_str = f"{val:.2f}x" if val is not None else "N/A"
                else: # Percentages
                    val_str = f"{val:+.1%}" if val is not None else "N/A"
            except:
                val_str = str(val)

            st.metric(f"{metric}", value=val_str, delta=f"{score:.0f}/100 Score", delta_color="normal" if score >= 50 else "inverse")
            
    with col2:
        quant = grader_data['quantitative_grade']
        q_color = get_color_for_grade(quant['grade'])
        st.markdown(f"""
            <div style='background-color: #0f172a; padding: 15px; border-radius: 8px; border-top: 3px solid {q_color};'>
                <h3 style='margin:0; font-size: 1.2rem; color: #e2e8f0;'>Quantitative Grade</h3>
                <h2 style='margin:0; font-size: 2rem; color: {q_color};'>{quant['grade']}</h2>
                <p style='margin:0; font-size: 0.9rem; color: #94a3b8;'>Measures Buying Pressure</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        for metric, data in quant['metrics'].items():
            val = data['value']
            score = data['score']
            if metric == "Buying Pressure (CMF)":
                val_str = f"{val:+.2f}" if val is not None else "N/A"
            else:
                val_str = f"{val:.2f}x" if val is not None else "N/A"
                
            st.metric(f"{metric}", value=val_str, delta=f"{score:.0f}/100 Score", delta_color="normal" if score >= 50 else "inverse")

    st.divider()
    with st.expander("Methodology Explained"):
        st.write(\"\"\"
        **Fundamental Grade** is determined by assessing:
        * Sales Growth, Operating Margin Growth, Earnings Growth, Earnings Surprises, Analyst Earnings Revisions, Cash Flow, Return on Equity.
        
        **Quantitative Grade** looks at the stock's buying pressure (using metrics like Chaikin Money Flow & Momentum). The more money that floods into a stock, the more momentum it has, and the higher the grade.
        
        **Composite Score Mapping**:
        * A (Strong Buy): Excellent growth potential & favorable sentiment.
        * B (Buy): Solid investment with slightly less upside.
        * C (Hold): Neutral rating.
        * D (Sell): Underwhelming fundamentals.
        * F (Strong Sell): Significant downside risks.
        \"\"\")
