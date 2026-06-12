# ESTRATEGIA CLAWTRADER — Binance Spot Real

> **Capital actual:** ~$30.22 USDT  
> **Capital inicial:** ~$28.90 USDT (~$578 MXN)  
> **Drawdown histórico:** -94% (desde máximo)  
> **Objetivo inmediato:** Generar ganancias diarias, aunque sean centavos.  
> **Objetivo secundario:** Crecer consistente, no rápido.

---

## ⚡ NUEVO — Módulo de Scalping Diario (Activo desde 11 Jun 2026)

### Filosofía
> *"Ganar centavos, pero ganar. Cada día."*

Con $7.69 USDT libres, no necesitamos esperar señales milagrosas. Podemos generar **$0.10-$0.30 diarios** con scalping disciplinado en pares líquidos.

### Pares autorizados para scalping

| Par | Precio aprox | Spread | Volumen 24h | Riesgo |
|-----|-------------|--------|-------------|--------|
| **XRPUSDT** | $1.11 | 0.01% | ~100M | Bajo |
| **ADAUSDT** | $0.17 | 0.02% | ~28M | Bajo |
| **SUIUSDT** | $0.75 | 0.02% | ~27M | Bajo |
| **TRXUSDT** | $0.32 | 0.01% | ~37M | Bajo |
| **NEARUSDT** | $2.00 | 0.02% | ~68M | Bajo |

### Reglas de scalping

#### 🟢 Cuándo ENTRAR:
```
☐ Precio tocando un soporte VISIBLE en timeframe 1m o 5m
☐ Volumen de entrada > 1.5x el volumen promedio de los últimos 5 velas
☐ Cuerpo de vela verde (alcista) después del toque de soporte
☐ Spread ≤ 0.05%
☐ No hay noticia macro en la próxima hora
```

#### 🟡 Cuándo SALIR (take profit):
```
☐ Ganancia de 0.4% a 0.8% desde entrada → VENDER
   (Con $7.69: ganancia neta de $0.03 a $0.06 por trade)
☐ Si en 15 minutos no se movió 0.3% favorable → cerrar en break-even o pérdida mínima
```

#### 🔴 Cuándo CORTAR (stop loss):
```
☐ Pérdida de 0.5% desde entrada → STOP INMEDIATO
☐ Pérdida máxima por trade: $0.04
```

#### 📋 Límites del scalping:
| Regla | Valor |
|-------|-------|
| Capital asignado | $7.69 USDT (fijo, no aumentarlo) |
| Trades máximos por día | 8 |
| Pérdidas consecutivas máximas | 3 |
| Si 3 pérdidas seguidas | Parar scalping, solo auto-cycle |
| Ganancia objetivo diaria | $0.15-$0.30 |
| Ganancia máxima diaria | Si llegas a +$0.50 → PARAS |

#### ⏰ Horario de scalping:
- **Mejor horario:** 8:00 AM - 12:00 PM CST
- **No scalpear:** después de 2:00 PM CST (spreads se ensanchan)
- **No scalpear fines de semana**

#### 🎯 Target diario por tamaño de capital:

Visualización de lo que puedes generar según tu consistencia:

```
Con $7.69 USDT de scalping:

  Consistencia   | Trades buenos/día | Ganancia/día | Ganancia/mes
  ───────────────┼───────────────────┼──────────────┼─────────────
  Principiante   | 2 de 4           | $0.06-$0.08  | $1.50
  Normal         | 3 de 5           | $0.10-$0.15  | $3.00
  Bueno          | 4 de 6           | $0.15-$0.25  | $4.50
  Excelente      | 5 de 7           | $0.25-$0.40  | $7.00
```

**Objetivo del primer mes:** Llegar al nivel "Normal" → +$3/mes en scalping.

---

## 1. FILTROS DE MERCADO — Cuándo NO operar (largas)

### 🔴 Filtro #1: Tendencia BTC
| BTC Trend | Acción | Score mínimo |
|-----------|--------|-------------|
| **BULLISH** | Operar normal | ≥11/16 |
| **SIDEWAYS** | Operar con cautela | ≥11/16 + Smart Money ALCISTA |
| **BEARISH** | **NO operar** | Solo si score ≥14/16 Y Smart Money ALCISTA |

*Definición: BULLISH = precio > EMA20(1h) > EMA50(1h) Y precio > EMA20(4h) > EMA50(4h)*

