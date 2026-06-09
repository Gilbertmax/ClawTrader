#!/usr/bin/env python3
"""Unified ClawTrader CLI."""
import argparse
import json

from config import get_config

DEFAULT_PRO_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"]


def print_json(data):
    print(json.dumps(data, indent=2, default=str))


def cmd_config(_args):
    print_json(get_config().safe_dict())
    return 0


def cmd_health(_args):
    import healthcheck

    healthcheck.main()
    return 0


def cmd_scan(args):
    from market_scanner import run_scan

    result = run_scan(pairs=args.symbols, min_score=args.min_score)
    print_json(result)
    return 0 if result.get("best") else 1


def cmd_pro_scan(args):
    from market_intelligence import scan_symbols

    print_json(scan_symbols(args.symbols))
    return 0


def cmd_decide(args):
    from market_intelligence import score_symbol

    print_json(score_symbol(args.symbol))
    return 0


def cmd_snapshot(args):
    import ccxt
    from crypto_live import snapshot

    exchange_map = {
        "binance": ccxt.binance,
        "coinbase": ccxt.coinbase,
        "bybit": ccxt.bybit,
        "kraken": ccxt.kraken,
        "okx": ccxt.okx,
    }
    exchanges = [(name, exchange_map[name]) for name in args.exchanges if name in exchange_map]
    if not exchanges:
        print_json({"error": "No valid exchanges specified"})
        return 1
    print_json(snapshot(exchanges, args.symbols))
    return 0


def cmd_analyze(args):
    from trading_analytics import analyze_symbol

    results = [analyze_symbol(sym, interval=args.interval, period=args.period) for sym in args.symbols]
    print_json(results if len(results) > 1 else results[0])
    return 0


def cmd_alpaca_status(_args):
    from alpaca_trader import AlpacaTrader

    trader = AlpacaTrader()
    print(trader.status(verbose=True))
    return 0


def cmd_binance_balances(_args):
    from binance_client import BinanceClient

    client = BinanceClient()
    print_json(client.balances())
    return 0


def cmd_risk(args):
    from risk import validate_trade

    cfg = get_config()
    print_json(
        validate_trade(
            entry=args.entry,
            current_price=args.current,
            stop_loss=args.stop,
            take_profit=args.take_profit,
            score=args.score,
            capital=args.capital if args.capital is not None else cfg.capital,
            requested_amount=args.amount,
            btc_bearish=args.btc_bearish,
            side=args.side,
            min_rr=args.min_rr,
        )
    )
    return 0


def cmd_report(_args):
    import clawtrader_report

    clawtrader_report.main()
    return 0


def cmd_dashboard(args):
    import server

    server.serve(host=args.host, port=args.port)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="ClawTrader unified CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("config", help="Show safe configuration summary")
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("health", help="Run installation healthcheck")
    p.set_defaults(func=cmd_health)

    p = sub.add_parser("scan", help="Run Binance market scanner")
    p.add_argument("--symbols", nargs="+", help="Symbols like BTCUSDT ETHUSDT")
    p.add_argument("--min-score", type=int, default=6)
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("pro-scan", help="Run professional multi-timeframe decision scanner")
    p.add_argument("--symbols", nargs="+", default=DEFAULT_PRO_SYMBOLS, help="Binance spot symbols like BTCUSDT ETHUSDT")
    p.set_defaults(func=cmd_pro_scan)

    p = sub.add_parser("decide", help="Build a professional decision plan for one Binance spot symbol")
    p.add_argument("symbol", help="Binance spot symbol like BTCUSDT")
    p.set_defaults(func=cmd_decide)

    p = sub.add_parser("snapshot", help="Fetch crypto market snapshot")
    p.add_argument("--symbols", nargs="+", default=["BTC/USDT", "ETH/USDT", "SOL/USDT"])
    p.add_argument("--exchanges", nargs="+", default=["binance"])
    p.set_defaults(func=cmd_snapshot)

    p = sub.add_parser("analyze", help="Run TA-Lib/yfinance analysis")
    p.add_argument("symbols", nargs="+")
    p.add_argument("--interval", default="1d")
    p.add_argument("--period", default="3mo")
    p.set_defaults(func=cmd_analyze)

    p = sub.add_parser("alpaca-status", help="Show Alpaca paper account status")
    p.set_defaults(func=cmd_alpaca_status)

    p = sub.add_parser("binance-balances", help="Show Binance balances")
    p.set_defaults(func=cmd_binance_balances)

    p = sub.add_parser("risk", help="Validate a trade proposal")
    p.add_argument("--entry", type=float, required=True)
    p.add_argument("--current", type=float, required=True)
    p.add_argument("--stop", type=float, required=True)
    p.add_argument("--take-profit", type=float, required=True)
    p.add_argument("--score", type=int, required=True)
    p.add_argument("--amount", type=float)
    p.add_argument("--capital", type=float)
    p.add_argument("--side", choices=["long", "short"], default="long")
    p.add_argument("--min-rr", type=float, default=1.2)
    p.add_argument("--btc-bearish", action="store_true")
    p.set_defaults(func=cmd_risk)

    p = sub.add_parser("report", help="Generate text report")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("dashboard", help="Start dashboard server")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=8080)
    p.set_defaults(func=cmd_dashboard)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
