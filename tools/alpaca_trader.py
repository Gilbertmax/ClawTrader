#!/usr/bin/env python3
"""
AlpacaTrader — Ejecución de órdenes via Alpaca Paper Trading API
Usa REST API directamente (sin librerías) para consistencia.
"""
import requests, json, time, warnings, os
from load_env import env_bool, load_env
warnings.filterwarnings("ignore")
load_env()

API_KEY = os.environ.get("ALPACA_API_KEY", "NOT_SET")
API_SECRET = os.environ.get("ALPACA_SECRET_KEY", "NOT_SET")
BASE = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets/v2")
DRY_RUN = env_bool("CLAWTRADER_DRY_RUN", True)
LIVE_TRADING = env_bool("CLAWTRADER_LIVE_TRADING", False)
HEADERS = {
    "APCA-API-KEY-ID": API_KEY,
    "APCA-API-SECRET-KEY": API_SECRET,
    "Content-Type": "application/json"
}

def log(msg):
    print(f"  {msg}")

class AlpacaTrader:
    def __init__(self):
        self._verify()
    
    def _get(self, path, params=None):
        if DRY_RUN or not LIVE_TRADING:
            if path == "/account":
                return {"status": "ACTIVE", "equity": "0", "cash": "0", "buying_power": "0"}
            if path in ("/positions", "/orders"):
                return []
            return {"dry_run": True, "path": path, "params": params or {}}
        r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params)
        return r.json() if r.status_code == 200 else {"error": r.text}
    
    def _post(self, path, data):
        if DRY_RUN or not LIVE_TRADING:
            return {"dry_run": True, "path": path, "data": data, "id": "dry-run", "status": "accepted"}
        r = requests.post(f"{BASE}{path}", headers=HEADERS, json=data)
        return r.json() if r.status_code in (200, 201) else {"error": r.text, "code": r.status_code}
    
    def _delete(self, path):
        r = requests.delete(f"{BASE}{path}", headers=HEADERS)
        return r.status_code in (200, 204)
    
    def _verify(self):
        if DRY_RUN or not LIVE_TRADING:
            return
        a = self._get("/account")
        assert a.get("status") == "ACTIVE", f"Cuenta no activa: {a.get('status')}"
    
    @property
    def account(self):
        return self._get("/account")
    
    @property
    def equity(self):
        return float(self.account.get("equity", 0))
    
    @property
    def cash(self):
        return float(self.account.get("cash", 0))
    
    @property
    def buying_power(self):
        return float(self.account.get("buying_power", 0))
    
    def positions(self):
        p = self._get("/positions")
        return p if isinstance(p, list) else []
    
    def orders(self, status="open"):
        o = self._get("/orders", {"status": status})
        return o if isinstance(o, list) else []
    
    def cancel_all(self):
        return self._delete("/orders")
    
    def bracket_buy(self, symbol, qty, take_profit, stop_loss, tif="day"):
        """
        ORDEN BRACKET COMPLETA — Entry MARKET + Take Profit LIMIT + Stop Loss STOP
        Todo en una sola orden. Alpaca la maneja como OCO internamente.
        
        Args:
            symbol: Símbolo (SPY, MSFT, AAPL, etc.)
            qty: Cantidad de shares
            take_profit: Precio límite de venta (profit)
            stop_loss: Precio disparador de stop (loss)
            tif: "day" o "gtc"
        """
        tif_str = "day" if tif == "day" else "gtc"
        
        data = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": "buy",
            "type": "market",
            "time_in_force": tif_str,
            "order_class": "bracket",
            "take_profit": {"limit_price": str(take_profit)},
            "stop_loss": {"stop_price": str(stop_loss)}
        }
        
        log(f"Enviando bracket BUY {qty} {symbol} | TP {take_profit} | SL {stop_loss}")
        result = self._post("/orders", data)
        
        if "error" in result:
            log(f"❌ Error: {result.get('error', 'desconocido')[:200]}")
            return None
        
        log(f"✅ Bracket creado: {result.get('id', '?')[:12]} | Status: {result.get('status')}")
        return result
    
    def bracket_sell(self, symbol, qty, take_profit, stop_loss, tif="day"):
        """Bracket para venta en corto"""
        tif_str = "day" if tif == "day" else "gtc"
        
        data = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": "sell",
            "type": "market",
            "time_in_force": tif_str,
            "order_class": "bracket",
            "take_profit": {"limit_price": str(take_profit)},
            "stop_loss": {"stop_price": str(stop_loss)}
        }
        
        log(f"Enviando bracket SELL {qty} {symbol} | TP {take_profit} | SL {stop_loss}")
        result = self._post("/orders", data)
        
        if "error" in result:
            log(f"❌ Error: {result.get('error', 'desconocido')[:200]}")
            return None
        
        log(f"✅ Bracket creado: {result.get('id', '?')[:12]} | Status: {result.get('status')}")
        return result
    
    def market_buy(self, symbol, qty, tif="day"):
        """Orden market simple de compra"""
        data = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": "buy",
            "type": "market",
            "time_in_force": "day" if tif == "day" else "gtc",
        }
        return self._post("/orders", data)
    
    def market_sell(self, symbol, qty, tif="day"):
        """Orden market simple de venta"""
        data = {
            "symbol": symbol.upper(),
            "qty": str(qty),
            "side": "sell",
            "type": "market",
            "time_in_force": "day" if tif == "day" else "gtc",
        }
        return self._post("/orders", data)
    
    def status(self, verbose=False):
        """Reporte de estado completo"""
        a = self.account
        ps = self.positions()
        os = self.orders()
        
        lines = []
        lines.append(f"Capital: ${float(a['equity']):,.2f}")
        lines.append(f"Cash: ${float(a['cash']):,.2f}")
        lines.append(f"Buying Power: ${float(a['buying_power']):,.2f}")
        lines.append(f"Posiciones: {len(ps)}")
        
        for p in ps:
            pnl = float(p.get("unrealized_pl", 0))
            pnl_pct = float(p.get("unrealized_plpc", 0)) * 100
            lines.append(f"  {p['symbol']} | {p['qty']} sh | Entry ${p['avg_entry_price']} | PnL ${pnl:.2f} ({pnl_pct:+.2f}%)")
        
        lines.append(f"Órdenes activas: {len(os)}")
        for o in os:
            lines.append(f"  {o['symbol']} | {o['side']} | {o['qty']} | {o['type']} | {o.get('status','?')}")
        
        if verbose:
            lines.append(f"Day PnL: ${float(a.get('equity','0')) - float(a.get('last_equity', a.get('equity','0'))):.2f}")
        
        return "\n".join(lines)


