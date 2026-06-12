"""
backtest.py — Backtesting simple para ClawTrader
Registra operaciones, evalúa win rate, drawdown, profit factor
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from load_env import load_env, status_dir

load_env()
DB_FILE = Path(os.environ.get("CLAWTRADER_TRADES_FILE", status_dir() / "trades_db.json"))


def load_trades():
    if DB_FILE.exists():
        with open(DB_FILE) as f:
            return json.load(f)
    return []


def save_trades(trades):
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(trades, f, indent=2)


def register_trade(sym, entry, exit_p, tp, sl, size_pct, score, entry_r1, btc_trend):
    """Registra una operación completada o en curso."""
    trades = load_trades()
    trade = {
        "sym": sym,
        "entry": round(entry, 6),
        "exit": round(exit_p, 6) if exit_p else None,
        "tp": round(tp, 6) if tp else None,
        "sl": round(sl, 6) if sl else None,
        "size_pct": size_pct,
        "score": score,
        "entry_rsi_1h": entry_r1,
        "btc_trend": btc_trend,
        "status": "open" if not exit_p else "closed",
        "timestamp": int(time.time()),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    if trade["status"] == "closed":
        trade["pnl_usdt"] = round((exit_p - entry) / entry * trade.get("capital_usado", 10), 2)
        trade["pnl_pct"] = round((exit_p - entry) / entry * 100, 2)
    trades.append(trade)
    save_trades(trades)
    return trade


def close_trade(sym, exit_p):
    """Cierra una operación abierta."""
    trades = load_trades()
    for t in reversed(trades):
        if t["sym"] == sym and t["status"] == "open":
            t["status"] = "closed"
            t["exit"] = round(exit_p, 6)
            t["pnl_pct"] = round((exit_p - t["entry"]) / t["entry"] * 100, 2)
            t["pnl_usdt"] = round(t["pnl_pct"] / 100 * 10, 2)  # estimado con $10
            t["exit_time"] = int(time.time())
            save_trades(trades)
            return t
    return None


def get_stats():
    """Calcula métricas de backtesting."""
    trades = load_trades()
    closed = [t for t in trades if t["status"] == "closed"]
    
    if not closed:
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "best_trade": None,
            "worst_trade": None,
            "score_avg_win": 0,
            "score_avg_loss": 0,
            "consecutive_losses": 0
        }
    
    wins = [t for t in closed if t.get("pnl_pct", 0) > 0]
    losses = [t for t in closed if t.get("pnl_pct", 0) <= 0]
    
    avg_win = sum(t["pnl_pct"] for t in wins) / len(wins) if wins else 0
    avg_loss = sum(t["pnl_pct"] for t in losses) / len(losses) if losses else 0
    
    total_wins = sum(t["pnl_pct"] for t in wins) if wins else 0
    total_losses = abs(sum(t["pnl_pct"] for t in losses)) if losses else 0
    
    profit_factor = round(total_wins / total_losses, 2) if total_losses > 0 else (total_wins if total_wins > 0 else 0)
    
    best = max(closed, key=lambda t: t.get("pnl_pct", 0)) if wins else None
    worst = min(closed, key=lambda t: t.get("pnl_pct", 0)) if losses else None
    
    # Score promedio en wins vs losses
    score_wins = sum(t.get("score", 0) for t in wins) / len(wins) if wins else 0
    score_losses = sum(t.get("score", 0) for t in losses) / len(losses) if losses else 0
    
    # Racha máxima de pérdidas
    max_consec = 0
    curr = 0
    for t in sorted(closed, key=lambda x: x.get("timestamp", 0)):
        if t.get("pnl_pct", 0) <= 0:
            curr += 1
            max_consec = max(max_consec, curr)
        else:
            curr = 0
    
    return {
        "total": len(closed),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(closed) * 100, 1),
        "profit_factor": profit_factor,
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "best_trade": best["sym"] + " " + str(best.get("pnl_pct", 0)) + "%" if best else None,
        "worst_trade": worst["sym"] + " " + str(worst.get("pnl_pct", 0)) + "%" if worst else None,
        "score_avg_win": round(score_wins, 1),
        "score_avg_loss": round(score_losses, 1),
        "consecutive_losses": max_consec
    }

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(get_stats(), indent=2))
    else:
        print(f"Trades registrados: {len(load_trades())}")
        print(json.dumps(get_stats(), indent=2))


if __name__ == "__main__":
    main()
