#!/usr/bin/env python3
"""
clawtrader_dual.py v2 — Monitoreo autónomo Alpaca + Binance.
CON HMAC CORREGIDO (urlencode para POST).
Escribe /tmp/clawtrader_status.json al finalizar.
"""
import json, os, time, hmac, hashlib
from datetime import datetime
from urllib.parse import urlencode
import requests as r
import yfinance as yf
from load_env import env_bool, env_float, load_env, status_dir

load_env()

# ===== CREDENTIALS =====
# Cargadas de variables de entorno
ALPACA_KEY = os.environ.get("ALPACA_API_KEY", "NOT_SET")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET_KEY", "NOT_SET")
ALPACA_URL = "https://paper-api.alpaca.markets"
ALPACA_HEADERS = {"APCA-API-KEY-ID": ALPACA_KEY, "APCA-API-SECRET-KEY": ALPACA_SECRET}

BINANCE_KEY = os.environ.get("BINANCE_API_KEY", "NOT_SET")
BINANCE_SECRET = os.environ.get("BINANCE_SECRET_KEY", "NOT_SET")
BINANCE_API = "https://api.binance.com"
BINANCE_HEADERS = {"X-MBX-APIKEY": BINANCE_KEY}

STATUS_FILE = status_dir() / "clawtrader_status.json"
DRY_RUN = env_bool("CLAWTRADER_DRY_RUN", True)
LIVE_TRADING = env_bool("CLAWTRADER_LIVE_TRADING", False)
CAPITAL = env_float("CLAWTRADER_CAPITAL", 1000)

# ===== BINANCE HELPERS (URLENCODE CORRECTO) =====
def binance_signed(params):
    """Firma HMAC-SHA256 con urlencode para POST/GET"""
    st = r.get(f"{BINANCE_API}/api/v3/time", timeout=5).json()["serverTime"]
    params["timestamp"] = st
    params["recvWindow"] = 5000
    query = urlencode(sorted(params.items()))
    sig = hmac.new(BINANCE_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query, sig

def binance_account():
    if BINANCE_KEY == "NOT_SET" or BINANCE_SECRET == "NOT_SET":
        return DummyResponse(401, {"error": "Binance credentials not configured"})
    query, sig = binance_signed({})
    url = f"{BINANCE_API}/api/v3/account?{query}&signature={sig}"
    return r.get(url, headers=BINANCE_HEADERS, timeout=10)

def binance_market_buy(symbol, quote_qty):
    """Compra market usando quoteOrderQty"""
    params = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": f"{quote_qty:.2f}",
        "newOrderRespType": "FULL"
    }
    query, sig = binance_signed(params)
    url = f"{BINANCE_API}/api/v3/order?{query}&signature={sig}"
    if DRY_RUN or not LIVE_TRADING:
        return DummyResponse(200, {"dry_run": True, "symbol": symbol, "quoteOrderQty": quote_qty, "fills": []})
    return r.post(url, headers=BINANCE_HEADERS, timeout=10)

def binance_oco_sell(symbol, qty, price, stop, t1):
    """OCO sell: stop loss + take profit"""
    buy_price = price
    t1_pct = 1.025
    stop_pct = 0.985
    # Si price es el actual, usar %. Si ya es target, dejarlo
    if t1 == price * t1_pct:
        t1_final = round(price * t1_pct, 2)
        stop_final = round(price * stop_pct, 2)
    else:
        t1_final = t1
        stop_final = stop
    
    params = {
        "symbol": symbol,
        "side": "SELL",
        "quantity": str(qty),
        "price": f"{t1_final:.8f}".rstrip('0').rstrip('.'),
        "stopPrice": f"{stop_final:.8f}".rstrip('0').rstrip('.'),
        "stopLimitPrice": f"{stop_final:.8f}".rstrip('0').rstrip('.'),
        "stopLimitTimeInForce": "GTC"
    }
    query, sig = binance_signed(params)
    url = f"{BINANCE_API}/api/v3/order/oco?{query}&signature={sig}"
    if DRY_RUN or not LIVE_TRADING:
        return DummyResponse(200, {"dry_run": True, "orderReports": []})
    return r.post(url, headers=BINANCE_HEADERS, timeout=10)

class DummyResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body

