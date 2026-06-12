#!/usr/bin/env python3
"""ClawTrader v2 — CLI unificada"""
import argparse, json, sys

from config import get_config

DEFAULT_PRO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]

def j(data):
    print(json.dumps(data, indent=2, default=str))

# ─── Comandos ──────────────────────────────────────────────

def cmd_config(_args):
    j(get_config().safe_dict())
    return 0

def cmd_health(_args):
    import healthcheck
    healthcheck.main()
    return 0

def cmd_balances(_args):
    from binance_client import BinanceClient
    c = BinanceClient()
    bals = c.balances()
    total = sum(v.get("usd_value", 0) for v in bals.values())
    print("\n📊 BALANCES:")
    for sym, info in bals.items():
        print(f"  {sym:6s}  {info.get('free',0):.6f}  ≈ ${info.get('usd_value',0):.2f}")
    print(f"  {'─'*30}")
    print(f"  TOTAL: ${total:.2f}")
    return 0

def cmd_scan(args):
    from market_scanner import run_scan
    result = run_scan(pairs=args.symbols, min_score=args.min_score)
    j(result)
    if result.get("best"):
        print(f"\n✅ Mejor: {result['best']['symbol']} (score {result['best']['score']}/16)")
    return 0 if result.get("best") else 1

def cmd_pro_scan(args):
    from market_intelligence import scan_symbols
    result = scan_symbols(args.symbols)
    j(result)
    best = result.get("best") or {}
    return 1 if best.get("decision") == "DATA_ERROR" else 0

def cmd_decide(args):
    from market_intelligence import score_symbol
    result = score_symbol(args.symbol)
    j(result)
    return 1 if result.get("decision") == "DATA_ERROR" else 0

def cmd_smart_money(args):
    from smart_money import analyze_sym
    r = analyze_sym(args.symbol.upper())
    j(r)
    decision = r.get("senal", {}).get("decision") or r.get("veredicto") or "NEUTRA"
    verdict = "✅ FAVORABLE" if decision == "ALCISTA" else "⚠️ DESFAVORABLE" if decision == "BAJISTA" else "⏳ NEUTRAL"
    print(f"\nVeredicto Smart Money: {verdict}")
    return 0

def cmd_risk(args):
    from risk import validate_trade
    cfg = get_config()
    j(validate_trade(
        entry=args.entry, current_price=args.current,
        stop_loss=args.stop, take_profit=args.take_profit,
        score=args.score,
        capital=args.capital if args.capital else cfg.capital,
        requested_amount=args.amount,
        btc_bearish=args.btc_bearish, side=args.side, min_rr=args.min_rr
    ))
    return 0

def cmd_backtest(_args):
    import backtest
    backtest.main()
    return 0

def cmd_engine_status(_args):
    try:
        from live_engine import load_engine
        j(load_engine())
        return 0
    except Exception as e:
        print(f"⚠️ No se pudo leer engine_state: {e}")
        return 1

def cmd_cycle_run(_args):
    """Ejecutar auto-cycle manualmente una vez"""
    sys.path.insert(0, '.')
    from auto_cycle import run_once
    run_once()
    return 0

def cmd_cycle_start(_args):
    """Iniciar auto-cycle en background"""
    import subprocess, os
    pid = os.fork()
    if pid == 0:
        os.execvp("openclaw", ["openclaw", "cron", "run", "auto-cycle"])
    print("✅ Auto-cycle iniciado en background")
    return 0

def cmd_estrategia(_args):
    """Mostrar resumen de ESTRATEGIA.md"""
    try:
        with open('ESTRATEGIA.md') as f:
            content = f.read()
        # Mostrar solo cabeceras y reglas clave
        lines = [l for l in content.split('\n') if l.startswith('#') or l.startswith('- [')]
        print("📋 ESTRATEGIA — Reglas clave:")
        for l in lines[:30]:
            print(f"  {l}")
        return 0
    except:
        print("⚠️ ESTRATEGIA.md no encontrado")
        return 1

# ─── Parser ────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(description="🦞 ClawTrader v2 — Trading Autónomo")
    sub = p.add_subparsers(dest="command", required=True)

    for name, help_text, func, args_fn in [
        ("config", "Mostrar configuración segura", cmd_config, None),
        ("health", "Verificar instalación", cmd_health, None),
        ("balances", "Mostrar balances Binance", cmd_balances, None),
        ("scan", "Escanear mercado (score 0-16)", cmd_scan, lambda x: [
            x.add_argument("--symbols", nargs="+", help="Symbols like BTCUSDT"),
            x.add_argument("--min-score", type=int, default=8)]),
        ("pro-scan", "Escanear mercado con analisis multi-timeframe", cmd_pro_scan, lambda x: [
            x.add_argument("--symbols", nargs="+", default=DEFAULT_PRO_SYMBOLS, help="Symbols like BTCUSDT ETHUSDT")]),
        ("decide", "Crear plan profesional para un simbolo", cmd_decide, lambda x: [
            x.add_argument("symbol", help="BTCUSDT")]),
        ("smart-money", "Analizar Smart Money de un símbolo", cmd_smart_money, lambda x: [
            x.add_argument("symbol", help="BTCUSDT")]),
        ("risk", "Validar propuesta de trade", cmd_risk, lambda x: [
            x.add_argument("--entry", type=float, required=True),
            x.add_argument("--current", type=float, required=True),
            x.add_argument("--stop", type=float, required=True),
            x.add_argument("--take-profit", type=float, required=True),
            x.add_argument("--score", type=int, required=True),
            x.add_argument("--amount", type=float),
            x.add_argument("--capital", type=float),
            x.add_argument("--side", choices=["long", "short"], default="long"),
            x.add_argument("--min-rr", type=float, default=1.2),
            x.add_argument("--btc-bearish", action="store_true")]),
        ("backtest", "Mostrar historial de trades", cmd_backtest, None),
        ("engine", "Mostrar estado del engine", cmd_engine_status, None),
        ("cycle-run", "Ejecutar auto-cycle una vez", cmd_cycle_run, None),
        ("cycle-start", "Iniciar auto-cycle", cmd_cycle_start, None),
        ("estrategia", "Mostrar resumen de estrategia", cmd_estrategia, None),
    ]:
        s = sub.add_parser(name, help=help_text)
        if args_fn:
            args_fn(s)
        s.set_defaults(func=func)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)

if __name__ == "__main__":
    raise SystemExit(main())
