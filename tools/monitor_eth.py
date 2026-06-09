#!/usr/bin/env python3
"""Monitor ETH spot position - alerts on significant changes"""
import requests as r, hmac, hashlib, time, json, os, sys
from urllib.parse import urlencode
import re

def get_keys():
    content = open("/home/gilbertoglez/.openclaw/workspace/tools/Binance Apikeys").read()
    API_KEY = re.search(r"Api key\s*=\s*(\S+)", content).group(1)
    SECRET_KEY = re.search(r"Secret Key\s*=\s*(\S+)", content).group(1)
    return API_KEY, SECRET_KEY

def get_balance(API_KEY, SECRET_KEY):
    h = {"X-MBX-APIKEY": API_KEY}
    st = r.get("https://api.binance.com/api/v3/time", timeout=5).json()["serverTime"]
    params = {"timestamp": st}
    q = urlencode(params)
    s = hmac.new(SECRET_KEY.encode(), q.encode(), hashlib.sha256).hexdigest()
    acc = r.get(f"https://api.binance.com/api/v3/account?{q}&signature=***", headers=h, timeout=10).json()
    
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
