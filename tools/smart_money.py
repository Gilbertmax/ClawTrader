"""
smart_money.py — Smart Money Concepts + Order Book para ClawTrader
Detecta: BOS, Order Blocks, Liquidity Sweeps, Imbalance de ordenes
"""

from urllib.request import urlopen
import json


def get_orderbook(sym, limit=20):
    """
    Obtiene depth (bid/ask) de Binance.
    Retorna: imbalance_ratio, bid_vol, ask_vol, bid_prices, ask_prices
    imbalance_ratio > 1.5 → demanda fuerte (alcista)
    imbalance_ratio < 0.67 → oferta fuerte (bajista)
    """
    url = f"https://api.binance.com/api/v3/depth?symbol={sym}&limit={limit}"
    with urlopen(url, timeout=5) as r:
        d = json.load(r)
    
    bid_vol = sum(float(b[1]) for b in d["bids"])
    ask_vol = sum(float(a[1]) for a in d["asks"])
    
    # Precio promedio ponderado de bids y asks
    bid_avg = sum(float(b[0]) * float(b[1]) for b in d["bids"]) / bid_vol if bid_vol > 0 else 0
    ask_avg = sum(float(a[0]) * float(a[1]) for a in d["asks"]) / ask_vol if ask_vol > 0 else 0
    
    imbalance = bid_vol / ask_vol if ask_vol > 0 else 1
    spread = ask_avg - bid_avg if ask_avg and bid_avg else 0
    
    # Precios de soporte/resistencia inmediatos
    top_bid = max(float(b[0]) for b in d["bids"])
    low_ask = min(float(a[0]) for a in d["asks"])
    
    return {
        "imbalance": round(imbalance, 2),
        "bid_vol": round(bid_vol, 2),
        "ask_vol": round(ask_vol, 2),
        "top_bid": top_bid,
        "low_ask": low_ask,
        "spread": round(spread, 6),
        "n_bids": len(d["bids"]),
        "n_asks": len(d["asks"])
    }


def detect_bos(kl, n=10):
    """
    Break of Structure (BOS) — detección de cambio de tendencia.
    Retorna: estructura actual, último BOS detectado, fuerza
    """
    if len(kl) < n * 2:
        return {"estructura": "NEUTRA", "bos": None, "fuerza": 0}
    
    # Dividir en 2 segmentos
    seg1 = kl[:n]
    seg2 = kl[n:2*n] if len(kl) >= n*2 else kl[n:]
    
    hi1 = max(float(k[2]) for k in seg1)
    lo1 = min(float(k[3]) for k in seg1)
    hi2 = max(float(k[2]) for k in seg2)
    lo2 = min(float(k[3]) for k in seg2)
    
    p = float(kl[-1][4])
    
    bos_up = hi2 > hi1  # Rompió máximo anterior = BOS alcista
    bos_down = lo2 < lo1  # Rompió mínimo anterior = BOS bajista
    
    # Fuerza del BOS: qué tanto lo rompió en %
    fuerza = 0
    bos_type = None
    
    if bos_up and hi2 > hi1:
        pct = (hi2 - hi1) / hi1 * 100
        fuerza = min(10, round(pct * 5))  # 2% de ruptura = 10 de fuerza
        bos_type = "ALCISTA"
    elif bos_down and lo2 < lo1:
        pct = (lo1 - lo2) / lo1 * 100
        fuerza = min(10, round(pct * 5))
        bos_type = "BAJISTA"
    
    # Determinar estructura actual
    if bos_type == "ALCISTA" and p > ema([float(x[4]) for x in kl], 20):
        estructura = "ALCISTA"
    elif bos_type == "BAJISTA" and p < ema([float(x[4]) for x in kl], 20):
        estructura = "BAJISTA"
    else:
        # Ver si estamos en rango
        rng = (hi1 - lo1) / lo1 * 100
        if rng < 3:
            estructura = "RANGO"
        elif p > ema([float(x[4]) for x in kl], 20):
            estructura = "ALCISTA_DEBIL"
        else:
            estructura = "BAJISTA_DEBIL"
    
    return {
        "estructura": estructura,
        "bos": bos_type,
        "fuerza": fuerza,
        "ultimo_max": round(max(hi1, hi2), 6),
        "ultimo_min": round(min(lo1, lo2), 6)
    }