# ===== STOCK ANALYSIS (yfinance) =====
def analyze_stock(sym):
    try:
        t = yf.Ticker(sym)
        df = t.history(period='5d', interval='15m')
        if df.empty:
            return {"symbol": sym, "error": "no data", "entry": None}
        close = df['Close']
        cur = float(close.iloc[-1])
        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta.where(delta < 0, 0.0))
        ag = gain.rolling(14).mean()
        al = loss.rolling(14).mean()
        rs = ag / al
        rsi = round(float(rs.iloc[-1]), 1) if float(al.iloc[-1]) > 0 else 100.0
        ema9 = round(float(close.ewm(span=9).mean().iloc[-1]), 2)
        try:
            df1m = t.history(period='1d', interval='1m')
            ld = float(df1m['Low'].min())
            hd = float(df1m['High'].max())
            pos = round((cur - ld) / (hd - ld) * 100, 1) if hd > ld else 50
        except:
            pos = 50
        last5 = close.tail(5)
        hl = bool(last5.iloc[-1] > min(last5.iloc[:-1]))
        lastk = df.iloc[-1]
        bc = bool(lastk['Close'] >= lastk['Open'])
        bc3 = sum(1 for i in range(-3, 0) if df.iloc[i]['Close'] >= df.iloc[i]['Open'])
        
        result = {
            "symbol": sym,
            "price": round(cur, 2),
            "rsi": rsi,
            "pos_pct": pos,
            "ema9": ema9,
            "above_ema9": bool(cur > ema9),
            "hl": bool(hl),
            "bc": bool(bc),
            "bc3": bc3,
            "conditions": {
                "pos": bool(pos <= 60),
                "rsi": bool(rsi >= 25 and rsi <= 65),
                "hl": bool(hl),
                "bc": bool(bc)
            }
        }
        if all([pos <= 60, rsi >= 25, rsi <= 65, hl, bc]):
            risk_pct = 0.0085
            stop = round(cur * (1 - risk_pct), 2)
            t1 = round(cur * 1.003, 2)
            t2 = round(cur * 1.006, 2)
            rr = round((t1 - cur) / (cur - stop), 2)
            result["entry"] = {
                "exchange": "alpaca",
                "symbol": sym,
                "price": cur,
                "stop": stop,
                "target1": t1,
                "target2": t2,
                "rr": rr,
                "qty": 1  # test 1 share
            }
        return result
    except Exception as e:
        return {"symbol": sym, "error": str(e)[:50], "entry": None}

# ===== CRYPTO ANALYSIS (Binance klines) =====
def get_rsi(closes, period=14):
    if len(closes) <= period:
        return 50
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0:
        return 100
    return 100 - (100 / (1 + ag / al))

def analyze_crypto(symbol, name, min_notional, balance_usdt):
    try:
        resp = r.get(f"{BINANCE_API}/api/v3/klines", params={"symbol": symbol, "interval": "15m", "limit": 96}, timeout=10)
        if resp.status_code != 200:
            return {"symbol": name, "error": f"API {resp.status_code}", "entry": None}
        data = resp.json()
        closes = [float(k[4]) for k in data]
        cur = closes[-1]
        rsi = round(get_rsi(closes), 1)
        h24 = max(float(k[2]) for k in data)
        l24 = min(float(k[3]) for k in data)
        pos = (cur - l24) / (h24 - l24) * 100 if h24 > l24 else 50
        ema9 = sum(closes[-9:]) / 9
        above9 = cur > ema9
        last5 = [float(k[4]) for k in data[-5:]]
        hl = last5[-1] > min(last5[:-1])
        last_k = data[-1]
        bc = float(last_k[4]) >= float(last_k[1])
        bc3 = sum(1 for i in range(-3, 0) if float(data[i][4]) >= float(data[i][1]))
        
        result = {
            "symbol": name,
            "price": round(cur, 2),
            "rsi": rsi,
            "pos_pct": round(pos, 1),
            "above_ema9": bool(above9),
            "hl": bool(hl),
            "bc": bool(bc),
            "bc3": bc3,
            "min_notional": min_notional,
            "conditions": {
                "pos": bool(pos <= 60),
                "rsi": bool(rsi >= 25 and rsi <= 65),
                "hl": bool(hl),
                "bc": bool(bc)
            }
        }
        if all([pos <= 60, rsi >= 25, rsi <= 65, hl, bc]):
            # Invertir 50% del balance (si alcanza min_notional)
            invest = min(balance_usdt * 0.5, balance_usdt - 0.05)
            if invest >= min_notional:
                qty = round(invest / cur, 4)
                result["entry"] = {
                    "exchange": "binance",
                    "symbol": symbol,
                    "name": name,
                    "qty": qty,
                    "price": round(cur, 2),
                    "invest_usd": round(qty * cur, 2),
                    "stop": round(cur * 0.985, 2),
                    "target1": round(cur * 1.025, 2),
                    "rr": round(1.025 / 0.985, 2)
                }
        return result
    except Exception as e:
        return {"symbol": name, "error": str(e)[:50], "entry": None}

