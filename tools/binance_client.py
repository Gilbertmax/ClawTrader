#!/usr/bin/env python3
"""Small Binance REST client with safe defaults."""
import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import requests

from config import get_config

BINANCE_API = "https://api.binance.com"


class BinanceClient:
    def __init__(self):
        self.config = get_config()
        self.api_key = os.environ.get("BINANCE_API_KEY")
        self.secret = os.environ.get("BINANCE_SECRET_KEY")
        self.headers = {"X-MBX-APIKEY": self.api_key or ""}

    @property
    def configured(self):
        return bool(self.api_key and self.secret)

    def public_get(self, path, params=None):
        response = requests.get(f"{BINANCE_API}{path}", params=params or {}, timeout=10)
        response.raise_for_status()
        return response.json()

    def signed_request(self, method, path, params=None):
        if not self.configured:
            return {"error": "Binance credentials not configured"}

        payload = dict(params or {})
        payload["timestamp"] = int(time.time() * 1000)
        payload["recvWindow"] = 5000
        query = urlencode(sorted(payload.items()))
        signature = hmac.new(self.secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        url = f"{BINANCE_API}{path}?{query}&signature={signature}"
        response = requests.request(method, url, headers=self.headers, timeout=10)
        try:
            body = response.json()
        except ValueError:
            body = {"error": response.text}
        if response.status_code >= 400:
            return {"error": body, "status_code": response.status_code}
        return body

    def account(self):
        return self.signed_request("GET", "/api/v3/account")

    def balances(self):
        account = self.account()
        if "error" in account:
            return account
        return {
            row["asset"]: {
                "free": float(row["free"]),
                "locked": float(row["locked"]),
            }
            for row in account.get("balances", [])
            if float(row["free"]) or float(row["locked"])
        }

    def market_buy(self, symbol, quote_qty):
        if self.config.dry_run or not self.config.live_trading:
            return {"dry_run": True, "symbol": symbol, "quoteOrderQty": float(quote_qty)}
        return self.signed_request(
            "POST",
            "/api/v3/order",
            {
                "symbol": symbol,
                "side": "BUY",
                "type": "MARKET",
                "quoteOrderQty": f"{float(quote_qty):.2f}",
                "newOrderRespType": "FULL",
            },
        )

