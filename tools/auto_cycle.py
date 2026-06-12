#!/usr/bin/env python3
"""
Auto Cycle — Cerebro autónomo completo.
Cada ejecución:
  1. Corre scanner (o usa último resultado)
  2. Si hay señal ≥11/16 con BTC cooperando:
     a. Verifica Order Book + BOS (Smart Money)
     b. Si pasa filtros → ejecuta compra en Binance
     c. Configura SL/TP en el engine
  3. Si hay posiciones abiertas → revisa trailing/SL/TP (con venta real)
  4. Reporta estado

USO: python3 tools/auto_cycle.py

Diseñado para correr cada 5 min vía cron.
"""

import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
import hmac
import hashlib
from pathlib import Path

from load_env import env_bool, load_env, status_dir

load_env()

# Cache de símbolos válidos en Binance (se carga una vez)
_VALID_SYMBOLS = None

def get_valid_symbols():
    """Carga lista de símbolos disponibles en Binance spot."""
    global _VALID_SYMBOLS
    if _VALID_SYMBOLS is not None:
        return _VALID_SYMBOLS
    try:
        info = binance_request("GET", "/api/v3/exchangeInfo")
        _VALID_SYMBOLS = {s["symbol"] for s in info["symbols"] if s["status"] == "TRADING" and s["symbol"].endswith("USDT")}
        return _VALID_SYMBOLS
    except:
        return set()
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

ENGINE_FILE = Path(os.environ.get("CLAWTRADER_ENGINE_FILE", status_dir() / "live_engine_state.json"))
ENGINE_PID_FILE = Path(os.environ.get("CLAWTRADER_LIVE_PID_FILE", status_dir() / "live_engine.pid"))
REPORT_FILE = Path(os.environ.get("CLAWTRADER_AUTO_CYCLE_REPORT", status_dir() / "auto_cycle_report.txt"))

STABLECOINS = {"USDC","USDT","BUSD","DAI","TUSD","FDUSD","PAXG","USTC"}

# ============================================================
# HELPERS
# ============================================================

def get_price(sym):
    with urllib.request.urlopen(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=5) as r:
        return float(json.load(r)["price"])

def get_api_keys():
    load_env()
    return os.environ.get("BINANCE_API_KEY"), os.environ.get("BINANCE_SECRET_KEY")

def live_trading_enabled():
    load_env()
    return env_bool("CLAWTRADER_LIVE_TRADING", False) and not env_bool("CLAWTRADER_DRY_RUN", True)

def blocked_live_action(action):
    return {
        "success": False,
        "dry_run": True,
        "error": (
            f"{action} bloqueada: activa CLAWTRADER_LIVE_TRADING=true "
            "y CLAWTRADER_DRY_RUN=false para permitir ordenes reales"
        ),
    }

def binance_request(method, path, params=None, sign=False):
    """Helper para requests autenticados a Binance."""
    base = "https://api.binance.com"
    if params is None:
        params = {}
    if sign:
        api_key, secret_key = get_api_keys()
        if not api_key or not secret_key:
            raise RuntimeError("BINANCE_API_KEY y BINANCE_SECRET_KEY son requeridas")
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 5000
        qs = urllib.parse.urlencode(sorted(params.items()))
        sig = hmac.new(secret_key.encode(), qs.encode(), hashlib.sha256).hexdigest()
        url = f"{base}{path}?{qs}&signature={sig}"
        headers = {"X-MBX-APIKEY": api_key}
        data = b"" if method == "POST" else None
    else:
        qs = urllib.parse.urlencode(params) if params else ""
        url = f"{base}{path}?{qs}" if qs else f"{base}{path}"
        headers = {}
        data = None

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)

def get_balances():
    """Devuelve dict {asset: free} de Binance."""
    acc = binance_request("GET", "/api/v3/account", sign=True)
    result = {}
    for b in acc["balances"]:
        free = float(b["free"])
        locked = float(b["locked"])
        if free > 0 or locked > 0:
            result[b["asset"]] = {"free": free, "locked": locked}
    return result

def get_usdt_balance():
    bal = get_balances()
    return bal.get("USDT", {}).get("free", 0)

