#!/usr/bin/env python3
"""Professional market intelligence engine for ClawTrader.

Public-data only: no credentials are required and no orders are placed.
"""
import math
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Optional

import numpy as np
import pandas as pd
import requests
import talib

from config import get_config
from risk import validate_trade

BINANCE_API = "https://api.binance.com"
TIMEFRAMES = ("15m", "1h", "4h", "1d")


@dataclass
class SymbolFilters:
    tick_size: Optional[float] = None
    step_size: Optional[float] = None
    min_notional: Optional[float] = None


def _request(path, params=None):
    response = requests.get(f"{BINANCE_API}{path}", params=params or {}, timeout=12)
    response.raise_for_status()
    return response.json()


def _decimal_round_down(value, step):
    if not step or step == 0:
        return float(value)
    d_value = Decimal(str(value))
    d_step = Decimal(str(step))
    return float((d_value / d_step).to_integral_value(rounding=ROUND_DOWN) * d_step)


def get_symbol_filters(symbol):
    try:
        data = _request("/api/v3/exchangeInfo", {"symbol": symbol})
        symbols = data.get("symbols", [])
        if not symbols:
            return SymbolFilters()
        filters = {row["filterType"]: row for row in symbols[0].get("filters", [])}
        price_filter = filters.get("PRICE_FILTER", {})
        lot_size = filters.get("LOT_SIZE", {})
        min_notional = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL") or {}
        return SymbolFilters(
            tick_size=float(price_filter.get("tickSize", 0)) or None,
            step_size=float(lot_size.get("stepSize", 0)) or None,
            min_notional=float(min_notional.get("minNotional", 0)) or None,
        )
    except Exception:
        return SymbolFilters()


