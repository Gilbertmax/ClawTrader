#!/usr/bin/env python3
"""
Live Engine v1 — WebSocket + Portfolio Manager + Trailing TP
Fase 3 del sistema ClawTrader.

Arquitectura:
  - WebSocket a Binance (stream de precios para símbolos vigilados)
  - Live Trader: recibe ticks, actualiza trailing TP, registra trades
  - Portfolio Manager: diversificación automática según señales

USO:
  python3 tools/live_engine.py start          → Inicia motor en vivo
  python3 tools/live_engine.py stop           → Detiene motor
  python3 tools/live_engine.py status         → Estado actual
  python3 tools/live_engine.py add SYM size   → Añade posición manual
  python3 tools/live_engine.py trail SYM tp%  → Configura trailing TP
"""

import json
import math
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

from load_env import env_bool, env_float, load_env, status_dir

load_env()

ENGINE_FILE = Path(os.environ.get("CLAWTRADER_ENGINE_FILE", status_dir() / "live_engine_state.json"))
ALERT_FILE = Path(os.environ.get("CLAWTRADER_LIVE_ALERT_FILE", status_dir() / "live_alert.txt"))
ERROR_LOG = Path(os.environ.get("CLAWTRADER_LIVE_ERROR_LOG", status_dir() / "live_engine_error.log"))
PID_FILE = Path(os.environ.get("CLAWTRADER_LIVE_PID_FILE", status_dir() / "live_engine.pid"))
MAX_CAPITAL = env_float("CLAWTRADER_CAPITAL", 1000)
MAX_POSITION_PCT = 0.85  # 85% max por trade
PORTFOLIO_LIMIT = 4  # max 4 posiciones simultáneas


def load_engine():
    if ENGINE_FILE.exists():
        with open(ENGINE_FILE) as f:
            return json.load(f)
    return {"running": False, "positions": {}, "trailing": {}, "history": []}


def save_engine(state):
    ENGINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ENGINE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_price(sym):
    with urlopen(f"https://api.binance.com/api/v3/ticker/price?symbol={sym}", timeout=5) as r:
        return float(json.load(r)["price"])


def _api_keys():
    load_env()
    api_key = os.environ.get("BINANCE_API_KEY")
    secret_key = os.environ.get("BINANCE_SECRET_KEY")
    return api_key, secret_key


def _live_trading_enabled():
    load_env()
    return env_bool("CLAWTRADER_LIVE_TRADING", False) and not env_bool("CLAWTRADER_DRY_RUN", True)


def _blocked_live_action(action):
    return {
        "success": False,
        "dry_run": True,
        "error": (
            f"{action} bloqueada: activa CLAWTRADER_LIVE_TRADING=true "
            "y CLAWTRADER_DRY_RUN=false para permitir ordenes reales"
        ),
    }


