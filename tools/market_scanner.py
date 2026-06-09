#!/usr/bin/env python3
from urllib.request import urlopen
import json

MIN_SCORE = 6

def k(sym, iv, lim=50):
    with urlopen(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval={iv}&limit={lim}", timeout=10) as r:
        return json.load(r)

def rsi(cl, p=14):
    g = l = 0
    for i in range(-p, 0):
        d = cl[i] - cl[i-1]
        if d > 0: g += d
        else: l -= d
    ag, al = g/p, l/p
    if al == 0: return 100
    return 100 - 100/(1 + ag/al)

def ema(cl, p):
    k2 = 2/(p+1)
    e = sum(cl[-p:])/p
    for c in cl[-p:]:
        e = c*k2 + e*(1-k2)
    return e

def scan(sym):
    try:
        c15 = k(sym, "15m", 30)
        c1 = k(sym, "1h", 48)
        c4 = k(sym, "4h", 20)
        p = float(c1[-1][4])
        cls15 = [float(x[4]) for x in c15]
        cls1 = [float(x[4]) for x in c1]
        cls4 = [float(x[4]) for x in c4]
        r15 = rsi(cls15)
        r1 = rsi(cls1)
        r4 = rsi(cls4)
        em20 = ema(cls15, 20)
        hi8 = max(float(x[2]) for x in c1[-8:])
        lo8 = min(float(x[3]) for x in c1[-8:])
        rp = (p-lo8)/(hi8-lo8)*100 if hi8 != lo8 else 50
        alc = sum(1 for x in c1[-6:] if float(x[4]) > float(x[1]))
        vols = [float(x[5]) for x in c15]
        av = sum(vols)/len(vols)
        vr = vols[-1]/av if av > 0 else 0
        
        s = 0
        rs = []
        if 45 <= r1 <= 65: s += 1
        if r1 > 50: s += 1; rs.append("RSI1h>50")
        if p > em20: s += 1; rs.append("P>EMA20")
        if r4 > 40: s += 1; rs.append("RSI4h>40")
        if alc >= 4: s += 1; rs.append(f"Alc{alc}/6h")
        if 20 <= rp <= 70: s += 1; rs.append(f"R{rp:.0f}%")
        if 0.8 <= vr <= 2.0: s += 1
        if rp < 35: s += 1; rs.append("CercaSop")
        if not (r15 > 70 > r1): s += 1
        
        return {"s": sym.replace("USDT",""), "p": round(p,2), "sco": s,
                "r15": round(r15,1), "r1": round(r1,1), "r4": round(r4,1),
                "alc": alc, "lo": lo8, "hi": hi8,
                "entry": round(lo8*1.01,2), "sl": round(lo8*0.99,2),
                "tp": round(hi8*0.995,2), "vr": round(vr,2)}
    except Exception as e:
        return None

pairs = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
         "ADAUSDT","DOGEUSDT","LINKUSDT","AVAXUSDT","NEARUSDT",
         "SUIUSDT","FETUSDT","ZECUSDT","DASHUSDT","WLDUSDT"]

results = []
for p in pairs:
    r = scan(p)
    if r: results.append(r)
results.sort(key=lambda x: x["sco"], reverse=True)

alerts = [r for r in results if r["sco"] >= MIN_SCORE]
now = __import__("datetime").datetime.now().strftime("%H:%M")

out = {"t": now, "n": len(results), "alerts": len(alerts),
       "scores": {r["s"]: r["sco"] for r in results[:10]},
       "best": alerts[0] if alerts else results[0]}
print(json.dumps(out))
