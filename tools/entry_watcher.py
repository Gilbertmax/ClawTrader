#!/usr/bin/env python3
"""
Entry Watcher — vigila pares específicos y alerta si tocan zona de entrada.
- Recibe una lista de pares con precio objetivo y tolerancia
- Cada ejecución revisa precios actuales vs targets
- Si hay match → escribe alerta a /tmp/entry_alert.txt
- Diseñado para correr cada 1-2 minutos vía cron

USO:
  python3 tools/entry_watcher.py set BTCUSDT 60000 0.02 61000 59000
    → Vigila BTC/USDT, entry deseado $60k ±2%, TP $61k, SL $59k

  python3 tools/entry_watcher.py check
    → Revisa todos los targets y alerta si alguno coincide

  python3 tools/entry_watcher.py list
    → Lista targets activos

  python3 tools/entry_watcher.py remove BTCUSDT
    → Elimina target

  python3 tools/entry_watcher.py clear
    → Elimina todos los targets
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from load_env import load_env, status_dir
from smart_money import get_orderbook, detect_bos

load_env()

WATCH_FILE = Path(os.environ.get("CLAWTRADER_ENTRY_WATCH_FILE", status_dir() / "entry_watcher_targets.json"))
ALERT_FILE = Path(os.environ.get("CLAWTRADER_ENTRY_ALERT_FILE", status_dir() / "entry_alert.txt"))


def load_targets():
    if WATCH_FILE.exists():
        with open(WATCH_FILE) as f:
            return json.load(f)
    return {"targets": []}


def save_targets(targets):
    WATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(WATCH_FILE, "w") as f:
        json.dump(targets, f, indent=2)


def get_price(sym):
    """Obtiene precio actual de Binance."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}"
    with urlopen(url, timeout=5) as r:
        d = json.load(r)
        return float(d["price"])


def get_vwap_obv(sym):
    """Obtiene VWAP, OBV y precio desde klines 1h últimas 24."""
    url = f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=24"
    with urlopen(url, timeout=10) as r:
        kl = json.load(r)
    if not kl:
        return None, None, 0
    p = float(kl[-1][4])
    # VWAP
    vol_acum = 0
    pxv_acum = 0
    for k in kl:
        hi, lo, close, vol = float(k[2]), float(k[3]), float(k[4]), float(k[5])
        tp = (hi + lo + close) / 3
        vol_acum += vol
        pxv_acum += tp * vol
    vwap = pxv_acum / vol_acum if vol_acum > 0 else p
    # OBV
    vals = []
    ob = 0
    for i in range(len(kl)):
        if i == 0:
            ob = 0
        else:
            c, c_prev = float(kl[i][4]), float(kl[i-1][4])
            vol = float(kl[i][5])
            if c > c_prev:
                ob += vol
            elif c < c_prev:
                ob -= vol
        vals.append(ob)
    if len(vals) >= 2:
        lo, hi = min(vals), max(vals)
        obv_pct = ((vals[-1]-lo)/(hi-lo)*100) if hi != lo else 50
    else:
        obv_pct = 50
    return vwap, round(obv_pct, 1), p


def cmd_set(args):
    """Añadir target: set SYMBOL entry_price tolerance tp sl"""
    if len(args) < 5:
        print("Uso: set SYMBOL entry_price tolerance tp sl [label]")
        return
    sym = args[0].upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    entry = float(args[1])
    tol = float(args[2])
    tp = float(args[3]) if args[3] != "0" else None
    sl = float(args[4]) if args[4] != "0" else None
    label = " ".join(args[5:]) if len(args) > 5 else sym.replace("USDT", "")

    data = load_targets()
    # Remove existing for same sym
    data["targets"] = [t for t in data["targets"] if t["sym"] != sym]
    data["targets"].append({
        "sym": sym,
        "label": label,
        "entry": entry,
        "tol": tol,
        "tp": tp,
        "sl": sl,
        "created_at": time.time(),
        "entry_min": entry * (1 - tol),
        "entry_max": entry * (1 + tol),
    })
    save_targets(data)
    print(f"✅ Vigilando {label} ({sym}): "
          f"entry ${entry:.4f} ±{tol*100:.0f}% "
          f"[${entry*(1-tol):.4f} - ${entry*(1+tol):.4f}]" +
          (f" TP ${tp:.4f}'" if tp else "") +
          (f" SL ${sl:.4f}" if sl else ""))


