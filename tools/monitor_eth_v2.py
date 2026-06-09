#!/usr/bin/env python3
"""Monitor ETH position using Binance credentials from the environment."""
import json, hmac, hashlib, os, requests
from urllib.parse import urlencode
from load_env import load_env

load_env()

API_KEY = os.environ.get("BINANCE_API_KEY")
SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY")
if not API_KEY or not SECRET_KEY:
    raise RuntimeError("BINANCE_API_KEY y BINANCE_SECRET_KEY no están configuradas")

h = {"X-MBX-APIKEY": API_KEY}
st = requests.get("https://api.binance.com/api/v3/time", timeout=5).json()["serverTime"]
q = urlencode({"timestamp": st})
s = hmac.new(SECRET_KEY.encode(), q.encode(), hashlib.sha256).hexdigest()
acc = requests.get(f"https://api.binance.com/api/v3/account?{q}&signature={s}", headers=h, timeout=10).json()

eth = usdt = eth_locked = 0
for b in acc.get("balances", []):
    if b["asset"] == "ETH":
        eth = float(b["free"])
        eth_locked = float(b["locked"])
    elif b["asset"] == "USDT":
        usdt = float(b["free"])

p = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()["price"])
print(json.dumps({"eth": eth, "locked": eth_locked, "usdt": usdt, "price": p, "value": (eth+eth_locked)*p, "total": (eth+eth_locked)*p+usdt}, indent=2))
