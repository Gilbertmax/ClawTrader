#!/usr/bin/env python3
"""
ClawTrader Analytics Engine v1.0
Análisis técnico multi-activo con TA-Lib + yfinance
"""
import argparse
import json
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import talib

# ─── Data Sources ───────────────────────────────────────────────────────

def fetch_candles(symbol, interval="1d", period="1mo"):
    """Fetch OHLCV from Yahoo Finance"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        return df
    except Exception as e:
        return None

# ─── Indicators ─────────────────────────────────────────────────────────

def calc_indicators(df):
    """Calculate all key indicators using TA-Lib"""
    if df is None or len(df) < 30:
        return None, None
    
    open_p = df['open'].values.astype(float)
    high = df['high'].values.astype(float)
    low = df['low'].values.astype(float)
    close = df['close'].values.astype(float)
    volume = df['volume'].values.astype(float) if 'volume' in df.columns else None
    
    results = {}
    
    # --- Trend ---
    # EMAs
    results['ema_9'] = talib.EMA(close, timeperiod=9).tolist()
    results['ema_21'] = talib.EMA(close, timeperiod=21).tolist()
    results['ema_50'] = talib.EMA(close, timeperiod=50).tolist()
    results['ema_200'] = talib.EMA(close, timeperiod=200).tolist()
    
    # SMAs
    results['sma_20'] = talib.SMA(close, timeperiod=20).tolist()
    results['sma_50'] = talib.SMA(close, timeperiod=50).tolist()
    results['sma_200'] = talib.SMA(close, timeperiod=200).tolist()
    
    # MACD
    macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
    results['macd'] = macd.tolist()
    results['macd_signal'] = macd_signal.tolist()
    results['macd_hist'] = macd_hist.tolist()
    
    # ADX (trend strength)
    results['adx'] = talib.ADX(high, low, close, timeperiod=14).tolist()
    
    # Parabolic SAR
    results['sar'] = talib.SAR(high, low, acceleration=0.02, maximum=0.2).tolist()
    
    # --- Momentum ---
    # RSI
    results['rsi_14'] = talib.RSI(close, timeperiod=14).tolist()
    
    # Stochastic
    slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0)
    results['stoch_k'] = slowk.tolist()
    results['stoch_d'] = slowd.tolist()
    
    # CCI
    results['cci'] = talib.CCI(high, low, close, timeperiod=14).tolist()
    
    # Williams %R
    results['williams_r'] = talib.WILLR(high, low, close, timeperiod=14).tolist()
    
    # ROC
    results['roc'] = talib.ROC(close, timeperiod=10).tolist()
    
    # --- Volatility ---
    # Bollinger Bands
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    results['bb_upper'] = upper.tolist()
    results['bb_middle'] = middle.tolist()
    results['bb_lower'] = lower.tolist()
    results['bb_width'] = ((upper - lower) / middle * 100).tolist()
    results['bb_percent_b'] = ((close - lower) / (upper - lower) * 100).tolist()
    
    # ATR
    results['atr_14'] = talib.ATR(high, low, close, timeperiod=14).tolist()
    
    # --- Volume ---
    if volume is not None:
        results['obv'] = talib.OBV(close, volume).tolist()
    
    # --- Pattern Recognition ---
    patterns = {}
    pattern_funcs = [
        ('doji', talib.CDLDOJI),
        ('hammer', talib.CDLHAMMER),
        ('engulfing', talib.CDLENGULFING),
        ('morning_star', talib.CDLMORNINGSTAR),
        ('evening_star', talib.CDLEVENINGSTAR),
        ('three_white_soldiers', talib.CDL3WHITESOLDIERS),
        ('three_black_crows', talib.CDL3BLACKCROWS),
    ]
    for name, func in pattern_funcs:
        patterns[name] = func(open_p, high, low, close).tolist()
    
    return results, patterns


def generate_signal(df, results, patterns, symbol="Unknown"):
    """Generate structured trading signal"""
    if df is None or results is None:
        return {"symbol": symbol, "error": "Insufficient data"}
    
    close = df['close'].values.astype(float)
    last_close = close[-1]
    prev_close = close[-2] if len(close) > 1 else last_close
    
    # Current values
    rsi = results['rsi_14'][-1] if results['rsi_14'][-1] is not None and not np.isnan(results['rsi_14'][-1]) else 50
    macd = results['macd'][-1] if results['macd'][-1] is not None and not np.isnan(results['macd'][-1]) else 0
    macd_signal = results['macd_signal'][-1] if results['macd_signal'][-1] is not None and not np.isnan(results['macd_signal'][-1]) else 0
    macd_hist = results['macd_hist'][-1] if results['macd_hist'][-1] is not None and not np.isnan(results['macd_hist'][-1]) else 0
    adx = results['adx'][-1] if results['adx'][-1] is not None and not np.isnan(results['adx'][-1]) else 0
    bb_upper = results['bb_upper'][-1]
    bb_lower = results['bb_lower'][-1]
    bb_mid = results['bb_middle'][-1]
    ema_9 = results['ema_9'][-1] if results['ema_9'][-1] is not None and not np.isnan(results['ema_9'][-1]) else last_close
    ema_21 = results['ema_21'][-1] if results['ema_21'][-1] is not None and not np.isnan(results['ema_21'][-1]) else last_close
    ema_50 = results['ema_50'][-1] if results['ema_50'][-1] is not None and not np.isnan(results['ema_50'][-1]) else last_close
    ema_200 = results['ema_200'][-1] if results['ema_200'][-1] is not None and not np.isnan(results['ema_200'][-1]) else last_close
    
    # Signal logic
    signals = []
    score = 0  # positive = bullish, negative = bearish
    
    # RSI
    if rsi < 30:
        signals.append("RSI oversold")
        score += 2
    elif rsi > 70:
        signals.append("RSI overbought")
        score -= 2
    elif rsi < 40:
        signals.append("RSI bearish zone")
        score -= 1
    elif rsi > 60:
        signals.append("RSI bullish zone")
        score += 1
    else:
        signals.append("RSI neutral")
    
    # MACD
    if macd > macd_signal and macd_hist > 0:
        signals.append("MACD bullish cross")
        score += 2
    elif macd < macd_signal and macd_hist < 0:
        signals.append("MACD bearish cross")
        score -= 2
    elif macd > macd_signal:
        signals.append("MACD improving")
        score += 1
    elif macd < macd_signal:
        signals.append("MACD weakening")
        score -= 1
    
    # Bollinger Bands
    bb_pct = results['bb_percent_b'][-1] if results['bb_percent_b'][-1] is not None and not np.isnan(results['bb_percent_b'][-1]) else 50
    if bb_pct > 95:
        signals.append("Price near BB upper (overextended)")
        score -= 1
    elif bb_pct < 5:
        signals.append("Price near BB lower (oversold bounce possible)")
        score += 2
    elif bb_pct > 80:
        signals.append("Price in upper BB zone")
        score += 1
    elif bb_pct < 20:
        signals.append("Price in lower BB zone")
        score -= 1
    
    # EMAs alignment
    if ema_9 > ema_21 > ema_50:
        signals.append("EMAs bullish alignment (9>21>50)")
        score += 2
    elif ema_9 < ema_21 < ema_50:
        signals.append("EMAs bearish alignment (9<21<50)")
        score -= 2
    
    # Price vs EMAs
    if last_close > ema_9:
        signals.append("Price above EMA 9")
        score += 1
    if last_close > ema_50:
        signals.append("Price above EMA 50")
        score += 1
    if last_close > ema_200:
        signals.append("Price above EMA 200")
        score += 1 if len(close) > 200 else 0
    
    # ADX trend strength
    if adx > 25:
        signals.append(f"Strong trend (ADX {adx:.1f})")
    elif adx > 20:
        signals.append(f"Trend developing (ADX {adx:.1f})")
    else:
        signals.append(f"Low trend strength (ADX {adx:.1f})")
    
    # Patterns
    detected_patterns = []
    for name, vals in patterns.items():
        last_val = vals[-1] if vals and len(vals) > 0 else 0
        if last_val and last_val != 0:
            if last_val > 0:
                detected_patterns.append(f"🟢 {name.replace('_',' ').title()} (bullish)")
                score += 2
            elif last_val < 0:
                detected_patterns.append(f"🔴 {name.replace('_',' ').title()} (bearish)")
                score -= 2
    
    # Change
    change_pct = ((last_close - prev_close) / prev_close) * 100
    
    # Final verdict
    if score >= 4:
        verdict = "🟢 STRONG BUY"
    elif score >= 2:
        verdict = "🟡 BUY"
    elif score <= -4:
        verdict = "🔴 STRONG SELL"
    elif score <= -2:
        verdict = "🟡 SELL"
    else:
        verdict = "⚪ NEUTRAL / HOLD"
    
    return {
        "symbol": symbol,
        "last_close": round(last_close, 5),
        "change_pct": round(change_pct, 2),
        "score": score,
        "verdict": verdict,
        "signals": signals,
        "patterns": detected_patterns,
        "indicators": {
            "rsi_14": round(rsi, 2),
            "macd": round(macd, 5),
            "macd_signal": round(macd_signal, 5),
            "macd_hist": round(macd_hist, 5),
            "adx": round(adx, 2),
            "ema_9": round(ema_9, 5),
            "ema_21": round(ema_21, 5),
            "ema_50": round(ema_50, 5),
            "bb_upper": round(bb_upper, 5),
            "bb_middle": round(bb_mid, 5),
            "bb_lower": round(bb_lower, 5),
            "bb_percent_b": round(bb_pct, 2),
        }
    }


def analyze_symbol(symbol, interval="1d", period="3mo"):
    """Full analysis pipeline for one symbol"""
    df = fetch_candles(symbol, interval, period)
    if df is None:
        return {"symbol": symbol, "error": "No data"}
    
    results, patterns = calc_indicators(df)
    signal = generate_signal(df, results, patterns, symbol)
    return signal


# ─── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClawTrader Analytics Engine")
    parser.add_argument("--symbols", nargs="+", default=["EURUSD=X", "GBPUSD=X", "JPY=X", "GC=F", "CL=F", "^GSPC", "^VIX", "DX-Y.NYB", "BTC-USD", "ETH-USD"])
    parser.add_argument("--interval", default="1d", help="Interval: 1m, 5m, 15m, 1h, 1d")
    parser.add_argument("--period", default="3mo", help="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    results = []
    for sym in args.symbols:
        sig = analyze_symbol(sym, args.interval, args.period)
        results.append(sig)
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if "error" in r:
                print(f"❌ {r['symbol']}: {r['error']}")
            else:
                print(f"\n{'='*60}")
                print(f"📊 {r['symbol']}  |  Close: {r['last_close']}  ({r['change_pct']:+.2f}%)")
                print(f"   Verdict: {r['verdict']}  (score: {r['score']:+d})")
                print(f"   RSI: {r['indicators']['rsi_14']}  |  MACD: {r['indicators']['macd']}  |  ADX: {r['indicators']['adx']}")
                print(f"   BB %B: {r['indicators']['bb_percent_b']:.1f}%")
                print(f"   EMAs: 9({r['indicators']['ema_9']}) 21({r['indicators']['ema_21']}) 50({r['indicators']['ema_50']})")
                print(f"   Signals: {', '.join(r['signals'][:3])}")
                if r['patterns']:
                    print(f"   Patterns: {', '.join(r['patterns'])}")
