#!/usr/bin/env python3
"""
check_crypto.py — Analiza SOL, BTC, ETH, BNB en Binance.
Ejecuta entradas automáticas si hay señal.
Escribe estado en /tmp/clawtrader_crypto.json
"""
import requests as r, json, os, hmac, hashlib, time
from datetime import datetime
from load_env import load_env, status_dir

load_env()

BINANCE_API = "https://api.binance.com"
SYMBOLS = [
    {"sym": "SOLUSDT", "name": "SOL/USDT", "active": True, "min_qty": 0.01},
    {"sym": "BTCUSDT", "name": "BTC/USDT", "active": True, "min_qty": 0.00001},
    {"sym": "ETHUSDT", "name": "ETH/USDT", "active": True, "min_qty": 0.0001},
    {"sym": "BNBUSDT", "name": "BNB/USDT", "active": True, "min_qty": 0.001}
]
RISK_PCT = 0.05  # 5% por trade en crypto (con $1.36)
STATUS_FILE = status_dir() / "clawtrader_crypto.json"

API_KEY = os.environ.get("BINANCE_API_KEY", "NOT_SET")
SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "NOT_SET")
HEADERS = {"X-MBX-APIKEY": API_KEY}

def get_account_balance():
    if API_KEY == "NOT_SET" or SECRET_KEY == "NOT_SET":
        return {}
    params = {"timestamp": int(time.time() * 1000), "omitZeroBalances": "true"}
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    sig = hmac.new(SECRET_KEY.encode(), query.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    resp = r.get(f"{BINANCE_API}/api/v3/account", headers=HEADERS, params=params, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        balances = {}
        for b in data["balances"]:
            free = float(b["free"])
            locked = float(b["locked"])
            if free + locked > 0:
                balances[b["asset"]] = {"free": free, "locked": locked}
        return balances
    return {}

def get_rsi(closes, period=14):
    if len(closes) <= period:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100
    return 100 - (100 / (1 + avg_gain / avg_loss))

def analyze_sol(sym_info, balance_usdt):
    sym = sym_info["sym"]
    resp = r.get(f"{BINANCE_API}/api/v3/klines", params={"symbol": sym, "interval": "15m", "limit": 96}, timeout=10)
    if resp.status_code != 200:
        return {"symbol": sym, "error": f"API: {resp.status_code}"}
    
    data = resp.json()
    closes = [float(k[4]) for k in data]
    current = closes[-1]
    
    rsi_val = round(get_rsi(closes), 1)
    
    high24 = max(float(k[2]) for k in data)
    low24 = min(float(k[3]) for k in data)
    pos_pct = (current - low24) / (high24 - low24) * 100 if high24 > low24 else 50
    
    ema9 = sum(closes[-9:]) / 9
    above_ema9 = current > ema9
    
    # Estructura
    last5 = [float(k[4]) for k in data[-5:]]
    hl = last5[-1] > min(last5[:-1])
    
    last_k = data[-1]
    bc = float(last_k[4]) >= float(last_k[1])
    
    last3 = data[-3:]
    bc3 = sum(1 for k in last3 if float(k[4]) >= float(k[1]))
    
    # Condiciones
    pos_ok = pos_pct <= 60
    rsi_ok = rsi_val >= 25 and rsi_val <= 65
    hl_ok = hl
    bc_ok = bc
    
    result = {
        "symbol": sym_info["name"],
        "price": round(current, 2),
        "rsi": rsi_val,
        "pos_pct": round(pos_pct, 1),
        "ema9": round(ema9, 2),
        "above_ema9": above_ema9,
        "hl": hl_ok,
        "bc": bc_ok,
        "bc3": bc3,
        "conditions": {
            "pos_ok": bool(pos_ok),
            "rsi_ok": bool(rsi_ok),
            "hl_ok": bool(hl_ok),
            "bc_ok": bool(bc_ok)
        }
    }
    
    if all([pos_ok, rsi_ok, hl_ok, bc_ok]):
        # Calcular compra con ~50% del balance
        invest = balance_usdt * 0.5
        qty_raw = invest / current
        # Redondear a cantidad minima
        qty = max(sym_info["min_qty"], round(qty_raw, 4))
        
        stop_pct = 0.015  # 1.5% stop en crypto (mas ajustado)
        stop_price = round(current * (1 - stop_pct), 2)
        t1_price = round(current * 1.025, 2)  # 2.5% target mas rapido
        rr = round((t1_price - current) / (current - stop_price), 2)
        
        result["entry"] = {
            "signal": "ENTRADA",
            "exchange": "binance",
            "symbol": sym,
            "qty": qty,
            "invest_usd": round(qty * current, 2),
            "price": round(current, 2),
            "stop": stop_price,
            "target1": t1_price,
            "rr": rr
        }
    
    return result

# === MAIN ===
balance = get_account_balance()
usdt_free = balance.get("USDT", {}).get("free", 0)
print(f"[{datetime.now().strftime('%H:%M:%S')}] Balance USDT: ${usdt_free}", flush=True)

results = {"timestamp": datetime.now().strftime("%H:%M:%S"), "symbols": {}}
best_entry = None

for sym_info in SYMBOLS:
    res = analyze_sol(sym_info, usdt_free)
    results["symbols"][sym_info["sym"]] = res
    
    label = res.get("symbol", sym_info["sym"])
    if "error" in res:
        print(f"  {label}: ❌ {res['error']}", flush=True)
    else:
        entry_str = "✅" if res.get("entry") else "⏳"
        print(f"  {label}: ${res['price']} RSI:{res['rsi']} Pos:{res['pos_pct']}% HL:{res['hl']} BC:{res['bc']} {entry_str}", flush=True)
        if res.get("entry") and not best_entry:
            best_entry = res["entry"]
            results["entry"] = best_entry

results["balance"] = {"USDT": usdt_free}

if best_entry:
    print(f"\n⚡ ENTRADA DETECTADA: {best_entry['symbol']} | {best_entry['qty']} @ ${best_entry['price']} | Stop ${best_entry['stop']} | R:R {best_entry['rr']}", flush=True)
else:
    print(f"\n⏳ Sin entrada. Esperando condiciones...", flush=True)

# Atomic write
tmp = os.fspath(STATUS_FILE) + ".tmp"
with open(tmp, 'w') as f:
    json.dump(results, f, indent=2)
    f.flush()
    os.fsync(f.fileno())
os.rename(tmp, STATUS_FILE)
