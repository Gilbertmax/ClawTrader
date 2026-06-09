#!/usr/bin/env python3
"""
ClawTrader Orchestrator v1.0
Orquesta los sub-agentes: Market Analyst → Risk Manager → Executor → Journalist
Corre en background como proceso independiente.
Ing. Gilbert — 29 Mayo 2026
"""
import json
import subprocess
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

TOOLS_DIR = Path(__file__).parent
MEMORY_DIR = TOOLS_DIR.parent / "memory"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def run_analysis(symbol="EURUSD=X", interval="5m", period="5d"):
    """Market Analyst: get TA-Lib signals"""
    try:
        sys.path.insert(0, str(TOOLS_DIR))
        from trading_analytics import analyze_symbol
        return analyze_symbol(symbol, interval=interval, period=period)
    except ImportError:
        log("⚠️ trading_analytics not found, using subprocess")
        result = subprocess.run(
            [sys.executable, "-c", f"""
import sys; sys.path.insert(0, '{TOOLS_DIR}')
from trading_analytics import analyze_symbol
import json
d = analyze_symbol('{symbol}', interval='{interval}', period='{period}')
print(json.dumps(d))
"""], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
        else:
            log(f"❌ Analysis failed: {result.stderr[:200]}")
            return None

def calculate_risk(capital, units, direction, entry, sl, tp, loss_streak=0):
    """Risk Manager: evaluate trade proposal"""
    if direction.upper() == "LONG":
        risk_amount = units * abs(entry - sl)
        reward_amount = units * abs(tp - entry)
    else:
        risk_amount = units * abs(sl - entry)
        reward_amount = units * abs(entry - tp)
    
    risk_pct = (risk_amount / capital) * 100
    rr = reward_amount / risk_amount if risk_amount > 0 else 0
    
    checks = {
        "risk_under_2pct": risk_pct <= 2.0,
        "rr_above_1.5": rr >= 1.5,
        "loss_streak_ok": loss_streak < 3,
        "sl_defined": sl and sl > 0,
        "tp_defined": tp and tp > 0,
    }
    
    approved = all(checks.values())
    reasons = []
    if not checks["risk_under_2pct"]:
        reasons.append(f"Riesgo {risk_pct:.2f}% excede 2%")
    if not checks["rr_above_1.5"]:
        reasons.append(f"R/R {rr:.1f} < 1.5")
    if not checks["loss_streak_ok"]:
        reasons.append(f"Racha {loss_streak} pérdidas")
    if not checks["sl_defined"]:
        reasons.append("SL no definido")
    if not checks["tp_defined"]:
        reasons.append("TP no definido")
    
    return {
        "decision": "APPROVED" if approved else "REJECTED",
        "reason": "; ".join(reasons) if reasons else f"R/R {rr:.1f}, riesgo {risk_pct:.3f}%",
        "risk_amount": round(risk_amount, 2),
        "risk_pct": round(risk_pct, 4),
        "reward_amount": round(reward_amount, 2),
        "rr_ratio": round(rr, 2),
    }

def register_trade(trade_data):
    """Journalist: log trade to daily journal"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    journal_path = MEMORY_DIR / f"{date_str}.md"
    
    entry_text = f"""
### Trade #{trade_data['id']} ({datetime.now().strftime('%H:%M CT')})
- **Activo:** {trade_data['asset']} | **Dirección:** {trade_data['direction']} | **Unidades:** {trade_data['units']}
- **Entrada:** {trade_data['entry']} | **Salida:** {trade_data.get('exit', 'ABIERTO')}
- **SL:** {trade_data['sl']} | **TP:** {trade_data['tp']}
- **PnL:** ${trade_data.get('pnl', 0):.2f} ({trade_data.get('pnl_pct', 0):.4f}%)
- **Razón entrada:** {trade_data.get('reason_entry', 'N/A')}
- **Razón salida:** {trade_data.get('reason_exit', 'N/A')}
- **Lección:** {trade_data.get('lesson', 'N/A')}
"""
    try:
        with open(journal_path, 'a') as f:
            f.write(entry_text)
        return {"status": "logged", "file": str(journal_path)}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def trading_cycle():
    """Full trading cycle: Analyze → Risk → Execute → Log"""
    log("🔄 Iniciando ciclo de trading")
    
    # 1. Market Analysis
    log("📊 Market Analyst: analizando EUR/USD 5m...")
    analysis = run_analysis("EURUSD=X", interval="5m", period="5d")
    if not analysis:
        log("❌ Análisis falló, abortando ciclo")
        return
    
    price = analysis.get('last_close', 0)
    score = analysis.get('score', 0)
    verdict = analysis.get('verdict', 'NEUTRAL')
    ind = analysis.get('indicators', {})
    patterns = analysis.get('patterns', [])
    signals = analysis.get('signals', {})
    
    log(f"📊 Precio: {price}, Score: {score}, Veredicto: {verdict}")
    
    # 2. Strength check (score -12..+12)
    if abs(score) < 4:
        log(f"⏸️  Señal débil (score={score}), no se propone trade")
        return
    
    # 3. Build proposal
    capital = 99996.30
    direction = "LONG" if score > 0 else "SHORT"
    entry = price
    
    bb_upper = ind.get('bb_upper', entry * 1.003)
    bb_lower = ind.get('bb_lower', entry * 0.997)
    
    if direction == "LONG":
        sl = round(entry - (entry - bb_lower) * 0.5, 5)
        tp = round(entry + (entry - bb_lower) * 1.5, 5)
    else:
        sl = round(entry + (bb_upper - entry) * 0.5, 5)
        tp = round(entry - (bb_upper - entry) * 1.5, 5)
    
    units = 5000
    
    # 4. Risk Assessment
    log(f"⚠️ Risk Manager: evaluando {direction} {units}u a {entry}...")
    risk = calculate_risk(capital, units, direction, entry, sl, tp)
    log(f"⚠️ Decisión: {risk['decision']} - {risk['reason']}")
    
    if risk['decision'] != 'APPROVED':
        log(f"❌ Trade rechazado: {risk['reason']}")
        return
    
    # 5. Print proposal
    trade = {
        "id": 1,
        "asset": "EUR/USD",
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "units": units,
        "risk_amount": risk['risk_amount'],
        "risk_pct": risk['risk_pct'],
        "rr": risk['rr_ratio'],
        "reason_entry": f"Score {score}: {verdict}",
        "pattern": patterns[0] if patterns else 'N/A',
    }
    
    log(f"""
╔══════════════════════════════════════════╗
║     ✅ TRADE PROPUESTO                  ║
║     {direction} {units}u EUR/USD @ {entry}          ║
║     SL: {sl} | TP: {tp}                ║
║     Riesgo: ${risk['risk_amount']} ({risk['risk_pct']:.3f}%)  ║
║     R/R: {risk['rr_ratio']}                           ║
║     Score: {score} | {verdict}                   ║
║     Patrón: {patterns[0] if patterns else 'N/A'}           ║
╚══════════════════════════════════════════╝
    """)
    
    # 6. Log to journal
    register_trade({**trade, "pnl": 0, "pnl_pct": 0, "exit": None, "reason_exit": None, "lesson": None})
    log("📝 Journalist: trade logged")
    
    return trade

def monitor_mode(interval=300):
    """Run trading cycles continuously"""
    log(f"🔄 ClawTrader Orchestrator iniciado (intervalo: {interval}s)")
    cycle_count = 0
    
    while True:
        cycle_count += 1
        log(f"\n{'='*50}")
        log(f"Ciclo #{cycle_count}")
        
        try:
            trading_cycle()
        except Exception as e:
            log(f"❌ Error en ciclo: {e}")
        
        log(f"💤 Esperando {interval}s...")
        time.sleep(interval)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ClawTrader Orchestrator')
    parser.add_argument('--interval', type=int, default=300, help='Ciclo en segundos')
    parser.add_argument('--once', action='store_true', help='Un solo ciclo')
    
    args = parser.parse_args()
    if args.once:
        trading_cycle()
    else:
        monitor_mode(args.interval)
