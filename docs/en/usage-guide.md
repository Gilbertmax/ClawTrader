# 🦞 ClawTrader — Usage Guide

> How to trade with ClawTrader, interpret signals, and manage your portfolio.

---

## 🚀 Quick Start

Once installed (see `installation-guide.md`), you can interact with ClawTrader in several ways:

### 1. Via Telegram (recommended)
Just talk to your ClawTrader bot on Telegram. You can:

- `@ClawTrader analyze BTC/USDT` — Analyze an asset
- `@ClawTrader signal` — Request a scanner signal
- `@ClawTrader report` — Daily trading report
- `@ClawTrader status` — Open positions status
- `@ClawTrader risk` — Evaluate trade risk

### 2. Via command line
```bash
# Run the market scanner
python3 tools/clawtrader.py scan

# Run the professional multi-timeframe scanner
python3 tools/clawtrader.py pro-scan --symbols BTCUSDT ETHUSDT SOLUSDT

# Build a decision plan for one asset
python3 tools/clawtrader.py decide BTCUSDT

# Analyze Smart Money
python3 tools/clawtrader.py smart-money BTCUSDT

# View engine status
python3 tools/clawtrader.py engine

# Verify installation
python3 tools/clawtrader.py health
```

### 3. From OpenClaw
```bash
openclaw
# Talk to ClawTrader like your personal trading assistant
```

---

## 📊 Interpreting scanner signals

The scanner assigns a **score** to each detected opportunity:

The `pro-scan` command uses multi-timeframe analysis (`15m`, `1h`, `4h`, `1d`), trend, momentum,
volatility, volume, liquidity, Binance exchange filters, and risk validation. The `decide` command shows
the same analysis for one asset and includes entry, stop loss, take profit, and ATR barrier planning.

| Score | Meaning | Action |
|---|---|---|
| **0-3** | Very weak | ❌ Do not trade |
| **4-6** | Weak/Neutral | ❌ Do not trade (wait) |
| **7** | Good | ⚠️ Max 50% of capital |
| **8-9** | Excellent | ✅ Up to 85% of capital |

### Example signal

```
🔍 SCAN: NEARUSDT
   Score: 7
   Price: $12.50
   Suggested entry: $12.50
   SL: $12.00 (4.0%)
   TP: $13.50 (8.0%)
   R/R: 1.5:1
   Trend: Bullish on 4H
```

---

## 🛡️ Entry validation

Before every buy, ClawTrader runs the **Entry Validator** which checks:

1. **Entry price** — No buy if current price is >2% above suggested entry
2. **Scanner score** — Score ≤6 = auto reject
3. **BTC trend** — If BTC is bearish, reduce size
4. **Available capital** — Calculate max amount based on score
5. **R/R Ratio** — Minimum 1.2:1 for altcoins
6. **Active session** — No more than 3 consecutive losses

### Example rejection

```
❌ TRADE REJECTED
   Reason: Current entry ($12.90) is +3.2% above suggested entry ($12.50)
   Score 7 allows 50% but entry is invalid
   BTC bearish reduces to 25%
```

---

## 📈 Position monitoring

When you have an open position, ClawTrader monitors it automatically:

- **🟢 Green** — Safe distance to SL → Hold
- **🟡 Yellow** — Price <2% from SL → Monitor more frequently
- **🔴 Red** — Price <1% from SL → Consider manual close
- **💚 Bright Green** — Price <2% from TP → Almost there

---

## 📝 Trade journal

Every trade is automatically logged. You can check your history:

```bash
# View today's journal
cat ~/.openclaw/workspace/memory/$(date +%F).md
```

The log includes:
- Asset and direction
- Entry price
- SL and TP
- Result (profit/loss)
- Trade rationale
- Score at entry time

---

## ⚠️ Important Rules

### Don't
- ❌ **Don't increase size** after a big win without justification
- ❌ **No martingale** (doubling down on losses)
- ❌ **No revenge trading** (trying to recover losses quickly)
- ❌ **Don't switch assets within hours** — enter and wait for resolution
- ❌ **Don't trade without defined SL and TP**

### Always do
- ✅ Respect the scanner score
- ✅ Place OCO from entry
- ✅ Journal every session
- ✅ Pause after 3 consecutive losses
- ✅ Reduce size if BTC is bearish

---

## 🔄 Typical workflow

```
1. 📊 Scanner finds opportunity (score 7+)
2. 🛡️ Entry Validator checks conditions
3. ✅ If all good → Simulate or execute buy only when live trading is enabled
4. 📈 Position Tracker monitors 24/7
5. ⏰ SL or TP is evaluated → Position closes only when live trading is enabled
6. 📝 Journal logs the result
7. 📊 Report sent to user via Telegram
```

---

## ⚙️ Engine Status

The `engine` command lets you view:

- Open positions
- Trade history
- Internal monitor state
- Trailing and SL/TP configuration

```bash
# View engine status
python3 tools/clawtrader.py engine
```

---

## 🆘 Useful commands

```bash
# Check installation
python3 tools/clawtrader.py health

# Professional multi-timeframe scanner
python3 tools/clawtrader.py pro-scan --symbols BTCUSDT ETHUSDT SOLUSDT

# Professional plan for one asset
python3 tools/clawtrader.py decide BTCUSDT

# Analyze Smart Money
python3 tools/clawtrader.py smart-money BTCUSDT

# Validate a trade proposal
python3 tools/clawtrader.py risk --entry 100 --current 101 --stop 97 --take-profit 106 --score 7 --amount 300

# Check system status
python3 tools/clawtrader.py health
```