def get_symbol_filters(sym):
    info = binance_request("GET", "/api/v3/exchangeInfo", params={"symbol": sym})
    filters = info["symbols"][0]["filters"]
    step = 0.001
    min_qty = 0.001
    min_notional = 5.0
    for f in filters:
        if f["filterType"] == "LOT_SIZE":
            step = float(f["stepSize"])
            min_qty = float(f["minQty"])
        if f["filterType"] == "NOTIONAL":
            min_notional = float(f["minNotional"])
    return step, min_qty, min_notional

def execute_buy(sym, size_usdt):
    """Compra real en Binance."""
    try:
        if not live_trading_enabled():
            return blocked_live_action("Compra real")
        px = get_price(sym)
        step, min_qty, min_notional = get_symbol_filters(sym)

        # Calcular qty mínima que cumpla AMBAS reglas (LOT_SIZE y NOTIONAL)
        qty_needed = max(min_qty, min_notional / px)
        # Redondear hacia arriba al step más cercano
        qty = math.ceil(qty_needed / step) * step
        # Ajustar decimales para evitar floats sucios
        qty = round(qty, 10)

        # El costo real
        actual_cost = qty * px

        if size_usdt < actual_cost and size_usdt < min_notional:
            return {"success": False, "error": f"Se necesitan al menos ${actual_cost:.2f} USDT para este par"}

        # Usar quoteOrderQty si el tamaño alcanza
        qs = size_usdt / px
        if qs < qty:
            qs = qty
        qs = math.floor(qs / step) * step
        if qs < min_qty:
            qs = min_qty

        # Serializar quantity como string fijo (sin notación científica)
        qty_str = f"{qs:.10f}".rstrip("0").rstrip(".")
        if qty_str == "0":
            return {"success": False, "error": "Cantidad cero después de ajustes"}

        result = binance_request("POST", "/api/v3/order", {
            "symbol": sym, "side": "BUY", "type": "MARKET",
            "quantity": qty_str
        }, sign=True)

        exec_qty = float(result.get("executedQty", 0))
        cum_quote = float(result.get("cummulativeQuoteQty", 0))
        return {"success": True, "filled_qty": exec_qty, "spent_usdt": cum_quote, "price": cum_quote / exec_qty if exec_qty else px}
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_sell(sym, qty=None):
    """Vende en Binance. Si qty es None, vende todo."""
    try:
        if not live_trading_enabled():
            return blocked_live_action("Venta real")
        if qty is None:
            bal = get_balances()
            asset = sym.replace("USDT", "")
            qty = bal.get(asset, {}).get("free", 0)
            if qty <= 0:
                return {"success": False, "error": "No balance"}
        step, min_qty, _ = get_symbol_filters(sym)
        qty = math.floor(qty / step) * step
        if qty < min_qty:
            return {"success": False, "error": f"Cantidad mínima {min_qty}"}
        qty = round(qty, 10)
        qty_str = f"{qty:.10f}".rstrip("0").rstrip(".")
        if qty_str == "0":
            return {"success": False, "error": "Cantidad cero"}

        result = binance_request("POST", "/api/v3/order", {
            "symbol": sym, "side": "SELL", "type": "MARKET",
            "quantity": qty_str
        }, sign=True)
        return {"success": True, "raw": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# ENGINE STATE
# ============================================================

def load_engine():
    if ENGINE_FILE.exists():
        with open(ENGINE_FILE) as f:
            return json.load(f)
    return {"running": False, "positions": {}, "trailing": {}, "history": []}

def save_engine(state):
    ENGINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENGINE_FILE, "w") as f:
        json.dump(state, f, indent=2)

# ============================================================
# SMART MONEY CHECK
# ============================================================

def get_orderbook(sym, limit=100):
    """Order Book imbalance. Retorna imbalance ratio (bid/ask)."""
    try:
        ob = binance_request("GET", "/api/v3/depth", params={"symbol": sym, "limit": limit})
        bid_vol = sum(float(b[1]) for b in ob["bids"][:10])
        ask_vol = sum(float(a[1]) for a in ob["asks"][:10])
        ratio = bid_vol / ask_vol if ask_vol > 0 else 0
        return {"bid_vol": bid_vol, "ask_vol": ask_vol, "imbalance": round(ratio, 2)}
    except:
        return None