### 🔴 Filtro #2: Smart Money
- **Order Book Imbalance ≥ 1.5x** → señal de entrada válida
- **BOS (Break of Structure)** detectado → confirmación de tendencia
- **Si Smart Money es BAJISTA** → NO entrar, aunque el score sea alto
- **Si Smart Money es NEUTRAL** → solo entrar si score ≥13/16

### 🔴 Filtro #3: VWAP
- **Precio DEBAJO de VWAP (1h)** → zona de valor, entrada permitida
- **Precio >2% SOBRE VWAP** → NO comprar (sobrevalorado)
- **VWAP check es OBLIGATORIO**, no opcional

### 🔴 Filtro #4: Volumen
- Volumen relativo (última vela vs promedio 15m) entre 0.5x y 2.5x
- Si volumen es anormalmente bajo (<0.3x) → NO entrar

### 🔴 Filtro #5: Máximo drawdown diario
- **Si el balance bajó 3% en el día** → fin de sesión. No más trades.
- **Si hay 2 pérdidas consecutivas** → pausa obligatoria de 24h.

---

## 2. SETUP DE ENTRADA — Largas (auto-cycle)

### Check list (TODO debe cumplirse):

```
☐ Score ≥ 11/16 (≥13 si BTC es SIDEWAYS, ≥14 si BEARISH)
☐ Smart Money NO es BAJISTA
☐ Order Book Imbalance ≥ 1.3x (ideal ≥ 1.5x)
☐ Precio DEBAJO de VWAP (1h)
☐ Precio NO >2% sobre VWAP
☐ RSI(1h) entre 40 y 65 (ni sobrecompra ni sobreventa extrema)
☐ MACD(1h) alcista O convergiendo
☐ BTC trend NO es BEARISH extremo
☐ No hay posición abierta en el mismo activo
☐ Balance libre ≥ $5 USDT (para cubrir min notional)
☐ No hemos perdido 3% del balance hoy
☐ No van 2 pérdidas consecutivas
```

### Señal ideal (entrada automática sin dudas):

Score ≥ 13/16 + Smart Money ALCISTA + Precio bajo VWAP + BTC BULLISH + RSI(1h) entre 45-60

---

## 3. TAMAÑO DE POSICIÓN (largas)

| Score | % del balance libre |
|-------|-------------------|
| 11-12 | 30-40% |
| 13-14 | 40-60% |
| 15-16 | 60-80% |

**Ajustes adicionales:**
- BTC BEARISH → multiplicar por 0.5 (mitad del tamaño)
- BTC SIDEWAYS → multiplicar por 0.75
- Balance < $10 USDT → **máximo 1 posición a la vez**
- Balance < $5 USDT → **NO operar** (capital insuficiente para cubrir comisiones y min notional)

**Regla estricta:** Nunca usar más del 85% del balance en una sola posición.

---

## 4. STOP LOSS Y TAKE PROFIT (largas)

| Escenario | SL | TP |
|-----------|-----|-----|
| BTC BULLISH | -4% | +7% |
| BTC SIDEWAYS | -4% | +5% |
| BTC BEARISH | -5% | +5% |
| Score ≥ 14 (señal fuerte) | -3.5% | +8% |

### Escalera de Ganancias (sistema de escalones):

**Regla base:** Cada $1 de ganancia asegurado = un escalón. Nunca perder lo ganado.

- Escalón mínimo protege: $0.50 → cuando la ganancia llega a $0.50, stop sube a entry
- Cada $1 completo de ganancia → stop sube $1 (protege el escalón anterior)
- Ejemplo con $10 invertidos:
  - Precio sube +$1 → stop sube a entry (nunca pierdes)
  - Precio sube +$2 → stop sube a entry+$1 (aseguras $1 de ganancia)
  - Precio sube +$3 → stop sube a entry+$2 (aseguras $2)
  - Si retrocede de $2.50 a $1.50 → stop se activa en entry+$1, cierras con +$1 ✅
  - Si sigue subiendo a $4 → stop sube a entry+$3, aseguras $3

**Salida:** Cuando el precio retrocede un escalón completo desde el máximo alcanzado.

**NO hay TP fijo.** La escalera decide cuándo salir.

---

## 5. PLAN DE SESIÓN

### Límites diarios:
- **Máximo 8 scalps por día** (en pares autorizados)
- **Máximo 2 largas por día** (auto-cycle)
- **1 posición máxima a la vez por tipo** (1 scalp activo + 1 larga activa es válido)
- **Drawdown máximo diario: 3%** — al llegar, se apaga todo **incluyendo scalping**
- **2 pérdidas consecutivas en scalping = fin del scalping del día**
- **2 pérdidas consecutivas en largas = pausa 24h**