def get_balance():
    """Obtiene balance USDT de Binance spot via v3/account."""
    try:
        import urllib.request, urllib.parse, hashlib, hmac
        api_key, secret_key = _api_keys()
        if not api_key or not secret_key:
            return None
        ts = int(time.time() * 1000)
        params = {"timestamp": ts, "recvWindow": 5000}
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(secret_key.encode(), qs.encode(), hashlib.sha256).hexdigest()
        req = urllib.request.Request(
            f"https://api.binance.com/api/v3/account?{qs}&signature={sig}",
            headers={"X-MBX-APIKEY": api_key}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            acct = json.load(r)
        for b in acct["balances"]:
            if b["asset"] == "USDT":
                free = float(b["free"])
                locked = float(b["locked"])
                return free + locked
        return 0
    except Exception as e:
        return None


# ========== PORTFOLIO MANAGER ==========

def calc_position_size(score, confidence=1.0):
    """Calcula tamaño de posición según score y confianza."""
    if score >= 14:
        pct = 0.85
    elif score >= 12:
        pct = 0.65
    elif score >= 10:
        pct = 0.45
    elif score >= 8:
        pct = 0.25
    else:
        pct = 0.0
    return pct * confidence


def portfolio_status():
    """Estado del portfolio: posiciones abiertas, balance, SL/TP."""
    state = load_engine()
    positions = state.get("positions", {})
    balance = get_balance()
    total_in_positions = sum(p["size_usdt"] for p in positions.values())

    status = {
        "balance_usdt": balance,
        "in_positions": round(total_in_positions, 2),
        "available": round((balance or 0) - total_in_positions, 2) if balance else 0,
        "open_positions": len(positions),
        "max_positions": PORTFOLIO_LIMIT
    }

    status["positions"] = {}
    for sym, p in positions.items():
        try:
            px = get_price(sym)
            pnl = (px - p["entry"]) / p["entry"] * 100
            status["positions"][sym] = {
                **p,
                "current_price": px,
                "pnl_pct": round(pnl, 2),
                "pnl_usdt": round(pnl / 100 * p["size_usdt"], 2)
            }
        except:
            status["positions"][sym] = {**p, "current_price": None, "pnl_pct": 0, "pnl_usdt": 0}

    return status


def add_position(sym, entry, size_usdt, tp, sl, score):
    """Añade posición al engine."""
    state = load_engine()
    if sym not in state["positions"]:
        state["positions"][sym] = {
            "entry": entry,
            "size_usdt": size_usdt,
            "tp": tp,
            "sl": sl,
            "score": score,
            "trail_activated": False,
            "trail_start_pct": 0,
            "trail_current_stop": sl,
            "highest_price": entry,
            "opened_at": time.time()
        }
        save_engine(state)
        return True
    return False


def close_position(sym, exit_price):
    """Cierra posición y registra trade."""
    state = load_engine()
    if sym not in state["positions"]:
        return False

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
        "score": p["score"],
        "tp": p["tp"],
        "sl": p["sl"],
        "trail_activated": p["trail_activated"],
        "opened_at": p["opened_at"],
        "closed_at": time.time(),
        "result": "WIN" if pnl_usdt > 0 else "LOSS"
    }

    state["history"].append(trade)
    del state["positions"][sym]
    save_engine(state)
    return trade


# ========== TRAILING TP ==========

def update_trailing(sym):
    """
    ESCALERA DE GANANCIAS — Estrategia de proteccion progresiva.
    
    En lugar de un trailing % fijo, protege ganancias por escalones:
    - Si la ganancia llega a $1, el stop sube a entry (nunca perder)
    - Si llega a $2, el stop sube a entry+$1 (asegurar $1)
    - Si llega a $3, el stop sube a entry+$2 (asegurar $2)
    - Y así sucesivamente, cada $1 de ganancia = 1 escalón
    
    Si el precio retrocede un escalón completo, se cierra.
    """
    state = load_engine()
    if sym not in state["positions"]:
        return None

    p = state["positions"][sym]
    try:
        px = get_price(sym)
    except:
        return None

    entry = p["entry"]
    size = p["size_usdt"]
    sl_original = p["sl"]
    tp_original = p["tp"]

    # Actualizar máximo precio alcanzado
    if px > p.get("highest_price", entry):
        p["highest_price"] = px

    highest = p["highest_price"]

    # Ganancia actual y ganancia máxima alcanzada (en dólares)
    gain_usdt = (px - entry) / entry * size
    peak_gain_usdt = (highest - entry) / entry * size

    # ---- ESCALERA DE GANANCIAS ----
    # Escalón mínimo de protección: $0.50 para cuentas pequeñas
    # Un escalón completo = entry + $1 de ganancia
    STEP_USDT = 1.0  # cada $1 es un escalón

    # Calcular escalón actual: cuántos $1 completos de ganancia
    current_step = max(0, int(gain_usdt / STEP_USDT))
    peak_step = max(0, int(peak_gain_usdt / STEP_USDT))

    # El trailing stop sube: protege el escalón anterior
    # Si llegamos a $2 de ganancia (step=2), aseguramos $1 (entry + $1)
    if peak_step >= 1:
        # El stop protege el último escalón alcanzado - 1
        protected_step = peak_step - 1
        trail_stop_price = entry + (protected_step * STEP_USDT / size * entry)
        p["trail_activated"] = True
        p["trail_current_stop"] = trail_stop_price
        
        # Verificar si se rompió el escalón
        if current_step <= protected_step:
            # Si la ganancia actual es menor o igual al escalón protegido
            trade = close_position(sym, px)
            action = "ESCALERA_STOP"
            save_engine(state)
            return {"action": action, "trade": trade}
        
        action = "ESCALERA_HOLDING"
    else:
        # Aún no hay ganancia, usar SL original si existe
        p["trail_current_stop"] = sl_original if sl_original else entry * 0.95
        action = "ESCALERA_INICIO"

    # Verificar SL original por si acaso
    if sl_original and px <= sl_original:
        trade = close_position(sym, px)
        action = "SL_HIT"
        save_engine(state)
        return {"action": action, "trade": trade}
    
    # Verificar TP original
    if tp_original and px >= tp_original:
        p["trail_current_stop"] = tp_original * 0.98  # asegurar casi todo
        save_engine(state)
        # No cerramos TP fijo, dejamos que la escalera decida
        action = "TP_ALCANZADO"

    save_engine(state)
    return {
        "action": action,
        "price": px,
        "entry": entry,
        "gain_usdt": round(gain_usdt, 4),
        "peak_gain_usdt": round(peak_gain_usdt, 4),
        "current_step": current_step,
        "trail_active": p["trail_activated"],
        "trail_stop": round(p.get("trail_current_stop", 0), 6)
    }


