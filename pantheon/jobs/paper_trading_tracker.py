import sys
from pathlib import Path

# Fix relative imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import math
import statistics
from datetime import datetime

from db.session import SessionLocal
from db.models import SignalRecord, PaperTrade
from data.weights_store import load_weights

GATE_CRITERIA = {
    "MIN_SHARPE":        1.5,
    "MAX_DRAWDOWN_MULT": 1.0,   # Must not exceed Nifty drawdown
    "MIN_ACCURACY":      0.55,  # 55% directional accuracy
    "MIN_REGIMES":       2,     # Alpha in at least 2 of 3 regimes
    "MIN_DISSENT_VALID": 0.70,  # 70% of DISSENT flags avoided adverse moves
    "MAX_WEIGHT_VAR":    0.03,  # Weight variance below this = converged
    "MIN_TRADING_DAYS":  90
}

def compute_metrics() -> dict:
    db = SessionLocal()
    
    try:
        # 1. SIGNALS WITH OUTCOMES
        all_signals = db.query(SignalRecord).filter(SignalRecord.outcome != None).all()
        
        if not all_signals:
            return {
                "total_signals": 0,
                "total_trades": 0,
                "accuracy": 0.0,
                "sharpe": 0.0,
                "max_drawdown_pct": 0.0,
                "regimes_positive": 0,
                "dissent_rate": 0.0,
                "days_elapsed": 0,
                "weight_variance": 0.0,
                "regime_pnl": {}
            }

        # 2. DIRECTIONAL ACCURACY
        correct = sum(1 for s in all_signals if s.direction == s.outcome and s.direction != "HOLD")
        directional = [s for s in all_signals if s.direction != "HOLD"]
        accuracy = correct / len(directional) if directional else 0.0

        # 3. PAPER TRADE P&L
        closed = db.query(PaperTrade).filter_by(is_open=False).all()
        pnls = [t.pnl_pct for t in closed if t.pnl_pct is not None]

        # 4. SHARPE RATIO
        if len(pnls) >= 2:
            mean_pnl = statistics.mean(pnls)
            std_pnl  = statistics.stdev(pnls)
            sharpe   = (mean_pnl / std_pnl) * (252 ** 0.5) if std_pnl > 0 else 0.0
        else:
            sharpe = 0.0

        # 5. MAX DRAWDOWN
        max_dd = 0.0
        if pnls:
            cumulative = []
            running = 100.0
            for p in pnls:
                running *= (1 + p/100)
                cumulative.append(running)
            peak = 100.0
            for val in cumulative:
                if val > peak: 
                    peak = val
                dd = (peak - val) / peak * 100
                if dd > max_dd: 
                    max_dd = dd

        # 6. REGIME-STRATIFIED RETURNS
        regime_pnl = {"BULL": [], "BEAR": [], "SIDEWAYS": []}
        for t in closed:
            if t.pnl_pct is not None and t.regime_at_entry in regime_pnl:
                regime_pnl[t.regime_at_entry].append(t.pnl_pct)
                
        regime_alpha = {
            r: statistics.mean(v) > 0
            for r, v in regime_pnl.items() if v
        }
        regimes_positive = sum(1 for v in regime_alpha.values() if v)

        # 7. DISSENT VALIDATION
        dissent_signals = [s for s in all_signals if s.dissent_flag]
        dissent_avoided = sum(
            1 for s in dissent_signals
            if s.outcome == "HOLD"  # Stayed flat = avoided adverse move
        )
        dissent_rate = (dissent_avoided / len(dissent_signals)) if dissent_signals else 0.0

        # 8. TRADING DAYS ELAPSED
        oldest = min(s.timestamp for s in all_signals) if all_signals else datetime.utcnow()
        days_elapsed = (datetime.utcnow() - oldest).days

        # 9. WEIGHT CONVERGENCE
        weights = load_weights()
        if weights:
            w_values = list(weights.values())
            weight_var = statistics.variance(w_values) if len(w_values) > 1 else 1.0
        else:
            weight_var = 1.0
            
        return {
            "total_signals":    len(all_signals),
            "total_trades":     len(closed),
            "accuracy":         round(accuracy, 4),
            "sharpe":           round(sharpe, 4),
            "max_drawdown_pct": round(max_dd, 4),
            "regimes_positive": regimes_positive,
            "dissent_rate":     round(dissent_rate, 4),
            "days_elapsed":     days_elapsed,
            "weight_variance":  round(weight_var, 6),
            "regime_pnl":       {r: round(statistics.mean(v), 4) if v else None 
                                 for r, v in regime_pnl.items()},
        }
    except Exception as e:
        print(f"Error computing metrics: {e}")
        return {}
    finally:
        db.close()