def detect_bos(sym):
    """Detecta Break of Structure simple en 1h."""
    try:
        kl = binance_request("GET", "/api/v3/klines", params={"symbol": sym, "interval": "1h", "limit": 20})
        highs = [float(k[2]) for k in kl]
        lows = [float(k[3]) for k in kl]
        closes = [float(k[4]) for k in kl]
        # BOS alcista: último cierre > máximo de los últimos 8 excepto el actual
        recent_high = max(highs[-9:-1]) if len(highs) >= 9 else max(highs[:-1])
        bos_up = closes[-1] > recent_high
        # BOS bajista: último cierre < mínimo de los últimos 8
        recent_low = min(lows[-9:-1]) if len(lows) >= 9 else min(lows[:-1])
        bos_down = closes[-1] < recent_low
        return {"bos_up": bos_up, "bos_down": bos_down, "recent_high": recent_high, "recent_low": recent_low}
    except:
        return None

def smart_money_check(sym):
    """Filtro Smart Money completo. Retorna dict con veredicto."""
    ob = get_orderbook(sym)
    bos = detect_bos(sym)

    result = {"imbalance": None, "bos_up": False, "bos_down": False, "veredicto": "NEUTRAL"}

    if ob:
        result["imbalance"] = ob["imbalance"]
    if bos:
        result["bos_up"] = bos["bos_up"]
        result["bos_down"] = bos["bos_down"]

    # Veredicto
    alcista_score = 0
    if ob and ob["imbalance"] > 1.3:
        alcista_score += 1  # presión compradora
    if ob and ob["imbalance"] > 1.8:
        alcista_score += 1  # presión fuerte
    if bos and bos["bos_up"]:
        alcista_score += 2  # BOS alcista
    if bos and bos["bos_down"]:
        alcista_score -= 2  # BOS bajista anula

    if alcista_score >= 2:
        result["veredicto"] = "ALCISTA"
    elif alcista_score <= -1:
        result["veredicto"] = "BAJISTA"
    else:
        result["veredicto"] = "NEUTRAL"

    return result

# ============================================================
# TRADING ENGINE
# ============================================================

def check_current_positions():
    """Revisa posiciones existentes: SL, TP, trailing, y ejecuta ventas reales."""
    state = load_engine()
    alerts = []

    for sym in list(state.get("positions", {}).keys()):
        p = state["positions"][sym]
        try:
            px = get_price(sym)
        except:
            continue

        entry = p["entry"]
        sl = p.get("sl")
        tp_orig = p.get("tp")
        gain_pct = (px - entry) / entry * 100
        action = "HOLDING"

        # SL fijo
        if sl and px <= sl:
            sell_r = execute_sell(sym)
            trade = close_pos_in_state(sym, px, "SL_HIT", state)
            alerts.append({"sym": sym, "action": "SL_HIT", "pnl": trade["pnl_usdt"] if trade else 0, "real_sold": sell_r.get("success", False)})
            continue

        # TP fijo
        if tp_orig and px >= tp_orig:
            sell_r = execute_sell(sym)
            trade = close_pos_in_state(sym, px, "TP_HIT", state)
            alerts.append({"sym": sym, "action": "TP_HIT", "pnl": trade["pnl_usdt"] if trade else 0, "real_sold": sell_r.get("success", False)})
            continue

        # Trailing
        tp_gain_pct = (tp_orig - entry) / entry * 100 if tp_orig else 3.0
        activation_pct = tp_gain_pct * 0.5

        if gain_pct >= activation_pct and not p.get("trail_activated"):
            p["trail_activated"] = True
            p["trail_current_stop"] = entry + (px - entry) * 0.3
            alerts.append({"sym": sym, "action": "TRAIL_ACTIVATED", "stop": p["trail_current_stop"]})

        elif p.get("trail_activated"):
            new_stop = px * 0.97
            if new_stop > p.get("trail_current_stop", 0):
                p["trail_current_stop"] = new_stop

            if px <= p.get("trail_current_stop", 0):
                sell_r = execute_sell(sym)
                trade = close_pos_in_state(sym, px, "TRAIL_STOPPED", state)
                alerts.append({"sym": sym, "action": "TRAIL_STOPPED", "pnl": trade["pnl_usdt"] if trade else 0, "real_sold": sell_r.get("success", False)})
                continue

        # Actualizar precio actual
        p["current_price"] = px
        p["pnl_pct"] = round(gain_pct, 2)

    save_engine(state)
    return alerts

