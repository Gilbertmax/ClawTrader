# 🦞 ClawTrader — Asistente de Trading Autónomo / Autonomous Trading Assistant

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge&logo=github" alt="Version">
  <img src="https://img.shields.io/badge/platform-OpenClaw-8A2BE2?style=for-the-badge&logo=openai" alt="OpenClaw">
  <img src="https://img.shields.io/badge/exchange-Binance-F0B90B?style=for-the-badge&logo=binance" alt="Binance">
  <img src="https://img.shields.io/badge/telegram-bot-26A5E4?style=for-the-badge&logo=telegram" alt="Telegram">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License">
</p>

---

## ES — 🇪🇸 Español

> ClawTrader es un asistente de trading open source para analizar mercados, gestionar riesgo y ejecutar flujos de paper/live trading con control, disciplina y transparencia.

---

### 🚀 Características Principales

| Característica | Descripción |
|---|---|
| 🤖 **Multi-Agente** | Sistema de agentes especializados: análisis técnico, validación de entradas, gestión de riesgo, monitoreo de posiciones |
| 📊 **Scanner de Mercado** | Escanea cientos de criptomonedas en Binance y encuentra oportunidades con scoring automático |
| 🛡️ **Gestión de Riesgo** | Validación estricta de entries, OCO automático, tamaño de posición según score |
| 💬 **Telegram Bot** | Controla tu trading desde Telegram: recibe señales, alertas y reportes |
| 🔄 **Multi-Exchange** | Binance (spot real) + Alpaca (paper trading) |
| ⏰ **Monitoreo 24/7** | Vigilancia continua de posiciones abiertas con alertas en tiempo real |
| 📈 **TA-Lib Real** | Análisis técnico con indicadores reales: RSI, MACD, BBands, EMAs |
| 📝 **Bitácora Automática** | Cada operación se registra automáticamente para análisis posterior |
| 🔐 **Seguridad** | Credenciales en `.env`, excluidas de git, y trading real desactivado por defecto |

### 📋 Requisitos

- **Python 3.9+** con pip
- **OpenClaw instalado y configurado**. ClawTrader se instala dentro de `~/.openclaw/skills` y `~/.openclaw/workspace`.
- **Cuenta en Binance** con API habilitada (opcional: Alpaca)
- **Bot de Telegram** (opcional)

### 🔧 Instalación

Primero instala OpenClaw. ClawTrader no reemplaza OpenClaw: agrega sus skills y tools al workspace de OpenClaw.

```bash
# 1. Instalar OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw --version

# Si openclaw no aparece después de instalar:
export PATH="$HOME/.npm-global/bin:$PATH"

# 2. Clonar ClawTrader
git clone https://github.com/tu-usuario/ClawTrader.git
cd ClawTrader

# 3. Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias de ClawTrader
pip install -r requirements.txt

# 5. Desplegar ClawTrader dentro de OpenClaw
python3 install.py
```

El instalador valida OpenClaw antes de pedir credenciales. Si OpenClaw no existe, se detiene con instrucciones.
Al terminar, reinicia el servicio de OpenClaw con `openclaw daemon restart` para que las skills y tools nuevas queden cargadas.

