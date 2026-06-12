# 🦞 ClawTrader v2 — Asistente de Trading Autónomo

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=for-the-badge&logo=github" alt="Version">
  <img src="https://img.shields.io/badge/exchange-Binance-F0B90B?style=for-the-badge&logo=binance" alt="Binance">
  <img src="https://img.shields.io/badge/telegram-bot-26A5E4?style=for-the-badge&logo=telegram" alt="Telegram">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python" alt="Python">
</p>

---

## 🇪🇸 Español

> ClawTrader es un asistente de trading autónomo que analiza mercados, gestiona riesgo y puede operar Binance Spot solo cuando el usuario activa trading real explícitamente.

### 🚀 Características

| Característica | Descripción |
|---|---|
| 🔬 **Scanner de Mercado** | Escanea top 200 criptos en Binance, scoring 0-16 con VWAP, OBV, EMAs, MACD, volumen |
| 🧠 **Smart Money Analysis** | Order Book imbalance, BOS, Order Blocks, Liquidity Sweeps |
| 🎯 **Entry Watcher** | Vigilancia cada 2 min: targets, VWAP, OBV, Order Book, BOS |
| ⚙️ **Auto Cycle** | Cerebro unificado: scanner → Smart Money → simulación/ejecución controlada → monitoreo |
| 📊 **Live Engine** | Portfolio Manager + trailing dinámico + SL/TP fijos; trading real bloqueado por defecto |
| 🛡️ **Risk Manager** | Tamaño de posición por score, drawdown control, pausa por pérdidas |
| 📝 **Backtest** | Registro histórico, win rate, profit factor, score promedio |
| 📈 **Trailing Inteligente** | Se activa al 50% del TP, sube al 97% del máximo, protege ganancias |
| 🔐 **Seguridad** | Credenciales en `.env`, dry-run por defecto, trading real requiere doble confirmación por variables |

### 📋 Requisitos

- **Python 3.9+**
- **OpenClaw** instalado y configurado
- **Cuenta Binance** con API Key (permisos de lectura y trading spot)

### 🔧 Instalación Rápida

```bash
# 1. Instalar OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. Clonar ClawTrader
git clone <tu-repo>/ClawTrader.git
cd ClawTrader

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar instalador (prepara .env y despliega tools/skills)
python3 install.py
```

Edita `~/.openclaw/workspace/.env` para agregar credenciales. Por defecto:

```bash
CLAWTRADER_DRY_RUN=true
CLAWTRADER_LIVE_TRADING=false
```

Para permitir órdenes reales debes cambiar ambas variables de forma intencional.

### 🎮 Uso

```bash
# Verificar instalación
python3 tools/clawtrader.py health

# Ver balances de Binance
python3 tools/clawtrader.py balances

# Escanear mercado (top oportunidades)
python3 tools/clawtrader.py scan --min-score 8

# Analizar Smart Money de un activo
python3 tools/clawtrader.py smart-money BTCUSDT

# Validar un trade propuesto
python3 tools/clawtrader.py risk --entry 0.10 --current 0.11 --stop 0.09 --take-profit 0.13 --score 12

# Ver historial de trades
python3 tools/clawtrader.py backtest

# Ejecutar auto-cycle manualmente
python3 tools/clawtrader.py cycle-run

# Ver estado del engine
python3 tools/clawtrader.py engine
```

O simplemente habla con ClawTrader en Telegram para recibir señales y gestionar operaciones.

### 📁 Estructura

