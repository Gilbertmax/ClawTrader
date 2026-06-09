#!/usr/bin/env python3
"""
ClawTrader Report — Reporte completo cada 15 min
Mercado: Binance (DOGE activo) + Alpaca (Stocks watch)
"""
import hashlib, hmac, time, requests, json, os, sys
from datetime import datetime

# ─── Load API keys from environment ───
BIN_API_KEY = os.environ.get("BINANCE_API_KEY_2", "NOT_SET")
BIN_SECRET = os.environ.get("BINANCE_SECRET_KEY_2", "NOT_SET")
BIN_HEADERS = {'X-MBX-APIKEY': BIN_API_KEY}

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "NOT_SET")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET_KEY_3", "NOT_SET")
ALPACA_HEADERS = {
    'APCA-API-KEY-ID': ALPACA_API_KEY,
    'APCA-API-SECRET-KEY': ALPACA_SECRET
}

# ─── State file for change detection ───
STATE_FILE = os.path.join(os.path.dirname(__file__), "clawtrader_state.json")

def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except:
        return {"doge_price": 0, "btc_price": 0, "doge_pnl": 0, "doge_dist_stop": 99, "last_full_report": 0}

def save_state(s):
    with open(STATE_FILE, 'w') as f:
        json.dump(s, f)

