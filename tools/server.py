#!/usr/bin/env python3
"""
ClawTrader Dashboard Server v1.0
Sirve dashboard HTML + API de datos en vivo
Ing. Gilbert — 29 Mayo 2026

Usage:
  python3 tools/server.py              # Puerto 8080
  python3 tools/server.py --port 9090  # Puerto personalizado
"""
import argparse
import http.server
import json
import sys
import time
import urllib.parse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))

import ccxt
import yfinance as yf

# ---------- Data Engines ----------
def get_crypto_snapshot():
    exchanges = [
        ('Binance', ccxt.binance),
        ('Coinbase', ccxt.coinbase),
    ]
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'XRP/USDT']
    result = {}
    for name, cls in exchanges:
        try:
            ex = cls({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})
            tickers = {}
            for sym in symbols:
                try:
                    t = ex.fetch_ticker(sym)
                    tickers[sym] = {
                        'last': t['last'],
                        'bid': t.get('bid'),
                        'ask': t.get('ask'),
                        'change_pct': round(t.get('percentage', 0), 2),
                        'volume': t.get('baseVolume', 0),
                    }
                except:
                    tickers[sym] = {'error': 'fetch failed'}
            result[name] = tickers
        except Exception as e:
            result[name] = {'error': str(e)[:80]}
    return result

def get_forex_snapshot():
    symbols = {
        'EURUSD=X': 'EUR/USD', 'GBPUSD=X': 'GBP/USD',
        'JPY=X': 'USD/JPY', 'DX-Y.NYB': 'DXY',
        'GC=F': 'GOLD', 'CL=F': 'USOIL',
        '^VIX': 'VIX', '^GSPC': 'SPX',
    }
    result = {}
    for sym, name in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='5d')
            if hist.empty:
                continue
            last = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = ((last - prev) / prev) * 100
            sma3 = hist['Close'].tail(3).mean()
            signal = 'BUY' if last > sma3 else 'SELL' if last < sma3 * 0.995 else 'HOLD'
            result[name] = {
                'last': round(float(last), 5),
                'change_pct': round(float(change), 2),
                'signal': signal,
            }
        except:
            pass
    return result

def get_chart_data(symbol='EURUSD=X', period='1mo', interval='1d'):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        if hist.empty:
            return []
        data = []
        for idx, row in hist.iterrows():
            ts = int(idx.timestamp())
            data.append({
                'time': ts,
                'open': round(float(row['Open']), 5),
                'high': round(float(row['High']), 5),
                'low': round(float(row['Low']), 5),
                'close': round(float(row['Close']), 5),
            })
        return data
    except:
        return []

# ---------- HTTP Handler ----------
class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        
        if path in ('/', '/index.html'):
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html_path = TOOLS_DIR / 'dashboard.html'
            if html_path.exists():
                self.wfile.write(html_path.read_bytes())
            else:
                self.wfile.write(b'<h1>ClawTrader Dashboard</h1><p>Dashboard HTML not found.</p>')
        
        elif path == '/api/tickers':
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            result = {
                'crypto': get_crypto_snapshot(),
                'markets': get_forex_snapshot(),
                'timestamp': time.strftime('%H:%M:%S'),
            }
            self.wfile.write(json.dumps(result).encode())
        
        elif path.startswith('/api/chart/'):
            symbol = path.replace('/api/chart/', '')
            if symbol == 'EURUSD':
                symbol = 'EURUSD=X'
            elif symbol == 'BTC':
                symbol = 'BTC-USD'
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = get_chart_data(symbol)
            self.wfile.write(json.dumps(data).encode())
        
        elif path == '/api/scan':
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            result = {
                'crypto': get_crypto_snapshot(),
                'markets': get_forex_snapshot(),
                'timestamp': time.strftime('%H:%M:%S'),
            }
            self.wfile.write(json.dumps(result).encode())
        
        elif path == '/health':
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'time': time.strftime('%H:%M:%S')}).encode())
        
        else:
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'ClawTrader Server - endpoints: /api/tickers /api/chart/SYMBOL /api/scan /health')
    
    def log_message(self, format, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} {args[2]}")

def generate_html():
    """Generate dashboard HTML from dashboard.py template if not exists"""
    html_path = TOOLS_DIR / 'dashboard.html'
    if not html_path.exists():
        try:
            import dashboard as db
            html_path.write_text(db.HTML_TEMPLATE)
            print(f"✅ Dashboard HTML generado: {html_path}")
        except ImportError:
            print("⚠️ dashboard.py not found, HTML not generated")

def main():
    parser = argparse.ArgumentParser(description='ClawTrader Dashboard Server')
    parser.add_argument('--port', type=int, default=8080, help='Port (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host (default: 0.0.0.0)')
    args = parser.parse_args()
    
    generate_html()
    
    server = http.server.HTTPServer((args.host, args.port), Handler)
    print(f"""
╔══════════════════════════════════════════════════╗
║     📈 ClawTrader Dashboard Server              ║
║     http://localhost:{args.port}                   ║
║                                                  ║
║     Endpoints:                                   ║
║       /              Dashboard HTML              ║
║       /api/tickers   Crypto + Forex snapshot     ║
║       /api/chart/EURUSD  Candle data             ║
║       /api/scan      Full market scan            ║
║       /health        Health check                ║
╚══════════════════════════════════════════════════╝
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped.")
        server.server_close()

if __name__ == '__main__':
    main()
