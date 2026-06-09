#!/usr/bin/env python3
"""
ClawTrader Crypto Snapshot Engine v1.0
Datos en vivo desde múltiples exchanges — síncrono, rápido
"""
import argparse
import json
import sys
import time
import warnings
warnings.filterwarnings("ignore")

SYMBOLS_DEFAULT = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']

import ccxt

def snapshot(exchanges_config, symbols):
    """Fetch snapshot from all configured exchanges"""
    results = {}
    for name, cls in exchanges_config:
        try:
            ex = cls({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'},
            })
            # Load markets once
            if not hasattr(snapshot, 'markets_loaded'):
                ex.load_markets()
            
            tickers = {}
            for sym in symbols:
                try:
                    t = ex.fetch_ticker(sym)
                    change_pct = t.get('percentage', 0)
                    tickers[sym] = {
                        'last': t['last'],
                        'bid': t.get('bid'),
                        'ask': t.get('ask'),
                        'change_pct': round(change_pct, 2) if change_pct else 0,
                        'volume': t.get('baseVolume', 0),
                        'high': t.get('high'),
                        'low': t.get('low'),
                    }
                except Exception as e:
                    tickers[sym] = {'error': str(e)[:60]}
            
            results[name] = tickers
        except Exception as e:
            results[name] = {'error': str(e)[:100]}
    
    return results


def perpetual_snapshot(exchanges_config, symbols, interval=10):
    """Run forever, printing snapshots"""
    print(json.dumps({
        'status': 'live',
        'exchanges': [e[0] for e in exchanges_config],
        'symbols': symbols,
        'interval_seconds': interval
    }))
    sys.stdout.flush()
    
    while True:
        data = snapshot(exchanges_config, symbols)
        data['_ts'] = time.time()
        print(json.dumps(data))
        sys.stdout.flush()
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='ClawTrader Crypto Engine')
    parser.add_argument('--symbols', nargs='+', default=SYMBOLS_DEFAULT,
                       help='Symbols like BTC/USDT ETH/USDT')
    parser.add_argument('--interval', type=int, default=10,
                       help='Poll interval in seconds (default: 10)')
    parser.add_argument('--once', action='store_true',
                       help='One snapshot only')
    parser.add_argument('--exchanges', nargs='+', 
                       default=['binance', 'coinbase', 'bybit'],
                       help='Exchanges to query')
    parser.add_argument('--forex', action='store_true',
                       help='Include forex pairs via yfinance')
    parser.add_argument('--all', action='store_true',
                       help='Full market scan')
    
    args = parser.parse_args()
    
    # Map exchange names to classes
    exchange_map = {
        'binance': ccxt.binance,
        'coinbase': ccxt.coinbase,
        'bybit': ccxt.bybit,
        'kraken': ccxt.kraken,
        'okx': ccxt.okx,
    }
    
    exchanges = []
    for name in args.exchanges:
        if name in exchange_map:
            exchanges.append((name, exchange_map[name]))
    
    if not exchanges:
        print(json.dumps({'error': 'No valid exchanges specified'}))
        return
    
    if args.all:
        # Full scan: crypto + forex + indices
        symbols = [
            'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT',
            'ADA/USDT', 'DOGE/USDT', 'DOT/USDT', 'AVAX/USDT',
            'LINK/USDT', 'MATIC/USDT'
        ]
        crypto = snapshot(exchanges[:2], symbols)
        
        # Forex via yfinance
        import yfinance as yf
        forex_symbols = {
            'EURUSD=X': 'EUR/USD',
            'GBPUSD=X': 'GBP/USD', 
            'JPY=X': 'USD/JPY',
            'DX-Y.NYB': 'DXY',
            'GC=F': 'GOLD',
            'CL=F': 'USOIL',
            '^VIX': 'VIX',
            '^GSPC': 'SPX',
        }
        forex = {}
        for sym, name in forex_symbols.items():
            try:
                t = yf.Ticker(sym)
                hist = t.history(period='2d')
                if not hist.empty:
                    last = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((last - prev) / prev) * 100
                    forex[name] = {
                        'last': round(last, 5),
                        'change_pct': round(change, 2)
                    }
            except:
                pass
        
        print(json.dumps({
            'type': 'full_scan',
            'timestamp': time.strftime('%H:%M:%S'),
            'crypto': crypto,
            'markets': forex
        }, indent=2))
    
    elif args.forex:
        # Mixed crypto + forex
        crypto = snapshot(exchanges[:2], args.symbols)
        import yfinance as yf
        forex_symbols = ['EURUSD=X', 'GBPUSD=X', 'JPY=X', 'GC=F']
        forex = {}
        for sym in forex_symbols:
            try:
                t = yf.Ticker(sym)
                hist = t.history(period='2d')
                if not hist.empty:
                    last = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = ((last - prev) / prev) * 100
                    forex[sym] = {
                        'last': round(last, 5),
                        'change_pct': round(change, 2)
                    }
            except:
                pass
        print(json.dumps({'crypto': crypto, 'forex': forex}, indent=2))
    
    elif args.once:
        data = snapshot(exchanges, args.symbols)
        print(json.dumps(data, indent=2))
    
    else:
        perpetual_snapshot(exchanges, args.symbols, args.interval)


if __name__ == '__main__':
    main()
