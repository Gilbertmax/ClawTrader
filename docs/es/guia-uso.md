# 🦞 ClawTrader — Guía de Uso

> Cómo operar con ClawTrader, interpretar señales y gestionar tu cartera.

---

## 🚀 Inicio rápido

Una vez instalado (ver `guia-instalacion.md`), puedes interactuar con ClawTrader de varias formas:

### 1. Por Telegram (recomendado)
Solo habla con tu bot de ClawTrader en Telegram. Puedes:

- `@ClawTrader activo BTC/USDT` — Analizar un activo
- `@ClawTrader señal` — Solicitar señal del scanner
- `@ClawTrader reporte` — Reporte diario de operaciones
- `@ClawTrader estado` — Estado de posiciones abiertas
- `@ClawTrader riesgo` — Evaluar riesgo de una operación

### 2. Por línea de comandos
```bash
# Ejecutar el scanner de mercado
python3 tools/market_scanner.py

# Monitoreo autónomo (procesa señales automáticamente)
python3 tools/autonomous_monitor.py

# Ver dashboard web
python3 tools/server.py
# Abre http://localhost:5000 en tu navegador

# Ejecutar orquestador
python3 tools/orchestrator.py
```

### 3. Desde OpenClaw
```bash
openclaw
# Habla con ClawTrader como si fuera tu asistente de trading personal
```

---

## 📊 Interpretar señales del scanner

El scanner asigna un **score** a cada oportunidad detectada:

| Score | Significado | Acción |
|---|---|---|
| **0-3** | Muy débil | ❌ No operar |
| **4-6** | Débil/Neutral | ❌ No operar (esperar) |
| **7** | Buena | ⚠️ Máximo 50% del capital |
| **8-9** | Excelente | ✅ Hasta 85% del capital |

### Ejemplo de señal

```
🔍 SCAN: NEARUSDT
   Score: 7
   Precio: $2.12
   Entry sugerido: $2.12
   SL: $2.06 (4.7%)
   TP: $2.25 (6.1%)
   R/R: 1.3:1
   Tendencia: Alcista en 4H
```

---

## 🛡️ Validación de entradas

Antes de cada compra, ClawTrader ejecuta el **Entry Validator** que verifica:

1. **Precio de entrada** — No comprar si el precio actual está >2% arriba del entry sugerido
2. **Score del scanner** — Score ≤6 = rechazar automáticamente
3. **Tendencia de BTC** — Si BTC está bajista, reducir tamaño
4. **Capital disponible** — Calcular monto máximo según score
5. **R/R Ratio** — Mínimo 1.2:1 para altcoins
6. **Sesión activa** — No más de 3 pérdidas consecutivas

### Ejemplo de rechazo

```
❌ OPERACIÓN RECHAZADA
   Razón: Entry actual ($2.19) está +3.3% arriba del entry sugerido ($2.12)
   Score 7 permite 50% pero entry inválido
   BTC bajista reduce a 25%
```

---

## 📈 Monitoreo de posiciones

Cuando tienes una posición abierta, ClawTrader la monitorea automáticamente:

- **🟢 Verde** — Distancia segura al SL → Mantener
- **🟡 Amarillo** — Precio a <2% del SL → Monitorear más frecuente
- **🔴 Rojo** — Precio a <1% del SL → Considerar cierre manual
- **💚 Verde Brillante** — Precio a <2% del TP → Casi en objetivo

---

## 📝 Bitácora de operaciones

Cada operación queda registrada automáticamente. Puedes consultar tu historial:

```bash
# Ver archivo de bitácora del día
cat ~/.openclaw/workspace/memory/$(date +%F).md
```

El registro incluye:
- Activo y dirección
- Precio de entrada
- SL y TP
- Resultado (ganancia/pérdida)
- Razón de la operación
- Score en el momento de entrada

---

## ⚠️ Reglas importantes

### No hacer
- ❌ **No aumentar tamaño** después de una ganancia grande sin justificación
- ❌ **No martingala** (duplicar pérdida)
- ❌ **No operar por venganza** (recuperar pérdidas rápido)
- ❌ **No cambiar de activo en horas** — entrar y esperar resolución
- ❌ **No operar sin SL y TP definidos**

### Siempre hacer
- ✅ Respetar el score del scanner
- ✅ Colocar OCO desde la entrada
- ✅ Bitácora de cada sesión
- ✅ Pausa después de 3 pérdidas consecutivas
- ✅ Reducir tamaño si BTC está bajista

---

## 🔄 Flujo de trabajo típico

```
1. 📊 Scanner encuentra oportunidad (score 7+)
2. 🛡️ Entry Validator verifica condiciones
3. ✅ Si todo ok → Ejecutar compra en Binance
4. 📈 Position Tracker monitorea 24/7
5. ⏰ SL o TP se ejecuta → Posición cerrada
6. 📝 Bitácora registra resultado
7. 📊 Reporte al usuario por Telegram
```

---

## 🌐 Dashboard web

El dashboard web (puerto 5000) te permite ver:

- Posiciones abiertas
- Historial de operaciones
- Balance de cuenta
- Señales recientes del scanner
- Estadísticas de rendimiento

```bash
# Iniciar dashboard
python3 tools/server.py
# Abrir: http://localhost:5000
```

---

## 🆘 Comandos útiles

```bash
# Verificar conexión a Binance
python3 -c "from tools.crypto_live import *; print(get_binance_ticker('BTCUSDT'))"

# Ejecutar análisis rápido
python3 tools/trading_analytics.py BTC/USDT 1h

# Verificar estado del sistema
ls -la ~/.openclaw/workspace/.env && echo "✅ .env OK" || echo "❌ .env no encontrado"
```