```
ClawTrader/
├── install.py                 # Instalador interactivo
├── requirements.txt           # Dependencias
├── ESTRATEGIA.md              # Estrategia completa de trading
├── README.md                  # Este archivo
│
├── tools/                     # Scripts de trading
│   ├── clawtrader.py          # CLI unificada
│   ├── config.py              # Configuración segura
│   ├── load_env.py            # Cargador de credenciales
│   ├── binance_client.py      # Cliente Binance API
│   ├── market_scanner.py      # Scanner v3 (score 0-16)
│   ├── smart_money.py         # Smart Money Analysis
│   ├── entry_watcher.py       # Vigilante de entradas
│   ├── live_engine.py         # Motor de ejecución controlada
│   ├── auto_cycle.py          # Cerebro unificado 5min
│   ├── backtest.py            # Registro histórico y análisis
│   ├── risk.py                # Gestión de riesgo
│   └── healthcheck.py         # Verificación del sistema
│
└── skills/                    # Skills de OpenClaw
    ├── es/                    # 🇪🇸 Skills en español
    │   ├── 00-trader-core/
    │   ├── 01-market-structure/
    │   ├── 02-risk-manager/
    │   └── ...
    └── en/                    # 🇬🇧 Skills en inglés
        ├── 00-trader-core/
        ├── 01-market-structure/
        └── ...
```

### 📜 Licencia

MIT — Úsalo, modifícalo, mejóralo.

Si te ayuda y quieres apoyar:
**PayPal:** `gilbertoreysena@hotmail.com`

El trading conlleva riesgo de pérdida de capital.

---

## 🇬🇧 English

> ClawTrader is an autonomous trading assistant that analyzes markets, manages risk, and can trade Binance Spot only when the user explicitly enables live trading.

### 🚀 Features

| Feature | Description |
|---|---|
| 🔬 **Market Scanner** | Scans top 200 coins, scoring 0-16 with VWAP, OBV, EMAs, MACD, volume |
| 🧠 **Smart Money Analysis** | Order Book imbalance, BOS, Order Blocks, Liquidity Sweeps |
| 🎯 **Entry Watcher** | 2-min interval checks: targets, VWAP, OBV, Order Book, BOS |
| ⚙️ **Auto Cycle** | Unified brain: scanner → Smart Money → simulation/controlled execution → monitoring |
| 📊 **Live Engine** | Portfolio Manager + dynamic trailing + fixed SL/TP; live trading is blocked by default |
| 🛡️ **Risk Manager** | Position sizing by score, drawdown control, loss pause |
| 📝 **Backtest** | Trade history, win rate, profit factor, avg score |
| 📈 **Smart Trailing** | Activates at 50% TP, climbs to 97% of max, protects profits |
| 🔐 **Security** | Credentials in `.env`, dry-run by default, live trading requires explicit env flags |

### 📋 Requirements

- **Python 3.9+**
- **OpenClaw** installed and configured
- **Binance account** with API Key (read + spot trade permissions)

### 🔧 Quick Install

```bash
# 1. Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. Clone ClawTrader
git clone <your-repo>/ClawTrader.git
cd ClawTrader

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run installer (prepares .env and deploys tools/skills)
python3 install.py
```

Edit `~/.openclaw/workspace/.env` to add credentials. Defaults:

```bash
CLAWTRADER_DRY_RUN=true
CLAWTRADER_LIVE_TRADING=false
```

Real orders require changing both variables intentionally.

### 🎮 Usage

```bash
# Verify installation
python3 tools/clawtrader.py health

# View Binance balances
python3 tools/clawtrader.py balances

# Scan market for opportunities
python3 tools/clawtrader.py scan --min-score 8

# Analyze Smart Money for an asset
python3 tools/clawtrader.py smart-money BTCUSDT

# Validate a proposed trade
python3 tools/clawtrader.py risk --entry 0.10 --current 0.11 --stop 0.09 --take-profit 0.13 --score 12

# View trade history
python3 tools/clawtrader.py backtest

# Run auto-cycle manually
python3 tools/clawtrader.py cycle-run

# View engine status
python3 tools/clawtrader.py engine
```

### 📁 Structure

Same as Spanish section above.

### 📜 License

MIT — Use it, modify it, improve it.

If this helps you and you want to support development:
**PayPal:** `gilbertoreysena@hotmail.com`

Trading involves risk of capital loss.
