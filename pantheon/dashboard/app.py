import sys
import os
from pathlib import Path

# Fix relative imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import func

from db.session import SessionLocal, init_db
from db.models import SignalRecord, PaperTrade
from data.weights_store import load_weights

st.set_page_config(
    page_title="Project Pantheon",
    page_icon="⚡",
    layout="wide"
)

def style_direction(val):
    if isinstance(val, str):
        if "BUY" in val:
            return 'background-color: rgba(0, 255, 0, 0.1); color: #00ff00;'
        elif "SELL" in val:
            return 'background-color: rgba(255, 0, 0, 0.1); color: #ff0000;'
        elif "HOLD" in val:
            return 'background-color: rgba(128, 128, 128, 0.1); color: #888888;'
    return ''

def main():
    init_db()
    
    db = SessionLocal()
    try:
        # SIDEBAR
        st.sidebar.header("Controls")
        if st.sidebar.button("Refresh Data"):
            st.rerun()
            
        st.sidebar.header("Stats")
        total_signals = db.query(SignalRecord).count()
        total_trades = db.query(PaperTrade).count()
        oldest_signal = db.query(func.min(SignalRecord.timestamp)).scalar()
        
        st.sidebar.write(f"**Total signals in DB:** {total_signals}")
        st.sidebar.write(f"**Total paper trades:** {total_trades}")
        st.sidebar.write(f"**Oldest signal date:** {oldest_signal.strftime('%Y-%m-%d') if oldest_signal else 'N/A'}")
        
        # SECTION 1: HEADER
        st.title("⚡ Project Pantheon — MMCI Signal Dashboard")
        
        last_signal = db.query(SignalRecord).order_by(SignalRecord.timestamp.desc()).first()
        market_regime = last_signal.market_regime if last_signal else "SIDEWAYS"
        
        st.subheader(f"{datetime.now().strftime('%B %d, %Y')} | Market Regime: **{market_regime}**")
        
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_signals = db.query(SignalRecord).filter(SignalRecord.timestamp >= today_start).all()
        
        t_total = len(today_signals)
        t_buy = sum(1 for s in today_signals if s.direction == "BUY")
        t_sell = sum(1 for s in today_signals if s.direction == "SELL")
        t_dissent = sum(1 for s in today_signals if s.dissent_flag)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Signals Today", t_total)
        c2.metric("BUY count", t_buy)
        c3.metric("SELL count", t_sell)
        c4.metric("DISSENT count", t_dissent)
        
        st.markdown("---")
        
        # SECTION 2: TODAY'S SIGNALS TABLE
        st.header("Today's Signals")
        if not today_signals:
            st.info("No signals found for today yet.")
        else:
            df_curr = pd.DataFrame([{
                "Symbol": s.symbol,
                "Direction": s.direction,
                "Score": round(s.consensus_score, 3),
                "Dissent": ("⚠ " if s.dissent_flag else "") + str(round(s.dissent_score, 3)),
                "Alloc%": round(s.suggested_alloc * 100, 1),
                "Risk": s.risk_level,
                "Regime": s.market_regime,
                "Time": s.timestamp.strftime("%H:%M:%S")
            } for s in today_signals])
            
            df_curr["ABS_Score"] = df_curr["Score"].abs()
            df_curr = df_curr.sort_values(by="ABS_Score", ascending=False).drop(columns=["ABS_Score"])
            
            # Apply color highlights to Direction cell
            styled_df = df_curr.style.map(style_direction, subset=['Direction'])
            st.dataframe(styled_df, use_container_width=True)
            
        st.markdown("---")
        
        # SECTION 3: MODEL WEIGHTS
        st.header("Model Weights")
        weights = load_weights()
        
        w_col1, w_col2 = st.columns(2)
        
        with w_col1:
            if weights:
                df_w = pd.DataFrame(weights.items(), columns=["Model", "Weight"]).set_index("Model")
                st.bar_chart(df_w)
            else:
                st.info("No weights found.")
                
        with w_col2:
            model_counts = []
            for k, w in weights.items():
                model_counts.append({
                    "Model": k,
                    "Weight %": round(w * 100, 2),
                    "Signals in DB": total_signals # Approximating DB count for the dashboard
                })
            st.dataframe(pd.DataFrame(model_counts), use_container_width=True)
            
        st.markdown("---")
        
        # SECTION 4: PAPER TRADES
        st.header("Paper Trades")
        open_trades = db.query(PaperTrade).filter(PaperTrade.is_open == True).all()
        
        if not open_trades:
            st.info("No active paper trades.")
        else:
            st.caption(f"Currently tracking {len(open_trades)} active trades.")
            df_trades = pd.DataFrame([{
                "Symbol": t.symbol,
                "Direction": t.direction,
                "Entry Price": f"₹{t.entry_price:.2f}",
                "Entry Date": t.entry_date.strftime("%Y-%m-%d %H:%M"),
                "Regime": t.regime_at_entry
            } for t in open_trades])
            
            styled_trades = df_trades.style.map(style_direction, subset=['Direction'])
            st.dataframe(styled_trades, use_container_width=True)
            
        st.markdown("---")
        
        # SECTION 5: SIGNAL HISTORY
        st.header("Signal History")
        history = db.query(SignalRecord).order_by(SignalRecord.timestamp.desc()).limit(50).all()
        
        if history:
            df_hist = pd.DataFrame([{
                "Time": h.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Symbol": h.symbol,
                "Direction": h.direction,
                "Score": round(h.consensus_score, 3),
                "Dissent": round(h.dissent_score, 3),
                "Price": f"₹{h.entry_price:.2f}" if h.entry_price else "N/A",
                "Reason": h.reasoning[:80] + "..." if len(h.reasoning) > 80 else h.reasoning
            } for h in history])
            
            styled_history = df_hist.style.map(style_direction, subset=['Direction'])
            st.dataframe(styled_history, use_container_width=True)
            
    except Exception as e:
        st.error(f"Execution failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
