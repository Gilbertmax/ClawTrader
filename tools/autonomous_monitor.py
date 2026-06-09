#!/usr/bin/env python3
"""
Monitor autónomo de trading — ClawTrader
Monitorea MSFT en 1m, detecta condiciones de entrada y ejecuta via Alpaca.
Escribe estado en /tmp/clawtrader_status.json (atómico).
Usa yfinance como fuente de datos.
"""
import yfinance as yf
import json, os, time, sys
import requests as r
from datetime import datetime
from load_env import env_bool, env_float, load_env, status_dir

load_env()

# === CONFIG ===
SYMBOL = "MSFT"
CAPITAL = env_float("CLAWTRADER_CAPITAL", 1000)
RISK_PER_TRADE = 0.005  # 0.5%
STOP_PCT = 0.0085  # 0.85%
RR_MIN = 1.5
STATUS_FILE = status_dir() / "clawtrader_status.json"
TRADE_FILE = status_dir() / "clawtrader_trade.json"
PID_FILE = status_dir() / "clawtrader_pid.txt"
DRY_RUN = env_bool("CLAWTRADER_DRY_RUN", True)
LIVE_TRADING = env_bool("CLAWTRADER_LIVE_TRADING", False)

# Alpaca credentials — leídas de variables de entorno
ALPACA_KEY = os.environ.get("ALPACA_API_KEY", "NOT_SET")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET_KEY", "NOT_SET")
ALPACA_BASE = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
ALPACA_HEADERS = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}

def atomic_write(path, data):
    path = os.fspath(path)
    tmp = path + ".tmp"
    with open(tmp, 'w') as f:
        json.dump(data, f)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, path)

def get_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta.where(delta < 0, 0.0))
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return float(rs.iloc[-1])

def check_msft():
    """Analiza MSFT 1m y retorna dict con estado y señal"""
    msft = yf.Ticker(SYMBOL)
    df = msft.history(period='1d', interval='1m')
    
    result = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "symbol": SYMBOL
    }
    
    if df.empty or len(df) < 20:
        result["error"] = f"insufficient_data: {len(df) if not df.empty else 0}"
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
    
    # Higher low (ultimas 5 velas)
    lows_5 = [float(x) for x in df['Low'].tail(5).values]
    higher_low = bool(lows_5[-1] > min(lows_5[:-1]))
    
    # Vela alcista
    last_candle = df.iloc[-1]
    bullish_candle = bool(float(last_candle['Close']) >= float(last_candle['Open']))
    body = round(abs(float(last_candle['Close']) - float(last_candle['Open'])), 2)
    
    # Ultimas 3 velas consecutivas alcistas
    last3 = df.tail(3)
    bullish_3 = sum(1 for i in range(3) if float(last3.iloc[i]['Close']) >= float(last3.iloc[i]['Open']))
    
    # Evaluar entrada
    entry = None
    conditions_met = {
        "pos_pct_ok": pos_pct <= 45,
        "rsi_ok": rsi >= 30,
        "higher_low": higher_low,
        "bullish_candle": bullish_candle,
        "bullish_3": bullish_3 >= 2
    }
    
    all_met = all(conditions_met.values())
    partial = sum(1 for v in conditions_met.values() if v)
    
    if all_met and body >= 0.05:
        # Calcular tamaño
        stop_price = round(current * (1 - STOP_PCT), 2)
        risk_per_share = current - stop_price
        position_size = int((CAPITAL * RISK_PER_TRADE) / risk_per_share)
        position_size = max(1, min(position_size, 100))  # Limitar a 100 shares
        
        target1 = round(current + risk_per_share * 1.5, 2)
        target2 = round(current + risk_per_share * 2.5, 2)
        rr1 = round((target1 - current) / risk_per_share, 2)
        rr2 = round((target2 - current) / risk_per_share, 2)
        
        entry = {
            "signal": "ENTRADA",
            "price": current,
            "shares": position_size,
            "risk_amount": round(position_size * risk_per_share, 2),
            "stop": stop_price,
            "target1": target1,
            "target2": target2,
            "rr1": rr1,
            "rr2": rr2,
            "capital_after": round(CAPITAL - position_size * current, 2)
        }
    
    result.update({
        "price": current,
        "rsi": rsi,
        "pos_pct": pos_pct,
        "low_day": low_day,
        "high_day": high_day,
        "ema9": ema9,
        "ema21": ema21,
        "higher_low": higher_low,
        "bullish_candle": bullish_candle,
        "bullish_3": bullish_3,
        "body": body,
        "conditions": conditions_met,
        "conditions_met": partial,
        "conditions_total": 5,
        "entry": entry
    })
    
    return result