# ===== ALPACA BRACKET =====
def alpaca_bracket(sym, qty, price, stop, t1):
    payload = {
        "symbol": sym,
        "qty": str(qty),
        "side": "buy",
        "type": "limit",
        "limit_price": str(price),
        "time_in_force": "day",
        "order_class": "bracket",
        "take_profit": {"limit_price": str(t1)},
        "stop_loss": {"stop_price": str(stop), "limit_price": str(stop)}
    }
    if DRY_RUN or not LIVE_TRADING:
        return DummyResponse(200, {"dry_run": True, "id": "dry-run", "payload": payload})
    return r.post(f"{ALPACA_URL}/v2/orders", headers=ALPACA_HEADERS, json=payload, timeout=10)

# ===== ASSETS TO MONITOR =====
STOCK_SYMBOLS = ["MSFT", "NVDA", "QQQ", "AAPL", "GOOGL", "AMZN", "TSLA", "SPY"]

# Crypto pairs con su minNotional
# DOGE min=1, SOL/BTC/ETH/BNB min=5
CRYPTO_CONFIGS = [
    ("SOLUSDT",   "SOL/USDT",   5.0),
    ("BTCUSDT",   "BTC/USDT",   5.0),
    ("ETHUSDT",   "ETH/USDT",   5.0),
    ("BNBUSDT",   "BNB/USDT",   5.0),
    ("DOGEUSDT",  "DOGE/USDT",  1.0),
]