> 💡 **¿No tienes cuenta en Binance?** [¡Crea una aquí!](https://www.binance.com/referral/earn-together/refer2earn-usdc/claim?hl=es-LA&ref=GRO_28502_BYDAT&utm_source=referral_entrance)

### 🔑 Configuración de APIs

#### Binance (obligatorio para operar crypto)
1. Ve a [Binance API Management](https://www.binance.com/en/support/faq/how-to-create-api-keys-on-binance-360002502072)
2. Crea una API Key con permisos de **lectura y trading** (spot)
3. Guarda API Key y Secret Key
4. El instalador te pedirá ambas credenciales

#### Alpaca (opcional — paper trading)
1. Regístrate en [Alpaca Markets](https://alpaca.markets/)
2. Crea una API Key para paper trading
3. El instalador te guiará

#### Telegram (opcional — notificaciones)
1. Crea un bot con [@BotFather](https://t.me/BotFather) en Telegram
2. Obtén tu Chat ID (usa @userinfobot)
3. El instalador te pedirá el Token y Chat ID

### 🎮 Uso Básico

```bash
# Iniciar sesión de trading
openclaw

# Ejecutar scanner de mercado manualmente
python3 tools/clawtrader.py scan

# Ejecutar scanner profesional multi-timeframe
python3 tools/clawtrader.py pro-scan --symbols BTCUSDT ETHUSDT SOLUSDT

# Crear plan de decisión para un activo
python3 tools/clawtrader.py decide BTCUSDT

# Ver snapshot crypto en vivo
python3 tools/clawtrader.py snapshot --exchanges binance

# Ver dashboard de trading
python3 tools/clawtrader.py dashboard
# Luego abre http://localhost:8080

# Validar instalación
python3 tools/clawtrader.py health
```

O simplemente habla con ClawTrader en Telegram para recibir señales y gestionar operaciones.

### 📁 Estructura del Proyecto

```
ClawTrader/
├── README.md              # Este archivo
├── install.py             # Instalador interactivo
├── deploy.sh              # Script de despliegue
├── .gitignore             # Archivos ignorados por git
├── .env.example           # Ejemplo de variables de entorno
│
├── tools/                 # Scripts de trading
│   ├── clawtrader.py          # CLI unificada
│   ├── config.py              # Configuración segura
│   ├── risk.py                # Validación de riesgo
│   ├── binance_client.py      # Cliente Binance REST
│   ├── market_scanner.py      # Scanner de mercados
│   ├── alpaca_trader.py       # Interfaz Alpaca
│   ├── autonomous_monitor.py  # Monitoreo autónomo
│   ├── clawtrader_dual.py     # Motor dual Binance+Alpaca
│   ├── monitor_eth.py         # Monitor ETH
│   ├── monitor_eth_v2.py      # Monitor ETH v2
│   ├── check_crypto.py        # Verificador crypto
│   ├── check_multi.py         # Verificador multi-activo
│   ├── trading_analytics.py   # Análisis técnico TA-Lib
│   ├── crypto_live.py         # Datos en vivo CCXT
│   ├── server.py              # Dashboard web
│   ├── orchestrator.py        # Orquestador de agentes
│   ├── clawtrader_report.py   # Generador de reportes
│   └── load_env.py            # Cargador de .env
│
├── skills/                # Skills de OpenClaw
│   ├── es/                    # 🇪🇸 Skills en español
│   │   ├── 00-trader-core/
│   │   ├── 01-market-structure/
│   │   ├── 02-risk-manager/
│   │   └── ...
│   └── en/                    # 🇬🇧 Skills en inglés
│       ├── 00-trader-core/
│       ├── 01-market-structure/
│       └── ...
│
└── docs/                  # Documentación
    ├── es/                    # 🇪🇸 Guías en español
    └── en/                    # 🇬🇧 Guides in English
```

### 📜 Licencia y Donaciones

ClawTrader es open source bajo [licencia MIT](LICENSE). Úsalo, modifícalo y mejóralo.

Para colaborar, revisa la [guía de contribución](docs/CONTRIBUTING.md).

Si este proyecto te ayuda y quieres apoyar su desarrollo:

**PayPal:** `gilbertoreysena@hotmail.com`

El trading conlleva riesgo de pérdida de capital.

---

---

## EN — 🇬🇧 English

> ClawTrader is an open-source trading assistant for market analysis, risk management, and controlled paper/live trading workflows built around discipline and transparency.

### 🚀 Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Agent System** | Specialized agents for technical analysis, entry validation, risk management, position monitoring |
| 📊 **Market Scanner** | Scans hundreds of Binance cryptocurrencies with automatic scoring |
| 🛡️ **Risk Management** | Strict entry validation, automatic OCO, position sizing per score |
| 💬 **Telegram Bot** | Control your trading from Telegram: receive signals, alerts, and reports |
| 🔄 **Multi-Exchange** | Binance (real spot) + Alpaca (paper trading) |
| ⏰ **24/7 Monitoring** | Continuous position tracking with real-time alerts |
| 📈 **Real TA-Lib** | Technical analysis with real indicators: RSI, MACD, BBands, EMAs |
| 📝 **Auto Journal** | Every trade is automatically logged for post-analysis |
| 🔐 **Security** | Credentials stored in `.env`, excluded from git, with live trading disabled by default |

### 📋 Requirements

- **Python 3.9+** with pip
- **OpenClaw installed and configured**. ClawTrader installs into `~/.openclaw/skills` and `~/.openclaw/workspace`.
- **Binance account** with API enabled (optional: Alpaca)
- **Telegram Bot** (optional)

### 🔧 Installation

Install OpenClaw first. ClawTrader does not replace OpenClaw: it adds its skills and tools to the OpenClaw workspace.

```bash
# 1. Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash
openclaw --version

# If openclaw is not found after installation:
export PATH="$HOME/.npm-global/bin:$PATH"

# 2. Clone ClawTrader
git clone https://github.com/your-user/ClawTrader.git
cd ClawTrader

# 3. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install ClawTrader dependencies
pip install -r requirements.txt

# 5. Deploy ClawTrader into OpenClaw
python3 install.py
```

The installer validates OpenClaw before asking for credentials. If OpenClaw is missing, it stops with instructions.
When it finishes, it restarts the OpenClaw service with `openclaw daemon restart` so the new skills and tools are loaded.

> 💡 **Don't have a Binance account yet?** [Create one here with my referral link!](https://www.binance.com/referral/earn-together/refer2earn-usdc/claim?hl=es-LA&ref=GRO_28502_BYDAT&utm_source=referral_entrance)

### 🔑 API Configuration

#### Binance (required to trade crypto)
1. Go to [Binance API Management](https://www.binance.com/en/support/faq/how-to-create-api-keys-on-binance-360002502072)
2. Create an API Key with **read and trade** permissions (spot)
3. Save API Key and Secret Key
4. The installer will ask for both credentials

#### Alpaca (optional — paper trading)
1. Register at [Alpaca Markets](https://alpaca.markets/)
2. Create a paper trading API Key
3. The installer will guide you

#### Telegram (optional — notifications)
1. Create a bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your Chat ID (use @userinfobot)
3. The installer will ask for Token and Chat ID

### 🎮 Basic Usage

```bash
# Start a trading session
openclaw

# Run market scanner manually
python3 tools/clawtrader.py scan

# Run professional multi-timeframe scanner
python3 tools/clawtrader.py pro-scan --symbols BTCUSDT ETHUSDT SOLUSDT

# Build a decision plan for one asset
python3 tools/clawtrader.py decide BTCUSDT

# View live crypto snapshot
python3 tools/clawtrader.py snapshot --exchanges binance

# View trading dashboard
python3 tools/clawtrader.py dashboard
# Then open http://localhost:8080

# Verify installation
python3 tools/clawtrader.py health
```

Or just talk to ClawTrader on Telegram to receive signals and manage trades.

### 📁 Project Structure

```
ClawTrader/
├── README.md              # This file
├── install.py             # Interactive installer
├── deploy.sh              # Deployment script
├── .gitignore             # Git ignored files
├── .env.example           # Environment variables example
│
├── tools/                 # Trading scripts
│   ├── clawtrader.py          # Unified CLI
│   ├── config.py              # Safe configuration
│   ├── risk.py                # Risk validation
│   ├── binance_client.py      # Binance REST client
│   ├── market_scanner.py      # Market scanner
│   ├── alpaca_trader.py       # Alpaca interface
│   ├── autonomous_monitor.py  # Autonomous monitor
│   ├── clawtrader_dual.py     # Dual Binance+Alpaca engine
│   ├── monitor_eth.py         # ETH monitor
│   ├── monitor_eth_v2.py      # ETH monitor v2
│   ├── check_crypto.py        # Crypto checker
│   ├── check_multi.py         # Multi-asset checker
│   ├── trading_analytics.py   # TA-Lib technical analysis
│   ├── crypto_live.py         # CCXT live data
│   ├── server.py              # Web dashboard
│   ├── orchestrator.py        # Agent orchestrator
│   ├── clawtrader_report.py   # Report generator
│   └── load_env.py            # .env loader
│
├── skills/                # OpenClaw Skills
│   ├── es/                    # 🇪🇸 Spanish skills
│   │   ├── 00-trader-core/
│   │   ├── 01-market-structure/
│   │   ├── 02-risk-manager/
│   │   └── ...
│   └── en/                    # 🇬🇧 English skills
│       ├── 00-trader-core/
│       ├── 01-market-structure/
│       └── ...
│
└── docs/                  # Documentation
    ├── es/                    # 🇪🇸 Spanish guides
    └── en/                    # 🇬🇧 English guides
```

### 📜 License And Donations

ClawTrader is open source under the [MIT License](LICENSE). Use it, modify it, and improve it.

To contribute, read the [contribution guide](docs/CONTRIBUTING.en.md).

If this project helps you and you want to support development:

**PayPal:** `gilbertoreysena@hotmail.com`

Trading involves risk of capital loss.