def test():
    """Prueba rápida de conexión"""
    t = AlpacaTrader()
    print("=" * 50)
    print("ALPACA TRADER — PRUEBA")
    print("=" * 50)
    print(t.status())
    print()
    print("✅ Conexión exitosa")
    return t


def test_bracket():
    """Prueba bracket order con 1 share SPY"""
    t = AlpacaTrader()
    print("=" * 50)
    print("PRUEBA BRACKET ORDER — 1 SPY")
    print("=" * 50)
    
    # Obtener precio actual de SPY
    bars = requests.get(
        "https://data.alpaca.markets/v2/stocks/SPY/bars?timeframe=1Min&limit=1&sort=desc",
        headers=HEADERS
    ).json()
    
    if "bars" in bars and bars["bars"].get("SPY"):
        price = float(bars["bars"]["SPY"][0]["c"])
        print(f"Precio actual SPY: ${price:.2f}")
        tp = round(price * 1.005, 2)  # +0.5%
        sl = round(price * 0.995, 2)  # -0.5%
        print(f"TP: ${tp} | SL: ${sl}")
        
        result = t.bracket_buy("SPY", 1, tp, sl)
        if result:
            print(f"✅ Bracket ID: {result.get('id')[:12]}")
            
            # Esperar fill
            time.sleep(3)
            print(f"\n{t.status()}")
        else:
            print("❌ Bracket falló")
    else:
        print("No se pudo obtener precio de SPY")
        print("Probando bracket sin precio")
        result = t.bracket_buy("SPY", 1, 600.00, 580.00)
        print(result)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test-bracket":
        test_bracket()
    else:
        test()