def alpaca_account():
    """Obtiene estado de cuenta Alpaca"""
    if ALPACA_KEY == "NOT_SET" or ALPACA_SECRET == "NOT_SET":
        return None
    try:
        resp = r.get(f"{ALPACA_BASE}/account", headers=ALPACA_HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None

def alpaca_positions():
    if ALPACA_KEY == "NOT_SET" or ALPACA_SECRET == "NOT_SET":
        return []
    try:
        resp = r.get(f"{ALPACA_BASE}/positions", headers=ALPACA_HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def alpaca_orders():
    if ALPACA_KEY == "NOT_SET" or ALPACA_SECRET == "NOT_SET":
        return []
    try:
        resp = r.get(f"{ALPACA_BASE}/orders", params={"status": "open"}, headers=ALPACA_HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return []
    except:
        return []

def execute_trade(entry):
    """Ejecuta bracket order en Alpaca"""
    order = {
        "symbol": SYMBOL,
        "qty": str(entry["shares"]),
        "side": "buy",
        "type": "limit",
        "limit_price": str(entry["price"]),
        "time_in_force": "day",
        "order_class": "bracket",
        "take_profit": {"limit_price": str(entry["target1"])},
        "stop_loss": {"stop_price": str(entry["stop"]), "limit_price": str(round(entry["stop"] * 0.99, 2))}
    }
    
    try:
        if DRY_RUN or not LIVE_TRADING:
            return {"dry_run": True, "order": order}
        resp = r.post(f"{ALPACA_BASE}/orders", headers=ALPACA_HEADERS, json=order, timeout=15)
        if resp.status_code in (200, 201):
            return resp.json()
        else:
            return {"error": resp.text[:300], "status": resp.status_code}
    except Exception as e:
        return {"error": str(e)}

def main():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ClawTrader Monitor iniciado - PID: {os.getpid()}", file=sys.stderr, flush=True)
    
    ciclo = 0
    trade_executed_this_session = False
    
    while True:
        try:
            # 1. Verificar posiciones existentes
            account = alpaca_account()
            positions = alpaca_positions()
            orders = alpaca_orders()
            
            has_position = len(positions) > 0
            has_orders = len(orders) > 0
            
            # 2. Analizar mercado
            analysis = check_msft()
            
            # 3. Incluir estado de cuenta
            if account:
                analysis["account"] = {
                    "equity": round(float(account.get("equity", 0)), 2),
                    "cash": round(float(account.get("cash", 0)), 2),
                    "status": account.get("status"),
                    "has_position": has_position,
                    "has_orders": has_orders
                }
            
            # 4. Si hay entrada Y no hay posiciones/ordenes activas Y no se ejecuto trade aun
            if analysis.get("entry") and not has_position and not has_orders and not trade_executed_this_session:
                entry = analysis["entry"]
                print(f"[{analysis['timestamp']}] ⚡ ENTRADA DETECTADA! Ejecutando MSFT {entry['shares']}sh @ ${entry['price']}...", file=sys.stderr, flush=True)
                
                result = execute_trade(entry)
                analysis["execution"] = result
                
                if "error" not in result:
                    trade_executed_this_session = True
                    analysis["trade_status"] = "EXECUTED"
                    print(f"[{analysis['timestamp']}] ✅ ORDEN EJECUTADA: {result.get('id', 'N/A')}", file=sys.stderr, flush=True)
                else:
                    analysis["trade_status"] = "FAILED"
                    print(f"[{analysis['timestamp']}] ❌ ORDEN FALLIDA: {result['error']}", file=sys.stderr, flush=True)
            
            # 5. Si hay posicion activa, monitorear PnL
            if has_position:
                for pos in positions:
                    pnl = float(pos.get("unrealized_pl", 0))
                    pnl_pct = float(pos.get("unrealized_plpc", 0)) * 100
                    analysis["active_position"] = {
                        "symbol": pos["symbol"],
                        "qty": pos["qty"],
                        "entry": pos["avg_entry_price"],
                        "current": pos["current_price"],
                        "pnl": round(pnl, 2),
                        "pnl_pct": round(pnl_pct, 2),
                        "value": round(float(pos["market_value"]), 2)
                    }
            
            # 6. Escribir status
            atomic_write(STATUS_FILE, analysis)
            
            ciclo += 1
            if ciclo % 5 == 0:
                print(f"[{analysis['timestamp']}] MSFT ${analysis['price']} | RSI {analysis['rsi']} | Señal: {'ENTRADA' if analysis.get('entry') else 'ESPERA'} | Ciclo {ciclo}", file=sys.stderr, flush=True)
            
            time.sleep(60)
            
        except Exception as e:
            print(f"ERROR CRITICO: {e}", file=sys.stderr, flush=True)
            atomic_write(STATUS_FILE, {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "error": str(e),
                "symbol": SYMBOL
            })
            time.sleep(60)

if __name__ == "__main__":
    main()