# ─── Binance signed GET ───
def bg(endpoint, params):
    p = params.copy()
    p['timestamp'] = int(time.time() * 1000)
    p['recvWindow'] = 60000
    qs = '&'.join(f"{k}={v}" for k, v in sorted(p.items()))
    sig = hmac.new(BIN_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{qs}&signature=***"
    r = requests.get(url, headers=BIN_HEADERS, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()

# ─── Binance signed POST/DELETE ───
def bp(endpoint, method, params):
    p = params.copy()
    p['timestamp'] = int(time.time() * 1000)
    p['recvWindow'] = 60000
    qs = '&'.join(f"{k}={v}" for k, v in sorted(p.items()))
    sig = hmac.new(BIN_SECRET.encode(), qs.encode(), hashlib.sha256).hexdigest()
    url = f"https://api.binance.com{endpoint}?{qs}&signature=***"
    if method == 'DELETE':
        r = requests.delete(url, headers=BIN_HEADERS, timeout=10)
    else:
        r = requests.post(url, headers=BIN_HEADERS, timeout=10)
    return r.json() if r.status_code == 200 else None

# ─── DOGE Snapshot ───
def get_doge():
    r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=DOGEUSDT", timeout=5)
    doge_price = float(r.json()['price'])
    
    s24 = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=DOGEUSDT", timeout=5).json()
    
    bal = bg("/api/v3/account", {})
    usdt_free = 0.0; doge_free = 0.0; doge_locked = 0.0
    if bal:
        for b in bal['balances']:
            if b['asset'] == 'USDT': usdt_free = float(b['free'])
            if b['asset'] == 'DOGE':
                doge_free = float(b['free'])
                doge_locked = float(b['locked'])
    
    orders = bg("/api/v3/openOrders", {"symbol": "DOGEUSDT"}) or []
    
    # Posición real desde balance
    qty = doge_free + doge_locked
    h24 = float(s24.get('highPrice', doge_price))
    l24 = float(s24.get('lowPrice', doge_price))
    pos = ((doge_price - l24) / (h24 - l24)) * 100 if (h24 - l24) > 0 else 50
    ds = (doge_price / 0.09450 - 1) * 100
    
    # Si no tenemos DOGE, reporte en modo observación
    if qty < 30:
        return {
            'p': doge_price, 'pnl': 0, 'pnl_pct': 0,
            'val': 0, 'cost': 0, 'entry': doge_price, 'qty': 0,
            'h24': h24, 'l24': l24, 'pos': pos, 'ds': ds,
            'usdt_free': usdt_free, 'doge_free': 0,
            'orders': [], 'no_position': True
        }
    
    # Posición activa — hardcodeada para esta sesión
    entry = 0.09593
    cost = entry * 242.0
    value = doge_price * qty
    pnl = value - cost
    pnl_pct = (doge_price / entry - 1) * 100
    
    return {
        'p': doge_price, 'pnl': pnl, 'pnl_pct': pnl_pct,
        'val': value, 'cost': cost, 'entry': entry, 'qty': qty,
        'h24': h24, 'l24': l24, 'pos': pos, 'ds': ds,
        'usdt_free': usdt_free, 'doge_free': doge_free,
        'orders': orders, 'no_position': False
    }

# ─── Market snapshot (no auth) ───
def get_market():
    syms = ['BTCUSDT','ETHUSDT','SOLUSDT','BNBUSDT','DOGEUSDT']
    m = {}
    for s in syms:
        try:
            r = requests.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={s}", timeout=5)
            j = r.json()
            nm = s.replace('USDT','')
            p = float(j['lastPrice'])
            hi = float(j['highPrice'])
            lo = float(j['lowPrice'])
            ch = float(j['priceChangePercent'])
            rsi = ((p - lo) / (hi - lo)) * 100 if hi != lo else 50
            m[nm] = {'p': p, 'ch': ch, 'hi': hi, 'lo': lo, 'rsi': max(0,min(100,rsi))}
        except:
            m[s.replace('USDT','')] = {'p': 0, 'ch': 0}
    return m

# ─── Alpaca stocks ───
def get_alpaca():
    stocks = {
        'SPY': 'SPY', 'QQQ': 'QQQ', 'AAPL': 'AAPL',
        'AMZN': 'AMZN', 'TSLA': 'TSLA', 'GOOGL': 'GOOGL'
    }
    res = {}
    for nm, sym in stocks.items():
        try:
            r = requests.get(f"https://data.alpaca.markets/v2/stocks/{sym}/trades/latest", headers=ALPACA_HEADERS, timeout=5)
            if r.status_code == 200:
                p = float(r.json()['trade']['p'])
                r2 = requests.get(f"https://data.alpaca.markets/v2/stocks/{sym}/snapshot", headers=ALPACA_HEADERS, timeout=5)
                if r2.status_code == 200:
                    pc = float(r2.json().get('prevDailyBar', {}).get('c', p))
                    ch = ((p / pc) - 1) * 100
                else:
                    ch = 0.0
                res[nm] = {'p': p, 'ch': ch}
        except:
            res[nm] = {'p': 0, 'ch': 0}
    return res

# ─── Build report text ───
def build(d, m, a, state, full):
    lines = []
    now = datetime.now().strftime("%H:%M")
    lines.append(f"📊 **CLAWTRADER — {now}**")
    lines.append("")
    
    # DOGE
    if d.get('no_position', False):
        lines.append(f"━━━ **🐶 DOGE/USDT** 🔴 **${d['p']:.5f}** ━━━")
        lines.append(f"**Sin posición abierta** | Capital disponible: **${d['usdt_free']:.2f}** (más ~${23.98-d['usdt_free']:.2f} en DOGE remanentes)")
        lines.append(f"Rango 24h: ${d['l24']:.5f} - ${d['h24']:.5f}")
        lines.append(f"Stop fantasma: $0.09450 | Distancia: {d['ds']:.1f}% — sin exposición")
    else:
        emoji = "🟢" if d['pnl'] >= 0 else ("🟡" if d['pnl'] > -0.30 else "🔴")
        lines.append(f"━━━ **🐶 DOGE/USDT** {'🟢' if d['pnl_pct']>=0 else '🔴'} **${d['p']:.5f}** ━━━")
        lines.append(f"PnL: **{d['pnl']:+.2f} USDT** ({d['pnl_pct']:+.2f}%)  |  Capital: **${d['val']+d['usdt_free']:.2f}**")
        lines.append(f"Entrada: ${d['entry']:.5f}  |  Cant: {d['qty']:.0f} DOGE  |  Inversión: ${d['cost']:.2f}")
        lines.append(f"Stop: $0.09450 → a **{d['ds']:.1f}%**  |  Rango 24h: ${d['l24']:.5f} - ${d['h24']:.5f} ({d['pos']:.0f}%)")
    
    if d['orders']:
        lines.append("")
        lines.append("━ **TARGETS** ━")
        for o in d['orders']:
            qty = float(o['origQty'])
            price = float(o['price'])
            gain = (price - d['entry']) * qty
            dist = (price / d['p'] - 1) * 100
            e = "💰" if dist < 4 else "🎯"
            lines.append(f"{e} VENDER {qty:.0f} @ ${price:.5f} → +${gain:.2f} (a {dist:.1f}%)")
    
    lines.append("")
    lines.append("━ **⚠️ ALERTAS** ━")
    if d.get('no_position', False):
        lines.append("🔍 **MODO OBSERVACIÓN** — sin posiciones abiertas")
        if d['p'] <= 0.09450:
            lines.append("DOGE tocó stop — bien que estamos fuera 👌")
    else:
        if d['p'] <= 0.09450:
            lines.append("🔴 **STOP LOSS — VENDER TODO AHORA**")
        elif d['ds'] < 0.5:
            lines.append("🔴 **STOP INMINENTE — prepárate**")
        elif d['ds'] < 1:
            lines.append("⚠️ Stop a menos de 1%")
        else:
            lines.append("✅ Stop seguro")
        
        if d['pnl'] > 0:
            lines.append(f"🟢 Ganando +${d['pnl']:.2f}")
        elif d['pnl'] >= -0.20:
            lines.append("🟡 Casi break-even")
        else:
            lines.append(f"🔴 {d['pnl']:.2f} USDT abajo")
    
    # Market
    lines.append("")
    lines.append("━━━ **🌍 CRIPTO** ━━━")
    for nm in ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE']:
        if nm in m:
            x = m[nm]
            ar = "🟢" if x['ch'] >= 0 else "🔴"
            if nm == 'DOGE':
                ln = f"• DOGE **${x['p']:,.4f}** {ar} ({x['ch']:+.1f}%) 🐶"
            else:
                ln = f"• {nm} **${x['p']:,.0f}** {ar} ({x['ch']:+.1f}%)"
            if nm != 'DOGE':
                if x.get('rsi', 50) < 20:
                    ln += " 💀"
                elif x.get('rsi', 50) < 35:
                    ln += " ⚡"
                elif x.get('rsi', 50) > 65:
                    ln += " 🔥"
            lines.append(ln)
    
    # Stocks
    lines.append("")
    lines.append("━━━ **🏛️ STOCKS** ━━━")
    lines.append("Alpaca: **$100,873.55** | 100% cash")
    top_list = []
    for nm, x in a.items():
        ar = "🟢" if x.get('ch',0) >= 0 else "🔴"
        top_list.append(f"{ar} {nm} ${x['p']:.2f} ({x['ch']:+.1f}%)")
    if top_list:
        lines.append("Watchlist:")
        for t in top_list[:6]:
            lines.append(f"  {t}")

    # Changes
    lines.append("")
    lines.append("━━━ **📊 CAMBIOS** ━━━")
    changes = []
    if d['pnl'] >= 0 and state.get('doge_pnl', -1) < 0:
        changes.append("**DOGE salió a positivo** 🟢")
    if d['ds'] >= 1.5 and state.get('doge_dist_stop', 0) < 1:
        changes.append("Peligro de stop disipado ✅")
    bp = m.get('BTC', {}).get('p', 0)
    old_bp = state.get('btc_price', 0)
    if abs(bp - old_bp) > 500 and old_bp > 0:
        changes.append(f"BTC: ${old_bp:,.0f} → **${bp:,.0f}**")
    old_dp = state.get('doge_price', 0)
    if old_dp > 0:
        dp_chg = ((d['p'] / old_dp) - 1) * 100
        if abs(dp_chg) > 1:
            changes.append(f"DOGE: ${old_dp:.5f} → **${d['p']:.5f}** ({dp_chg:+.2f}%)")

    if not changes:
        lines.append("Sin cambios relevantes. Todo estable.")
    else:
        for c in changes:
            lines.append(c)

    # Update state
    state['doge_pnl'] = d['pnl']
    state['doge_price'] = d['p']
    state['doge_dist_stop'] = d['ds']
    state['btc_price'] = m.get('BTC', {}).get('p', 0)
    state['last_full_report'] = time.time()
    save_state(state)

    if full:
        lines.append("")
        lines.append("📅 **Próximo full reporte en 10 min**")
        lines.append("⚠️ Solo envío alerta entre reportes si hay cambios relevantes.")

    return "\n".join(lines)

# ─── ENTRY ───
def main():
    state = load_state()
    d = get_doge()
    m = get_market()
    a = get_alpaca()
    
    now = time.time()
    last_full = state.get('last_full_report', 0)
    full = (now - last_full) >= 600  # 10 min for full report
    
    report = build(d, m, a, state, full)
    print(report)

if __name__ == "__main__":
    main()