# ========== CHECK ALL POSITIONS ==========

def check_all_positions():
    """Revisa todas las posiciones abiertas y actualiza trailing."""
    state = load_engine()
    results = []
    for sym in list(state["positions"].keys()):
        r = update_trailing(sym)
        if r:
            results.append({"sym": sym, **r})
            # Si se cerró por trailing/SL/TP, ejecutar venta REAL en Binance
            if r.get("action") in ("TRAIL_STOPPED", "ESCALERA_STOP", "SL_HIT", "TP_HIT"):
                t = r.get("trade", {})
                if t:
                    sell_result = execute_sell(sym)
                    if sell_result.get("success"):
                        results[-1]["real_sell"] = sell_result
                        results[-1]["real_pnl"] = t.get("pnl_usdt", 0)
                    else:
                        results[-1]["sell_error"] = sell_result.get("error")
    return results


# ========== EJECUCIÓN REAL ==========

def execute_buy(sym, size_usdt):
    """Ejecuta orden de compra en Binance spot a precio de mercado."""
    try:
        import urllib.request, urllib.parse, hashlib, hmac
        if not _live_trading_enabled():
            return _blocked_live_action("Compra real")
        api_key, secret_key = _api_keys()
        if not api_key or not secret_key:
            return {"success": False, "error": "BINANCE_API_KEY y BINANCE_SECRET_KEY son requeridas"}

        px = get_price(sym)
        qty = size_usdt / px

        # Obtener filtros del símbolo
        info_url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={sym}"
        with urlopen(info_url, timeout=5) as r:
            info = json.load(r)
        step = 0.001
        min_notional = 5.0
        for f in info["symbols"][0]["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
            if f["filterType"] == "NOTIONAL":
                min_notional = float(f["minNotional"])

        # Validar mínimo
        if size_usdt < min_notional:
            return {"success": False, "error": f"Mínimo ${min_notional} USDT, pediste ${size_usdt:.2f}"}

        # Calcular cantidad redondeada
        qty = math.floor(qty / step) * step

        ts = int(time.time() * 1000)
        params = {
            "symbol": sym, "side": "BUY", "type": "MARKET",
            "quantity": qty,
            "timestamp": ts, "recvWindow": 5000
        }
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(secret_key.encode(), qs.encode(), hashlib.sha256).hexdigest()
        req = urllib.request.Request(
            f"https://api.binance.com/api/v3/order?{qs}&signature={sig}",
            headers={"X-MBX-APIKEY": api_key},
            method="POST", data=b""
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.load(r)
        fill = float(result["executedQty"])
        spent = sum(float(f["commission"]) for f in result.get("fills", []))
        return {"success": True, "filled_qty": fill, "spent_usdt": spent, "raw": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def execute_sell(sym, qty=None):
    """Ejecuta orden de venta en Binance spot."""
    try:
        import urllib.request, urllib.parse, hashlib, hmac
        if not _live_trading_enabled():
            return _blocked_live_action("Venta real")
        api_key, secret_key = _api_keys()
        if not api_key or not secret_key:
            return {"success": False, "error": "BINANCE_API_KEY y BINANCE_SECRET_KEY son requeridas"}

        if qty is None:
            # Vender toda la posición
            ts = int(time.time() * 1000)
            params = {"timestamp": ts, "recvWindow": 5000}
            qs = urllib.parse.urlencode(params)
            sig = hmac.new(secret_key.encode(), qs.encode(), hashlib.sha256).hexdigest()
            req = urllib.request.Request(
                f"https://api.binance.com/api/v3/account?{qs}&signature={sig}",
                headers={"X-MBX-APIKEY": api_key},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                acct = json.load(r)
            asset = sym.replace("USDT", "")
            for b in acct["balances"]:
                if b["asset"] == asset:
                    qty = float(b["free"])
                    break
            if not qty or qty <= 0:
                return {"success": False, "error": "No balance"}

        # Redondear
        info_url = f"https://api.binance.com/api/v3/exchangeInfo?symbol={sym}"
        with urlopen(info_url, timeout=5) as r:
            info = json.load(r)
        for f in info["symbols"][0]["filters"]:
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
                qty = math.floor(qty / step) * step
                break

        ts = int(time.time() * 1000)
        params = {
            "symbol": sym, "side": "SELL", "type": "MARKET",
            "quantity": qty,
            "timestamp": ts, "recvWindow": 5000
        }
        qs = urllib.parse.urlencode(params)
        sig = hmac.new(secret_key.encode(), qs.encode(), hashlib.sha256).hexdigest()
        req = urllib.request.Request(
            f"https://api.binance.com/api/v3/order?{qs}&signature={sig}",
            headers={"X-MBX-APIKEY": api_key},
            method="POST", data=b""
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.load(r)
        return {"success": True, "raw": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== CLI ==========

def cmd_status(args=None):
    state = load_engine()
    port = portfolio_status()
    print(f"🟢 Live Engine — {len(state['positions'])} posiciones activas")
    print(f"💰 Balance: ${port['balance_usdt'] or '?'} | En posiciones: ${port['in_positions']} | Libre: ${port['available']}")
    print(f"📊 Historial: {len(state['history'])} trades cerrados")
    if port["positions"]:
        print(f"\n📋 Posiciones:")
        for sym, p in port["positions"].items():
            trail = "🔁" if p.get("trail_activated") else "  "
            pnl_sym = "+" if p["pnl_usdt"] >= 0 else ""
            print(f"  {trail} {sym:>8}: entry ${p['entry']:.4f} | ${p['current_price']:.4f} | "
                  f"{pnl_sym}{p['pnl_pct']}% ({pnl_sym}${p['pnl_usdt']:.2f}) | "
                  f"SL ${p.get('trail_current_stop', p.get('sl',0)):.4f} TP ${p.get('tp',0):.4f}")
    if state["history"]:
        last5 = state["history"][-5:]
        wins = sum(1 for t in last5 if t["result"] == "WIN")
        print(f"\n🕐 Últimos {len(last5)} trades: {wins}W/{len(last5)-wins}L")


def cmd_add(args):
    if len(args) < 2:
        print("Uso: add SYM size_usdt [tp] [sl]")
        return
    sym = args[0].upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    size = float(args[1])
    tp = float(args[2]) if len(args) > 2 else None
    sl = float(args[3]) if len(args) > 3 else None

    px = get_price(sym)
    # Ejecutar compra real
    result = execute_buy(sym, size)
    if result["success"]:
        print(f"✅ Compra ejecutada: {sym} ${px:.4f} x ${size:.2f}")
        add_position(sym, px, size, tp, sl, 0)
        print(f"   Registrado en engine con TP=${tp or '—'} SL=${sl or '—'}")
    else:
        print(f"❌ Error compra: {result.get('error')}")
        print(f"   (Registrando igual para simulación)")
        add_position(sym, px, size, tp, sl, 0)
        print(f"   Posición registrada en modo simulación")


def cmd_close(args):
    if not args:
        print("Uso: close SYM")
        return
    sym = args[0].upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    px = get_price(sym)
    # Vender real
    result = execute_sell(sym)
    trade = close_position(sym, px)
    if trade:
        pnl = "+" if trade["pnl_usdt"] > 0 else ""
        print(f"🔴 Cerrado {sym} a ${px:.4f} | P&L: {pnl}${trade['pnl_usdt']:.2f} ({pnl}{trade['pnl_pct']}%)")
        if result.get("success"):
            print(f"   ✅ Venta ejecutada en Binance")
        else:
            print(f"   ⚠️  Venta simulada (error API: {result.get('error')})")
    else:
        print(f"No hay posición para {sym}")


def cmd_trail(args):
    """Configura trailing TP manual."""
    if len(args) < 1:
        print("Uso: trail SYM [tp%]")
        return
    sym = args[0].upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    state = load_engine()
    if sym in state["positions"]:
        tp_pct = float(args[1]) if len(args) > 1 else 3.0
        entry = state["positions"][sym]["entry"]
        state["positions"][sym]["tp"] = entry * (1 + tp_pct/100)
        save_engine(state)
        print(f"✅ Trailing TP configurado para {sym}: {tp_pct}% (${state['positions'][sym]['tp']:.4f})")
    else:
        print(f"No hay posición para {sym}")


def cmd_check(args2=None):
    """Revisa todas las posiciones y trailing."""
    results = check_all_positions()
    for r in results:
        sym = r["sym"]
        action = r.get("action", "?")
        price = r.get("price", "?")
        gain = r.get("gain_pct", 0)
        trail = r.get("trail_active", False)

        if action == "TRAIL_ACTIVATED":
            print(f"🔁 {sym}: TRAILING ACTIVADO a ${r.get('trail_stop',0):.4f} (gain {gain}%)")
        elif action == "TRAIL_UPDATED":
            print(f"🔁 {sym}: Stop subió a ${r.get('trail_stop',0):.4f}")
        elif action == "TRAIL_STOPPED":
            t = r.get("trade", {})
            print(f"🔴 {sym}: TRAILING STOP ejecutado! P&L: ${t.get('pnl_usdt',0):.2f}")
        elif action == "SL_HIT":
            t = r.get("trade", {})
            print(f"🔴 {sym}: SL alcanzado! P&L: ${t.get('pnl_usdt',0):.2f}")
        elif action == "TP_HIT":
            t = r.get("trade", {})
            print(f"🏆 {sym}: TP alcanzado! P&L: ${t.get('pnl_usdt',0):.2f}")
        elif trail:
            print(f"🔁 {sym}: ${price:.4f} ({gain}%) | Trail stop ${r.get('trail_stop',0):.4f}")
        else:
            print(f"⏳ {sym}: ${price:.4f} ({gain}%) | Esperando trailing...")


# ========== THREAD: Live Monitor ==========

_live_thread = None
_live_running = False


def _live_loop():
    """Loop cada 30 segundos revisando posiciones."""
    global _live_running
    while _live_running:
        try:
            results = check_all_positions()
            signal = None
            for r in results:
                a = r.get("action")
                if a in ("TRAIL_STOPPED", "SL_HIT", "TP_HIT"):
                    signal = r
            if signal:
                # Write alert for cron to pick up
                ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(ALERT_FILE, "w") as f:
                    f.write(f"🚨 LIVE ENGINE ALERT\n")
                    f.write(f"Sym: {signal['sym']}\n")
                    f.write(f"Action: {signal['action']}\n")
                    t = signal.get("trade", {})
                    if t:
                        f.write(f"P&L: ${t.get('pnl_usdt', 0):.2f}\n")
                    sell_r = signal.get("real_sell", {})
                    if sell_r:
                        f.write(f"Venta real: OK\n")
                    elif signal.get("sell_error"):
                        f.write(f"Venta real error: {signal['sell_error']}\n")
        except Exception as e:
            # Silently log errors
            try:
                ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)
                with open(ERROR_LOG, "a") as f:
                    f.write(f"[{datetime.now().isoformat()}] Loop error: {e}\n")
            except:
                pass
        time.sleep(30)


def cmd_start(args=None):
    global _live_running, _live_thread
    if _live_running:
        print("⚠️  Live Engine ya está corriendo")
        return
    _live_running = True
    _live_thread = threading.Thread(target=_live_loop, daemon=True)
    _live_thread.start()
    state = load_engine()
    state["running"] = True
    state["started_at"] = time.time()
    save_engine(state)
    # Escribir PID file
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print(f"🚀 Live Engine iniciado — revisando cada 30s (PID {os.getpid()})")


def cmd_stop(args=None):
    global _live_running
    _live_running = False
    state = load_engine()
    state["running"] = False
    save_engine(state)
    # Limpiar PID file
    if PID_FILE.exists():
        PID_FILE.unlink()
    print("🛑 Live Engine detenido")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: live_engine.py <start|stop|status|add|close|trail|check> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    cmds = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
        "add": cmd_add,
        "close": cmd_close,
        "trail": cmd_trail,
        "check": cmd_check,
    }
    if cmd in cmds:
        cmds[cmd](args)
    else:
        print(f"Comando desconocido: {cmd}")