def get_klines(symbol, interval, limit=250):
    data = _request("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    rows = []
    for row in data:
        rows.append(
            {
                "open_time": int(row[0]),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
                "close_time": int(row[6]),
                "quote_volume": float(row[7]),
                "trades": int(row[8]),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty and int(df.iloc[-1]["close_time"]) > int(time.time() * 1000):
        df = df.iloc[:-1].copy()
    return df


def get_24h(symbol):
    try:
        data = _request("/api/v3/ticker/24hr", {"symbol": symbol})
        return {
            "last": float(data.get("lastPrice", 0)),
            "quote_volume": float(data.get("quoteVolume", 0)),
            "price_change_pct": float(data.get("priceChangePercent", 0)),
            "high": float(data.get("highPrice", 0)),
            "low": float(data.get("lowPrice", 0)),
        }
    except Exception as exc:
        return {"error": str(exc)}


def indicators(df):
    if df is None or len(df) < 60:
        return {"error": "insufficient candles"}

    high = df["high"].to_numpy(dtype=float)
    low = df["low"].to_numpy(dtype=float)
    close = df["close"].to_numpy(dtype=float)
    volume = df["volume"].to_numpy(dtype=float)

    ema20 = talib.EMA(close, timeperiod=20)
    ema50 = talib.EMA(close, timeperiod=50)
    ema200 = talib.EMA(close, timeperiod=200)
    rsi = talib.RSI(close, timeperiod=14)
    adx = talib.ADX(high, low, close, timeperiod=14)
    atr = talib.ATR(high, low, close, timeperiod=14)
    macd, macd_signal, macd_hist = talib.MACD(close)
    bb_upper, bb_mid, bb_lower = talib.BBANDS(close, timeperiod=20)
    vol_ma20 = pd.Series(volume).rolling(20).mean().to_numpy()

    last = close[-1]
    atr_last = _safe_last(atr)
    bb_mid_last = _safe_last(bb_mid)
    bb_width = ((_safe_last(bb_upper) - _safe_last(bb_lower)) / bb_mid_last * 100) if bb_mid_last else 0
    position_lookback = close[-50:] if len(close) >= 50 else close
    range_low = float(np.min(position_lookback))
    range_high = float(np.max(position_lookback))
    range_pos = ((last - range_low) / (range_high - range_low) * 100) if range_high > range_low else 50
    volume_ratio = (volume[-1] / _safe_last(vol_ma20)) if _safe_last(vol_ma20) else 0

    return {
        "close": round(float(last), 8),
        "ema20": round(_safe_last(ema20), 8),
        "ema50": round(_safe_last(ema50), 8),
        "ema200": round(_safe_last(ema200), 8) if not math.isnan(_safe_last(ema200)) else None,
        "rsi": round(_safe_last(rsi), 2),
        "adx": round(_safe_last(adx), 2),
        "atr": round(atr_last, 8),
        "atr_pct": round((atr_last / last * 100), 3) if last else 0,
        "macd_hist": round(_safe_last(macd_hist), 8),
        "bb_width_pct": round(bb_width, 3),
        "volume_ratio": round(volume_ratio, 3),
        "range_position_pct": round(range_pos, 2),
        "return_lookback_pct": round(((last / close[-20]) - 1) * 100, 3) if len(close) > 20 and close[-20] else 0,
    }


def _safe_last(values):
    value = float(values[-1])
    return 0.0 if math.isnan(value) else value


def classify_timeframe(row):
    if "error" in row:
        return "unknown"

    up_stack = row["close"] > row["ema20"] > row["ema50"]
    down_stack = row["close"] < row["ema20"] < row["ema50"]
    strong_trend = row["adx"] >= 22
    high_vol = row["atr_pct"] >= 4.0 or row["bb_width_pct"] >= 10.0

    if up_stack and strong_trend:
        return "trend_up_high_vol" if high_vol else "trend_up"
    if down_stack and strong_trend:
        return "trend_down_high_vol" if high_vol else "trend_down"
    if row["adx"] < 17:
        return "range_high_vol" if high_vol else "range"
    return "transition"


def score_symbol(symbol):
    cfg = get_config()
    frames = {}
    for interval in TIMEFRAMES:
        try:
            frames[interval] = indicators(get_klines(symbol, interval))
            frames[interval]["regime"] = classify_timeframe(frames[interval])
        except Exception as exc:
            frames[interval] = {"error": str(exc), "regime": "unknown"}

    ticker = get_24h(symbol)
    filters = get_symbol_filters(symbol)
    current = frames.get("1h", {}).get("close") or ticker.get("last") or 0

    score, reasons, warnings = _score_components(frames, ticker)
    plan = _build_plan(current, frames, filters, score)
    validation = validate_trade(
        entry=plan["entry"],
        current_price=current,
        stop_loss=plan["stop_loss"],
        take_profit=plan["take_profit"],
        score=max(0, min(9, round(score / 10))),
        capital=cfg.capital,
        requested_amount=plan["suggested_amount"],
        btc_bearish=False,
        min_rr=1.2,
    )
    decision = _decision(score, validation, warnings)

    return {
        "symbol": symbol,
        "timestamp": int(time.time()),
        "price": current,
        "decision": decision,
        "score": round(score, 2),
        "confidence": round(min(100, max(0, score)), 2),
        "reasons": reasons,
        "warnings": warnings,
        "ticker_24h": ticker,
        "filters": {
            "tick_size": filters.tick_size,
            "step_size": filters.step_size,
            "min_notional": filters.min_notional,
        },
        "timeframes": frames,
        "plan": plan,
        "risk_validation": validation,
    }


def _score_components(frames, ticker):
    score = 50.0
    reasons = []
    warnings = []

    data_errors = [tf for tf in TIMEFRAMES if "error" in frames.get(tf, {})]
    if len(data_errors) == len(TIMEFRAMES):
        return 0.0, reasons, ["market data unavailable for all timeframes"]

    regimes = {tf: frames.get(tf, {}).get("regime", "unknown") for tf in TIMEFRAMES}
    higher_up = regimes.get("4h", "").startswith("trend_up") and regimes.get("1d", "") in {
        "trend_up",
        "transition",
        "range",
    }
    higher_down = regimes.get("4h", "").startswith("trend_down") or regimes.get("1d", "").startswith("trend_down")

    if higher_up:
        score += 16
        reasons.append("higher timeframes support bullish continuation")
    if higher_down:
        score -= 22
        warnings.append("higher timeframe trend is bearish")

    one_h = frames.get("1h", {})
    fifteen = frames.get("15m", {})
    if "error" in one_h:
        warnings.append("1h market data unavailable")
        score -= 15
    else:
        if one_h.get("rsi", 50) < 30:
            score += 7
            reasons.append("1h RSI is oversold")
        elif 45 <= one_h.get("rsi", 50) <= 65:
            score += 8
            reasons.append("1h RSI is in a constructive momentum band")
        elif one_h.get("rsi", 50) > 75:
            score -= 12
            warnings.append("1h RSI is overextended")

        if one_h.get("macd_hist", 0) > 0:
            score += 6
            reasons.append("1h MACD histogram is positive")
        else:
            score -= 4

        atr_pct = one_h.get("atr_pct", 0)
        if 0.4 <= atr_pct <= 3.5:
            score += 6
            reasons.append("1h volatility is tradable")
        elif atr_pct > 5:
            score -= 12
            warnings.append("1h volatility is elevated")

        if 15 <= one_h.get("range_position_pct", 50) <= 70:
            score += 6
            reasons.append("price is not chasing the top of its 1h range")
        elif one_h.get("range_position_pct", 50) > 85:
            score -= 10
            warnings.append("price is near the top of its recent 1h range")

    if "error" in fifteen:
        warnings.append("15m market data unavailable")
        score -= 8
    elif fifteen.get("volume_ratio", 0) >= 1.15:
        score += 5
        reasons.append("15m volume is above its 20-period average")
    elif fifteen.get("volume_ratio", 0) < 0.55:
        score -= 6
        warnings.append("15m volume is weak")

    if ticker.get("error"):
        warnings.append("24h ticker unavailable")
        score -= 10
    elif ticker.get("quote_volume", 0) >= 5_000_000:
        score += 5
        reasons.append("24h quote volume is liquid")
    else:
        score -= 8
        warnings.append("24h quote volume is thin")

    return max(0, min(100, score)), reasons, warnings


def _build_plan(current, frames, filters, confidence):
    one_h = frames.get("1h", {})
    atr = one_h.get("atr") or current * 0.015
    entry = current
    stop = current - atr * 1.6
    take_profit = current + atr * 2.4
    rr = (take_profit - entry) / (entry - stop) if entry > stop else 0
    score_equivalent = max(0, min(9, round(confidence / 10)))
    fraction = 0 if score_equivalent <= 6 else (0.5 if score_equivalent == 7 else 0.85)
    capital = get_config().capital
    suggested_amount = round(capital * fraction, 2)

    if filters.tick_size:
        entry = _decimal_round_down(entry, filters.tick_size)
        stop = _decimal_round_down(stop, filters.tick_size)
        take_profit = _decimal_round_down(take_profit, filters.tick_size)

    quantity = _decimal_round_down(suggested_amount / entry, filters.step_size) if entry and suggested_amount else 0.0
    notional = round(quantity * entry, 8)
    order_checks = []
    if filters.min_notional and suggested_amount and notional < filters.min_notional:
        order_checks.append(f"notional {notional:.8f} is below Binance minimum {filters.min_notional}")

    return {
        "side": "long",
        "market_scope": "binance_spot_long_only",
        "entry": entry,
        "stop_loss": stop,
        "take_profit": take_profit,
        "reward_risk": round(rr, 2),
        "atr_multiple_stop": 1.6,
        "atr_multiple_target": 2.4,
        "triple_barrier": {
            "upper": take_profit,
            "lower": stop,
            "vertical_bars": 24,
            "basis": "1h ATR",
        },
        "suggested_amount": suggested_amount,
        "suggested_quantity": quantity,
        "estimated_notional": notional,
        "order_checks": order_checks,
        "live_trading_required": False,
    }


def _decision(score, validation, warnings):
    if any("unavailable" in w for w in warnings):
        return "DATA_ERROR"
    if score >= 72 and validation["approved"] and not any("bearish" in w for w in warnings):
        return "APPROVED_PAPER"
    if score >= 58:
        return "WATCH"
    return "REJECT"


def scan_symbols(symbols):
    results = [score_symbol(symbol) for symbol in symbols]
    results.sort(key=lambda row: row.get("score", 0), reverse=True)
    return {
        "timestamp": int(time.time()),
        "count": len(results),
        "results": results,
        "best": results[0] if results else None,
    }