# ===== MAIN =====
if __name__ == "__main__":
    ts = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    results = {
        "timestamp": ts,
        "stocks": {},
        "crypto": {},
        "alpaca": {},
        "binance_balance": {},
        "entry": None,
        "execution": None,
        "error": None
    }
    
    print(f"🤖 CLAWTRADER DUAL v2 - {ts}", flush=True)
    print("=" * 50, flush=True)
    
    # --- STOCKS ---
    print("\n📈 STOCKS (Alpaca):", flush=True)
    for sym in STOCK_SYMBOLS:
        res = analyze_stock(sym)
        results["stocks"][sym] = res
        if "error" in res:
            print(f"  {sym}: ❌ {res['error']}", flush=True)
        else:
            e = "⏳"
            if "entry" in res:
                e = "✅"
            c = res["conditions"]
            print(f"  {sym:6} ${res['price']:<8} RSI:{res['rsi']:<5} Pos:{res['pos_pct']}% HL:{int(res['hl'])} BC:{int(res['bc'])} {e}", flush=True)
    
    # Alpaca account
    try:
        if ALPACA_KEY == "NOT_SET" or ALPACA_SECRET == "NOT_SET":
            a_resp = DummyResponse(401, {"error": "Alpaca credentials not configured"})
        else:
            a_resp = r.get(f"{ALPACA_URL}/v2/account", headers=ALPACA_HEADERS, timeout=5)
        if a_resp.status_code == 200:
            a = a_resp.json()
            results["alpaca"] = {"equity": float(a["equity"]), "cash": float(a["cash"])}
            print(f"\n💰 Alpaca: ${float(a['equity']):>10,.2f} | Cash: ${float(a['cash']):>10,.2f}", flush=True)
        else:
            print(f"\n❌ Alpaca API error: {a_resp.status_code}", flush=True)
            results["error"] = f"Alpaca HTTP {a_resp.status_code}"
    except Exception as e:
        print(f"\n❌ Alpaca error: {e}", flush=True)
        results["error"] = str(e)
    
    # --- CRYPTO ---
    print("\n🔵 CRYPTO (Binance):", flush=True)
    
    usdt_bal = 0.0
    try:
        resp = binance_account()
        if resp.status_code == 200:
            for b in resp.json()["balances"]:
                if b["asset"] == "USDT":
                    usdt_bal = float(b["free"])
                    break
            print(f"💰 Binance: ${usdt_bal:.2f} USDT", flush=True)
        else:
            print(f"❌ Binance account error: {resp.status_code}", flush=True)
    except Exception as e:
        print(f"❌ Binance account error: {e}", flush=True)
    
    results["binance_balance"] = {"USDT": usdt_bal}
    
    for symbol, name, min_not in CRYPTO_CONFIGS:
        res = analyze_crypto(symbol, name, min_not, usdt_bal)
        results["crypto"][symbol] = res
        if "error" in res:
            print(f"  {name:10} ❌ {res['error']}", flush=True)
        else:
            e = "⏳"
            if "entry" in res and res["entry"]:
                e = "✅"
            c = res["conditions"]
            print(f"  {name:10} ${res['price']:<8} RSI:{res['rsi']:<5} Pos:{res['pos_pct']}% HL:{int(res['hl'])} BC:{int(res['bc'])} {e}", flush=True)
    
    # --- DETECT ENTRY ---
    best_entry = None
    
    # Priorizar stocks
    for sym, res in results["stocks"].items():
        if "entry" in res and res["entry"]:
            best_entry = res["entry"]
            best_entry["asset_type"] = "stock"
            break
    
    # Si no hay stock, buscar crypto
    if not best_entry:
        for sym, res in results["crypto"].items():
            if "entry" in res and res["entry"]:
                # Verificar que tengamos fondos
                needed = res["entry"].get("invest_usd", res["entry"].get("min_notional", 10))
                if usdt_bal >= needed:
                    best_entry = res["entry"]
                    best_entry["asset_type"] = "crypto"
                    break
    
    # --- EXECUTE ---
    if best_entry and best_entry["asset_type"] == "stock":
        e = best_entry
        results["entry"] = e
        print(f"\n⚡ ENTRADA STOCK: {e['symbol']} @ ${e['price']:.2f} | Stop ${e['stop']} | T1 ${e['target1']} | R:R {e['rr']}", flush=True)
        
        code, body = "", ""
        try:
            resp = alpaca_bracket(e["symbol"], 1, e["price"], e["stop"], e["target1"])
            code = resp.status_code
            body = resp.json()
        except Exception as ex:
            code = 0
            body = str(ex)
        
        ox = {"symbol": e["symbol"], "qty": 1, "status": code, "response": str(body)[:200]}
        results["execution"] = ox
        
        if code == 200 and body.get("id"):
            print(f"✅ Alpaca bracket ENVIADA: {body.get('id')}", flush=True)
        else:
            print(f"❌ Alpaca bracket FALLÓ: {code} - {body.get('message', str(body)[:100])}", flush=True)
    
    elif best_entry and best_entry["asset_type"] == "crypto":
        e = best_entry
        results["entry"] = e
        invest = e.get("invest_usd", usdt_bal * 0.5)
        
        print(f"\n⚡ ENTRADA CRYPTO: {e['name']} | ${invest:.2f} @ ${e['price']} | Stop ${e['stop']} | T1 ${e['target1']} | R:R {e['rr']}", flush=True)
        
        # Comprar market
        print(f"\n🔫 Comprando {invest:.2f} USDT de {e['symbol']}...", flush=True)
        try:
            buy_resp = binance_market_buy(e["symbol"], invest)
            buy_code = buy_resp.status_code
            buy_body = buy_resp.json()
            
            if buy_code == 200:
                fills = buy_body.get("fills", [])
                filled_qty = sum(float(f["qty"]) for f in fills)
                avg_price = float(buy_body.get("avgPrice", e["price"]))
                print(f"✅ COMPRA EJECUTADA: {filled_qty} @ ${avg_price:.2f}", flush=True)
                
                # OCO sell
                if filled_qty > 0:
                    qty_str = f"{filled_qty:.8f}".rstrip('0').rstrip('.')
                    print(f"🔫 Colocando OCO sell...", flush=True)
                    oco_resp = binance_oco_sell(e["symbol"], qty_str, avg_price, e["stop"], e["target1"])
                    oco_code = oco_resp.status_code
                    oco_body = oco_resp.json()
                    
                    if oco_code == 200:
                        print(f"✅ OCO sell COLOCADA: orders {len(oco_body.get('orderReports', []))}", flush=True)
                        results["execution"] = {
                            "buy": {"filled_qty": filled_qty, "avg_price": avg_price},
                            "oco": {"status": oco_code, "orders": oco_body.get("orderReports", [])[:3]}
                        }
                    else:
                        print(f"❌ OCO sell FALLÓ: {oco_body.get('msg', str(oco_body)[:200])}", flush=True)
                        results["execution"] = {
                            "buy": {"filled_qty": filled_qty, "avg_price": avg_price},
                            "oco_error": oco_body.get("msg", str(oco_body)[:200])
                        }
            else:
                print(f"❌ COMPRA FALLÓ: {buy_body.get('msg', str(buy_body)[:200])}", flush=True)
                results["execution"] = {"error": buy_body.get("msg", str(buy_body)[:200])}
                
        except Exception as ex:
            print(f"❌ EXCEPCIÓN: {ex}", flush=True)
            results["execution"] = {"error": str(ex)}
    
    else:
        print(f"\n⏳ Sin entrada. Monitoreando.", flush=True)
    
    # --- WRITE STATUS ---
    tmp = STATUS_FILE.with_suffix(STATUS_FILE.suffix + ".tmp")
    try:
        with open(tmp, 'w') as f:
            json.dump(results, f)
            f.flush()
            os.fsync(f.fileno())
        os.rename(tmp, STATUS_FILE)
        print(f"\n✅ Estado escrito en {STATUS_FILE}", flush=True)
    except Exception as ex:
        print(f"❌ Error escribiendo status: {ex}", flush=True)
