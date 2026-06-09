#!/usr/bin/env python3
"""Monitor ETH spot position - alerts on significant changes"""
import requests as r, hmac, hashlib, time, json, os, sys
from urllib.parse import urlencode
from load_env import load_env

load_env()

def get_keys():
    API_KEY = os.environ.get("BINANCE_API_KEY")
    SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
    if not API_KEY or not SECRET_KEY:
        raise RuntimeError("BINANCE_API_KEY y BINANCE_SECRET_KEY no están configuradas")
    return API_KEY, SECRET_KEY

def get_balance(API_KEY, SECRET_KEY):
    h = {"X-MBX-APIKEY": API_KEY}
    st = r.get("https://api.binance.com/api/v3/time", timeout=5).json()["serverTime"]
    params = {"timestamp": st}
    q = urlencode(params)
    s = hmac.new(SECRET_KEY.encode(), q.encode(), hashlib.sha256).hexdigest()
    acc = r.get(f"https://api.binance.com/api/v3/account?{q}&signature={s}", headers=h, timeout=10).json()
    
    eth = 0
    usdt = 0
    eth_locked = 0
    for b in acc.get("balances", []):
        if b["asset"] == "ETH":
            eth = float(b["free"])
            eth_locked = float(b["locked"])
        elif b["asset"] == "USDT":
            usdt = float(b["free"])
    
    p = float(r.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()["price"])
    total_usd = (eth + eth_locked) * p + usdt
    
    return {
        "eth": eth,
        "eth_locked": eth_locked,
        "usdt": usdt,
        "price": p,
        "total_usd": total_usd,
        "position_value": (eth + eth_locked) * p
    }

if __name__ == "__main__":
    API_KEY, SECRET_KEY = get_keys()
    data = get_balance(API_KEY, SECRET_KEY)
    print(json.dumps(data, indent=2))
    
    if data["price"] < 1580:
        print("ALERTA: ETH bajo ${:.2f}".format(data["price"]))
    if data["eth"] == 0 and data["eth_locked"] == 0:
        print("Posicion ETH cerrada")