def close_pos_in_state(sym, exit_price, reason, state):
    """Cierra posición en estado y registra trade."""
    if sym not in state["positions"]:
        return None
    p = state["positions"][sym]
    pnl_pct = (exit_price - p["entry"]) / p["entry"] * 100
    pnl_usdt = pnl_pct / 100 * p["size_usdt"]

    trade = {
        "sym": sym.replace("USDT", ""),
        "type": "COMPRA",
        "entry": p["entry"],
        "exit": exit_price,
        "size_usdt": p["size_usdt"],
        "pnl_pct": round(pnl_pct, 2),
        "pnl_usdt": round(pnl_usdt, 4),
        "score": p.get("score", 0),
        "tp": p.get("tp"),
        "sl": p.get("sl"),
        "trail_activated": p.get("trail_activated", False),
        "opened_at": p.get("opened_at", 0),
        "closed_at": time.time(),
        "result": "WIN" if pnl_usdt > 0 else "LOSS",
        "reason": reason
    }
    state["history"].append(trade)
    del state["positions"][sym]
    return trade

# ============================================================
# SCANNER + ENTRY LOGIC
# ============================================================

def run_scanner():
    """Ejecuta el scanner y devuelve resultados."""
    import subprocess
    result = subprocess.run(
        ["python3", os.path.join(BASE, "market_scanner.py")],
        capture_output=True, text=True, timeout=90
    )
    if result.returncode != 0:
        # Intentar leer último output
        for line in result.stderr.split("\n"):
            if "BTC:" in line:
                print(f"[AUTO] Scanner stderr: {line.strip()}")
        return None

    try:
        data = json.loads(result.stdout.strip().split("\n")[-1])
        return data
    except:
        return None

def find_new_entry(scanner_data):
    """
    Busca la mejor señal del scanner y decide si entrar.
    Retorna dict con decisión o None.
    """
    if not live_trading_enabled():
        print("[AUTO] Live trading desactivado; no se buscaran entradas reales.")
        return None

    if not scanner_data:
        return None

    btc_trend = scanner_data.get("btc", {}).get("trend", "BEARISH")
    btc_factor = scanner_data.get("btc_factor", 0.6)
    best = scanner_data.get("best")
    scores = scanner_data.get("scores", {})

    # Si no hay best o score insuficiente
    if not best or best.get("sco", 0) < 11:
        return None

    # Validar que el símbolo exista en Binance
    valid_syms = get_valid_symbols()
    sym = best["s"] + "USDT"
    if sym not in valid_syms:
        print(f"[AUTO] ⚠️ {sym} no existe en Binance spot, saltando")
        return None

    # Si BTC está bajista, solo considerar scores >= 13
    min_score = 13 if btc_trend == "BEARISH" else 11
    if btc_trend == "SIDEWAYS":
        min_score = 11

    score = best["sco"]

    if score < min_score:
        return None

    # Smart Money check
    sm = smart_money_check(sym)
    force_enter = False

    if sm["veredicto"] == "ALCISTA":
        force_enter = True
    elif sm["veredicto"] == "BAJISTA":
        return None  # Smart Money dice no
    # NEUTRAL: ok si score alto

    # VWAP check (si disponible)
    vwap = best.get("vwap")
    price = best.get("p", 0)
    if vwap and price > vwap * 1.03:
        # Precio >3% sobre VWAP = caro, no entrar
        if not force_enter:
            return None

    # Calcular tamaño de posición
    usdt_balance = get_usdt_balance()
    if usdt_balance < 5:
        return None

    # Tamaño según score y BTC
    if score >= 14:
        size_pct = 0.60
    elif score >= 12:
        size_pct = 0.45
    elif score >= 11:
        size_pct = 0.35
    else:
        size_pct = 0.25

    size_pct *= btc_factor
    size_usdt = usdt_balance * size_pct
    size_usdt = min(size_usdt, usdt_balance * 0.85)  # max 85%

    # Ajustar al mínimo notional
    _, _, min_notional = get_symbol_filters(sym)
    if size_usdt < min_notional:
        size_usdt = min_notional

    return {
        "sym": sym,
        "name": best["s"],
        "score": score,
        "price": price,
        "size_usdt": round(size_usdt, 2),
        "smart_money": sm,
        "entry_type": "autonomous",
        "btc_trend": btc_trend
    }