def detect_order_blocks(kl, n=15):
    """
    Order Blocks — últimas velas donde hubo acumulación/distribución.
    Order Block alcista = última vela bajista antes del movimiento alcista.
    Order Block bajista = última vela alcista antes del movimiento bajista.
    """
    if len(kl) < n:
        return {"ob_alcista": None, "ob_bajista": None, "valido": False}
    
    recent = kl[-n:]
    ob_alcista = None
    ob_bajista = None
    
    for i in range(len(recent) - 3):
        c1, c2, c3 = float(recent[i][4]), float(recent[i+1][4]), float(recent[i+2][4])
        o1, o2 = float(recent[i][1]), float(recent[i+1][1])
        hi1 = float(recent[i][2])
        lo1 = float(recent[i][3])
        
        # Order Block ALCISTA: vela bajista (c1 < o1) seguida de 2 velas alcistas
        if c1 < o1 and c2 > float(recent[i+1][1]) and c3 > float(recent[i+2][1]):
            ob_alcista = {
                "tipo": "ALCISTA",
                "precio_max": round(hi1, 6),
                "precio_min": round(lo1, 6),
                "indice": i
            }
        
        # Order Block BAJISTA: vela alcista (c1 > o1) seguida de 2 velas bajistas
        if c1 > o1 and c2 < float(recent[i+1][1]) and c3 < float(recent[i+2][1]):
            ob_bajista = {
                "tipo": "BAJISTA",
                "precio_max": round(hi1, 6),
                "precio_min": round(lo1, 6),
                "indice": i
            }
    
    return {"ob_alcista": ob_alcista, "ob_bajista": ob_bajista, "valido": ob_alcista or ob_bajista}


def detect_liquidity_sweeps(kl, n=20):
    """
    Liquidity Sweeps — barridos de liquidez (stops).
    Detecta: precio que cruza un mínimo anterior y luego revierte.
    """
    if len(kl) < n:
        return {"sweep": None, "valido": False}
    
    recent = kl[-n:]
    p = float(recent[-1][4])
    
    # Dividir en 2: primera mitad para niveles, segunda para barridos
    mid = len(recent) // 2
    first_half = recent[:mid]
    second_half = recent[mid:]
    
    # Niveles de liquidez
    min_nivel = min(float(k[3]) for k in first_half)
    max_nivel = max(float(k[2]) for k in first_half)
    
    # Buscar barridos
    sweep_bajo = False
    sweep_alto = False
    vol_sweep = False
    
    for k in second_half:
        lo = float(k[3])
        hi = float(k[2])
        vol = float(k[5])
        
        if lo < min_nivel * 0.998:  # Barrió el mínimo
            sweep_bajo = True
            min_nivel = lo
        if hi > max_nivel * 1.002:  # Barrió el máximo
            sweep_alto = True
            max_nivel = hi
    
    # Si el precio está cerca del mínimo barrido, posible reversal alcista
    if sweep_bajo and p > ema([float(x[4]) for x in recent], 20):
        return {
            "sweep": "LIQUIDEZ_ABAJO_BARRIDA",
            "nivel": round(min_nivel, 6),
            "p_actual": round(p, 6),
            "reversal": "POSIBLE_ALCISTA",
            "valido": True
        }
    
    if sweep_alto and p < ema([float(x[4]) for x in recent], 20):
        return {
            "sweep": "LIQUIDEZ_ARRIBA_BARRIDA",
            "nivel": round(max_nivel, 6),
            "p_actual": round(p, 6),
            "reversal": "POSIBLE_BAJISTA",
            "valido": True
        }
    
    return {"sweep": None, "valido": False}


def ema(cl, p):
    if len(cl) < p:
        return cl[-1] if cl else 0
    k2 = 2 / (p + 1)
    e = sum(cl[-p:]) / p
    for c in cl[-p:]:
        e = c * k2 + e * (1 - k2)
    return e