### Horario:
- **Scalping:** 8:00 AM - 2:00 PM CST (mejor liquidez)
- **Auto-cycle:** 24/7
- **No operar:** fines de semana (volumen bajo, spreads anchos)
- **No operar:** durante noticias macro importantes (FOMC, CPI, NFP)

### Protocolo pre-sesión:
1. Revisar BTC trend (BULLISH/BEARISH/SIDEWAYS)
2. Revisar si hay drawsdown pendiente del día anterior
3. Si ayer hubo pérdida >5% → hoy solo observar, no operar

---

## 6. RECUPERACIÓN (RECOVERY RULES)

### Después de pérdida:
- **1 pérdida normal** → continuar normalmente
- **2 pérdidas consecutivas en largas** → **PAUSA OBLIGATORIA 24h**
- **3 pérdidas consecutivas en scalping** → **PAUSA OBLIGATORIA 24h**
- **Drawdown del día >3%** → fin de sesión inmediato
- **Drawdown de la semana >8%** → no operar el resto de la semana

### No hacer bajo ninguna circunstancia:
- ❌ **No hacer "revenge trading"** (intentar recuperar rápido)
- ❌ **No duplicar posición** para "promediar"
- ❌ **No cambiar el plan** después de una pérdida
- ❌ **No operar emocionalmente** — si hay duda, no se entra

---

## 7. AUTO-CYCLE: Configuración

### Criterios para ENTRADA AUTOMÁTICA (largas):
```
Score      ≥  11/16
BTC        ≠  BEARISH extremo  (si BEARISH, score ≥ 14 e imbalance ≥ 1.5)
SmartMkt   ≠  BAJISTA
VWAP       Precio < VWAP
Balance    ≥  $5 USDT libre
Hoy        No más de 2 trades, no drawdown >3%
Consecutivas No van 2 pérdidas seguidas
```

### Cuando el auto-cycle NO debe comprar:
- Balance libre < $5 USDT
- Ya hay posición abierta (1 máx)
- BTC en BEARISH con score < 14
- Smart Money BAJISTA
- Precio >2% sobre VWAP
- Hemos perdido 2 trades seguidos hoy

---

## 8. GESTIÓN DEL PORTFOLIO HOLD

### Estado actual (11 Jun 2026):
```
BTC:  $17.51  (hold, RSI diario 21.6 — sobreventa)
LINK: $5.01   (hold, RSI diario 30.4 — cerca de sobreventa)
```

### Reglas del hold:
- **BTC:** Hold hasta que RSI diario salga de sobreventa (>35) O precio suba +8% en un día (vender)
- **LINK:** Hold, si RSI sube >50 y hay señal del scanner, considerar vender para liberar capital
- **No vender en rojo.** Hold es pasivo, no activo.

---

## 9. PROTOCOLO DE CRISIS

Si el balance cae por debajo de $20.00 USDT:
1. Pausar auto-cycle y scalping INMEDIATAMENTE
2. Cerrar TODAS las posiciones
3. No operar por 7 días
4. Evaluar si continuar o depositar más capital

Si hay 3 pérdidas consecutivas (en diferentes días):
1. Pausar auto-cycle y scalping
2. Revisar si el mercado está en condiciones desfavorables
3. Hacer backtest de las últimas 20 señales

---

## 10. REGLAS FINALES (NO NEGOCIABLES)

1. **Stop-loss siempre.** No existe trade sin SL.
2. **Tamaño respetado.** No aumentar porque "esta es buena".
3. **Una larga a la vez.** Los scalps pueden coexistir con la larga.
4. **No cambiar de activo en horas.** Entrar y esperar resolución.
5. **Las pérdidas son del sistema, no personales.** Asumir y seguir el plan.
6. **El plan se sigue o se detiene.** No se modifica sobre la marcha.
7. **Revisión semanal obligatoria.** Evaluar qué funcionó y qué no.
8. **Si dudas, no entras.** Mañana hay otro día.
9. **Scalping es ganar centavos, no dollars.** No fuerces el tamaño.
10. **$0.10 hoy > $0.00 mañana.**

---

> *"No se trata de ganar rápido. Se trata de ganar consistente. Los centavos de hoy son los dólares de mañana."*
>
> — ClawTrader