def cmd_check(args=None):
    """Revisa precios vs targets."""
    data = load_targets()
    if not data["targets"]:
        print("No hay targets activos.")
        return

    alerts = []
    for t in data["targets"]:
        try:
            px = get_price(t["sym"])
            # Smart Money: Order Book + BOS
            try:
                ob = get_orderbook(t["sym"])
                with urlopen(f"https://api.binance.com/api/v3/klines?symbol={t['sym']}&interval=1h&limit=20", timeout=10) as r_kl:
                    kl_ob = json.load(r_kl)
                bos = detect_bos(kl_ob, 10)
                ob_status = f"OB {ob['imbalance']}x" + ("✅" if ob['imbalance'] > 1.5 else ("🔴" if ob['imbalance'] < 0.67 else ""))
                bos_status = f"BOS {bos['bos'] or '—'}"
            except:
                ob_status = "OB err"
                bos_status = ""
            # Obtener VWAP y OBV para contexto profesional
            vwap_val, obv_val, _ = get_vwap_obv(t["sym"])
            
            entry_min = t["entry_min"]
            entry_max = t["entry_max"]
            in_zone = entry_min <= px <= entry_max
            hit_tp = t["tp"] and px >= t["tp"]
            hit_sl = t["sl"] and px <= t["sl"]

            # Contexto profesional de valor
            vwap_status = ""
            if vwap_val:
                if px < vwap_val:
                    vwap_status = "DEBAJO VWAP ✅"
                elif px > vwap_val * 1.02:
                    vwap_status = ">2% SOBRE VWAP ⚠️"
                else:
                    vwap_status = "~VWAP"
            obv_status = f"OBV {obv_val}" + ("✅" if obv_val and obv_val > 55 else "")

            status = "🟢" if in_zone else ("🏆" if hit_tp else ("🔴" if hit_sl else "⏳"))
            details = []
            if in_zone:
                details.append(f"EN ZONA DE ENTRADA 🎯")
            if hit_tp:
                details.append(f"TP ALCANZADO ${t['tp']:.4f} 🏆")
            if hit_sl:
                details.append(f"SL ALCANZADO ${t['sl']:.4f} 🔴")
            if not details:
                details.append(f"Esperando ${entry_min:.4f}-${entry_max:.4f}")

            alert = f"[{t['label']}] ${px:.4f} | {status} | {details[0]} | {vwap_status} | {obv_status} | {ob_status} | {bos_status}"
            print(alert)

            if in_zone or hit_tp or hit_sl:
                alerts.append(alert)
        except Exception as e:
            print(f"[{t['sym']}] Error: {e}")

    # Write alert file if any match
    if alerts:
        ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERT_FILE, "w") as f:
            f.write(f"🚨 ENTRY WATCHER ALERT — {__import__('datetime').datetime.now().strftime('%H:%M')}\n")
            f.write("\n".join(alerts))
        print(f"\n⚠️  {len(alerts)} alerta(s) escritas en {ALERT_FILE}")
    else:
        if ALERT_FILE.exists():
            ALERT_FILE.unlink()


def cmd_list(args=None):
    data = load_targets()
    if not data["targets"]:
        print("No hay targets activos.")
        return
    print(f"📋 Targets activos ({len(data['targets'])}):")
    for t in data["targets"]:
        eta = time.time() - t["created_at"]
        print(f"   {t['label']:>8} ({t['sym']}) → "
              f"${t['entry']:.4f} ±{t['tol']*100:.0f}% "
              f"[${t['entry_min']:.4f}-${t['entry_max']:.4f}]"
              + (f" TP${t['tp']:.4f}" if t['tp'] else "")
              + (f" SL${t['sl']:.4f}" if t['sl'] else "")
              + f" | Hace {int(eta//3600)}h{int((eta%3600)//60)}m")


def cmd_remove(args):
    if not args:
        print("Uso: remove SYMBOL")
        return
    sym = args[0].upper()
    if not sym.endswith("USDT"):
        sym += "USDT"
    data = load_targets()
    before = len(data["targets"])
    data["targets"] = [t for t in data["targets"] if t["sym"] != sym]
    if len(data["targets"]) < before:
        save_targets(data)
        print(f"🗑️  Eliminado target para {sym}")
    else:
        print(f"No se encontró target para {sym}")


def cmd_clear(args=None):
    save_targets({"targets": []})
    if ALERT_FILE.exists():
        ALERT_FILE.unlink()
    print("🧹 Todos los targets eliminados")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: entry_watcher.py <set|check|list|remove|clear> [args...]")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    cmds = {
        "set": cmd_set,
        "check": cmd_check,
        "list": cmd_list,
        "remove": cmd_remove,
        "clear": cmd_clear,
    }
    if cmd in cmds:
        cmds[cmd](args)
    else:
        print(f"Comando desconocido: {cmd}")