def analyze_sym(sym):
    """
    Análisis completo Smart Money + Order Book para un símbolo.
    Retorna dict con toda la información.
    """
    try:
        from urllib.request import urlopen
        # Klines
        with urlopen(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=30", timeout=10) as r:
            kl = json.load(r)
        with urlopen(f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=15m&limit=30", timeout=10) as r:
            kl15 = json.load(r)
        
        p = float(kl[-1][4])
        cls1 = [float(x[4]) for x in kl]
        ema20 = ema(cls1, 20)
        
        # Order Book
        ob = get_orderbook(sym)
        
        # BOS
        bos = detect_bos(kl, 10)
        
        # Order Blocks
        obs = detect_order_blocks(kl, 15)
        
        # Liquidity Sweeps
        ls = detect_liquidity_sweeps(kl, 20)
        
        # Interpretación general
        senal = _interpretar(ob, bos, obs, ls, p, ema20)
        
        return {
            "sym": sym,
            "p": round(p, 6),
            "ob": ob,
            "bos": bos,
            "obs": obs,
            "ls": ls,
            "senal": senal
        }
    except Exception as e:
        return {"sym": sym, "error": str(e)}


def _interpretar(ob, bos, obs, ls, p, ema20):
    """Interpreta todas las señales en una recomendación."""
    alcistas = 0
    bajistas = 0
    detalles = []
    
    # Order Book
    if ob["imbalance"] > 1.5:
        alcistas += 1
        detalles.append(f"Order Book imbalance {ob['imbalance']}x demanda ✅")
    elif ob["imbalance"] < 0.67:
        bajistas += 1
        detalles.append(f"Order Book imbalance {ob['imbalance']}x oferta 🔴")
    else:
        detalles.append(f"Order Book balanceado {ob['imbalance']}x")
    
    # BOS
    if bos["bos"] == "ALCISTA":
        alcistas += 2
        detalles.append(f"BOS ALCISTA fuerza {bos['fuerza']}/10 ✅")
    elif bos["bos"] == "BAJISTA":
        bajistas += 2
        detalles.append(f"BOS BAJISTA fuerza {bos['fuerza']}/10 🔴")
    else:
        detalles.append("Sin BOS claro")
    
    # Order Blocks
    if obs["ob_alcista"] and obs["ob_bajista"]:
        detalles.append(f"OB Alcista en ${obs['ob_alcista']['precio_min']}, OB Bajista en ${obs['ob_bajista']['precio_max']}")
        if p > obs["ob_alcista"]["precio_max"]:
            alcistas += 1
            detalles.append("Precio sobre OB alcista ✅")
    elif obs["ob_alcista"]:
        alcistas += 1
        detalles.append(f"OB Alcista en ${obs['ob_alcista']['precio_min']}-${obs['ob_alcista']['precio_max']} ✅")
    elif obs["ob_bajista"]:
        bajistas += 1
        detalles.append(f"OB Bajista en ${obs['ob_bajista']['precio_min']}-${obs['ob_bajista']['precio_max']} 🔴")
    
    # Liquidity Sweeps
    if ls["valido"]:
        if "POSIBLE_ALCISTA" in str(ls.get("reversal", "")):
            alcistas += 1
            detalles.append(f"Liquidity sweep abajo en ${ls['nivel']}, posible reversal alcista 🎯")
        elif "POSIBLE_BAJISTA" in str(ls.get("reversal", "")):
            bajistas += 1
            detalles.append(f"Liquidity sweep arriba en ${ls['nivel']}, posible reversal bajista ⚠️")
    
    # Tendencia EMA
    if p > ema20:
        alcistas += 1
    else:
        bajistas += 1
    
    decision = "ALCISTA" if alcistas > bajistas + 1 else ("BAJISTA" if bajistas > alcistas + 1 else "NEUTRA")
    
    return {
        "decision": decision,
        "alcistas": alcistas,
        "bajistas": bajistas,
        "detalles": detalles
    }


if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    r = analyze_sym(sym)
    print(json.dumps(r, indent=2))
