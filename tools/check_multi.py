#!/usr/bin/env python3
"""
Multi-activo check para ClawTrader.
Escanea MSFT, NVDA, QQQ, SPY en 1m y escribe estado al archivo.
Corre cada 2 minutos via cron (clawtrader-check-aggressive).
"""
import yfinance as yf, json, os
from datetime import datetime
from load_env import env_float, load_env, status_dir

load_env()

SYMBOLS = {
    "MSFT": {"name": "Microsoft", "active": True},
    "NVDA": {"name": "NVIDIA", "active": True}
}
CAPITAL = env_float("CLAWTRADER_CAPITAL", 1000)
RISK_PCT = 0.005
STOP_PCT = 0.0085
STATUS_FILE = status_dir() / "clawtrader_status.json"

def get_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return float(rs.iloc[-1])

def analyze_symbol(sym):
    t = yf.Ticker(sym)
    df = t.history(period='1d', interval='1m')
    
    result = {"symbol": sym, "error": None}
    
    if df.empty or len(df) < 15:
        result["error"] = f"insufficient_data: {len(df)}"
        return result
    
    close = df['Close']
    current = round(float(close.iloc[-1]), 2)
    low_day = round(float(df['Low'].min()), 2)
    high_day = round(float(df['High'].max()), 2)
    pos_pct = round(((current - low_day) / (high_day - low_day)) * 100, 1)
    rsi = round(get_rsi(close), 1)
    
    # EMAs
    ema9 = round(float(close.ewm(span=9).mean().iloc[-1]), 2)
    ema21 = round(float(close.ewm(span=21).mean().iloc[-1]), 2)
    
    # Structure
    lows_5 = [float(x) for x in df['Low'].tail(5).values]
    hl = bool(lows_5[-1] > min(lows_5[:-1]))
    
    last = df.iloc[-1]
    bc = bool(float(last['Close']) >= float(last['Open']))
    body = round(abs(float(last['Close']) - float(last['Open'])), 2)
    
    last3 = df.tail(3)
    bc3 = sum(1 for i in range(3) if float(last3.iloc[i]['Close']) >= float(last3.iloc[i]['Open']))
    
    result.update({
        "price": current,
        "rsi": rsi,
        "pos_pct": pos_pct,
        "low": low_day,
        "high": high_day,
        "ema9": ema9,
        "ema21": ema21,
        "hl": hl,
        "bc": bc,
        "bc3": bc3,
        "body": body
    })
    
    # Condiciones de entrada
    # Para MSFT: mas conservador (pos <= 45)
    # Para NVDA: mas relajado porque esta alto (pos <= 92)
    if sym == "MSFT":
        cond_pos = pos_pct <= 45
    else:
        cond_pos = pos_pct <= 92
    
    cond_rsi = rsi >= 30
    cond_hl = hl
    cond_bc = bc
    cond_bc3 = bc3 >= 2
    cond_body = body >= 0.05
    
    result["conditions"] = {
        "pos_ok": cond_pos,
        "rsi_ok": cond_rsi,
        "hl_ok": cond_hl,
        "bc_ok": cond_bc,
        "bc3_ok": cond_bc3,
        "body_ok": cond_body
    }
    
    if all([cond_pos, cond_rsi, cond_hl, cond_bc, cond_bc3, cond_body]):
        risk_share = round(current * STOP_PCT, 2)
        shares = max(1, min(100, int((CAPITAL * RISK_PCT) / risk_share)))
        stop = round(current - risk_share, 2)
        t1 = round(current + risk_share * 1.5, 2)
        t2 = round(current + risk_share * 2.5, 2)
        result["entry"] = {
            "signal": "ENTRADA",
            "shares": shares,
            "stop": stop,
            "t1": t1,
            "t2": t2,
            "rr1": round((t1 - current) / risk_share, 2),
            "rr2": round((t2 - current) / risk_share, 2),
            "risk_usd": round(shares * risk_share, 2),
            "capital_after": round(CAPITAL - shares * current, 2)
        }
    
    return result

# Main
status = {
    "timestamp": datetime.now().strftime("%H:%M:%S"),
    "symbols": {}
}

for sym in SYMBOLS:
    try:
        result = analyze_symbol(sym)
        status["symbols"][sym] = result
    except Exception as e:
        status["symbols"][sym] = {"symbol": sym, "error": str(e)}

# Best candidate
best = None
for sym, data in status["symbols"].items():
    if data.get("entry") and not data.get("error"):
        best = sym
        status["best_entry"] = sym
        status["entry"] = data["entry"]
        status["entry"]["symbol"] = sym
        status["entry"]["price"] = data["price"]
        status["entry"]["rsi"] = data["rsi"]
        break

# Atomic write
tmp = os.fspath(STATUS_FILE) + ".tmp"
with open(tmp, 'w') as f:
    json.dump(status, f, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.rename(tmp, STATUS_FILE)

# Print summary
print(f"[{status['timestamp']}] Multi-check:", flush=True)
for sym, data in status["symbols"].items():
    if data.get("error"):
        print(f"  {sym}: ❌ {data['error']}", flush=True)
    else:
        e = "✅" if data.get("entry") else "⏳"
        print(f"  {sym}: ${data['price']} RSI:{data['rsi']} Pos:{data['pos_pct']}% HL:{data['hl']} BC:{data['bc']} {e}", flush=True)

if best:
    ed = status["entry"]
    print(f"\n⚡ BEST ENTRY: {best} | {ed['shares']}sh @ ${ed['price']} | R:R {ed['rr1']} | Risk ${ed['risk_usd']}", flush=True)
else:
    print("\n⏳ No hay entrada. Monitoreando...", flush=True)