# ============================================================
# MAIN CYCLE
# ============================================================

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 Auto Cycle iniciado")
    results = []

    # 1. Revisar posiciones existentes primero
    print("[AUTO] Revisando posiciones activas...")
    pos_alerts = check_current_positions()
    for a in pos_alerts:
        sym = a.get("sym", "?")
        act = a.get("action", "?")
        if act in ("TRAIL_STOPPED", "SL_HIT", "TP_HIT"):
            pnl = a.get("pnl", 0)
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            sold = "✅" if a.get("real_sold") else "⚠️"
            print(f"  {sold} {sym}: CERRADO ({act}) | P&L: {pnl_str}")
            results.append(f"🔴 {sym} cerrado por {act}: {pnl_str}")
        elif act == "TRAIL_ACTIVATED":
            stop = a.get("stop", 0)
            print(f"  🔁 {sym}: Trailing activado (stop ${stop:.4f})")
            results.append(f"🔁 {sym}: Trailing activado")
        else:
            print(f"  {sym}: {act}")

    # 2. Buscar nuevas entradas
    print("[AUTO] Ejecutando scanner...")
    scanner_data = run_scanner()
    if scanner_data:
        btc = scanner_data.get("btc", {})
        print(f"  BTC: ${btc.get('p',0):,.0f} | {btc.get('trend','?')}")
        best = scanner_data.get("best", {})
        if best:
            print(f"  Mejor: {best.get('s','?')} score={best.get('sco',0)}")

        entry = find_new_entry(scanner_data)
        if entry:
            print(f"\n[AUTO] 🎯 Señal detectada: {entry['name']} (score {entry['score']}/16)")
            sm = entry["smart_money"]
            print(f"  Smart Money: {sm['veredicto']} (imbalance: {sm.get('imbalance','?')})")
            print(f"  Size: ${entry['size_usdt']} | BTC: {entry['btc_trend']}")

            # Ejecutar compra
            buy_r = execute_buy(entry["sym"], entry["size_usdt"])
            if buy_r["success"]:
                filled_qty = buy_r.get("filled_qty", 0)
                avg_price = buy_r.get("price", entry["price"])
                spent = buy_r.get("spent_usdt", entry["size_usdt"])

                # Calcular SL/TP
                sl_pct = 0.05 if entry["btc_trend"] == "BEARISH" else 0.04
                tp_pct = 0.05 if entry["btc_trend"] == "BEARISH" else 0.07

                sl_price = avg_price * (1 - sl_pct)
                tp_price = avg_price * (1 + tp_pct)

                # Registrar en engine
                state = load_engine()
                state["positions"][entry["sym"]] = {
                    "entry": avg_price,
                    "size_usdt": spent,
                    "tp": tp_price,
                    "sl": sl_price,
                    "score": entry["score"],
                    "trail_activated": False,
                    "trail_current_stop": sl_price,
                    "opened_at": time.time(),
                    "size_qty": filled_qty
                }
                save_engine(state)

                msg = f"✅ COMPRADO {entry['name']} a ${avg_price:.4f} | ${spent:.2f} | SL ${sl_price:.4f} TP ${tp_price:.4f}"
                print(f"\n[AUTO] {msg}")
                results.append(msg)
            else:
                err = buy_r.get("error", "desconocido")
                print(f"\n[AUTO] ❌ Error compra: {err}")
                results.append(f"⚠️ Señal {entry['name']} rechazada (error: {err})")
        else:
            print("[AUTO] Sin señales válidas en este ciclo")
    else:
        print("[AUTO] Scanner no disponible")

    # 3. Estado final
    state = load_engine()
    bal = get_usdt_balance() if live_trading_enabled() else 0
    positions = state.get("positions", {})
    print(f"\n[AUTO] 💰 Balance: ${bal:.2f} | Posiciones: {len(positions)}")
    for s, p in positions.items():
        try:
            px = get_price(s)
            pnl = (px - p["entry"]) / p["entry"] * 100
            print(f"  {s}: ${p['entry']:.4f} → ${px:.4f} ({pnl:+.2f}%) | SL ${p.get('sl',0):.4f} TP ${p.get('tp',0):.4f}")
        except:
            pass

    # Escribir resumen
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w") as f:
        f.write(f"=== Auto Cycle {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
        for r in results:
            f.write(f"{r}\n")
        f.write(f"Balance: ${bal:.2f} | Posiciones: {len(positions)}\n")

    print(f"\n[AUTO] ✅ Ciclo completado en {time.time():.0f}s")

def run_once():
    return main()

if __name__ == "__main__":
    main()