def check_exit_gate() -> dict:
    m = compute_metrics()
    if not m:
        m = {
            "sharpe": 0.0, "max_drawdown_pct": 0.0, "accuracy": 0.0,
            "regimes_positive": 0, "dissent_rate": 0.0, "weight_variance": 1.0,
            "days_elapsed": 0, "total_signals": 0, "total_trades": 0
        }
        
    gate = {
        "sharpe":       m["sharpe"]           >= GATE_CRITERIA["MIN_SHARPE"],
        "drawdown":     m["max_drawdown_pct"] <= 15.0,  # Hardcoded max baseline logic for now
        "accuracy":     m["accuracy"]         >= GATE_CRITERIA["MIN_ACCURACY"],
        "regimes":      m["regimes_positive"] >= GATE_CRITERIA["MIN_REGIMES"],
        "dissent":      m["dissent_rate"]     >= GATE_CRITERIA["MIN_DISSENT_VALID"],
        "weight_conv":  m["weight_variance"]  <= GATE_CRITERIA["MAX_WEIGHT_VAR"],
        "days":         m["days_elapsed"]     >= GATE_CRITERIA["MIN_TRADING_DAYS"],
    }
    passed = sum(1 for v in gate.values() if v)
    
    return {
        "metrics":      m,
        "gate":         gate,
        "passed":       passed,
        "total":        len(gate),
        "ready":        passed == len(gate),
    }

def print_gate_report() -> None:
    result = check_exit_gate()
    m = result["metrics"]
    g = result["gate"]
    
    print("=" * 60)
    print("PAPER TRADING EXIT GATE REPORT")
    print("=" * 60)
    print(f"Days elapsed:       {m['days_elapsed']} / 90 required")
    print(f"Total signals:      {m['total_signals']}")
    print(f"Directional trades: {m['total_trades']}")
    print()
    
    rows = [
        ("Sharpe Ratio",      f"{m['sharpe']:.3f}",       ">= 1.5",     g["sharpe"]),
        ("Max Drawdown",      f"{m['max_drawdown_pct']:.2f}%", "<= 15%",   g["drawdown"]),
        ("Directional Acc",   f"{m['accuracy']:.1%}",     ">= 55%",     g["accuracy"]),
        ("Regime Coverage",   f"{m['regimes_positive']}/3",">= 2 regimes",g["regimes"]),
        ("Dissent Validity",  f"{m['dissent_rate']:.1%}", ">= 70%",     g["dissent"]),
        ("Weight Convergence",f"{m['weight_variance']:.5f}","<= 0.03",  g["weight_conv"]),
        ("Trading Days",      f"{m['days_elapsed']}",     ">= 90",      g["days"]),
    ]
    
    for name, value, target, passed in rows:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name:<22} {value:<12} {target}")
        
    print()
    print(f"Gate: {result['passed']}/{result['total']} criteria met")
    if result["ready"]:
        print("🚀 READY FOR LIVE TRADING")
    else:
        print("⏳ Continue paper trading")
    print("=" * 60)

if __name__ == "__main__":
    print_gate_report()
