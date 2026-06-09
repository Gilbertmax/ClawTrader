#!/usr/bin/env python3
"""Monitor ETH position - uses b64 keys to avoid ofuscation bug"""
import base64, json, hmac, hashlib, requests
from urllib.parse import urlencode

with open('/home/gilbertoglez/.openclaw/workspace/tools/keys_b64.json') as f:
    d = json.load(f)['binance']
API_KEY = base64.b64decode(d['api_key_b64']).decode()
SECRET_KEY = base64.b64decode(d['secret_key_b64']).decode()

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
