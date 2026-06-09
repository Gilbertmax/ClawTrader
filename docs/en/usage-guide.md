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
python3 tools/market_scanner.py

# Autonomous monitoring (processes signals automatically)
python3 tools/autonomous_monitor.py

# View web dashboard
python3 tools/server.py
# Open http://localhost:5000 in your browser

# Run the orchestrator
python3 tools/orchestrator.py
```

### 3. From OpenClaw
```bash
openclaw
# Talk to ClawTrader like your personal trading assistant
```

---

## 📊 Interpreting scanner signals

The scanner assigns a **score** to each detected opportunity:

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
3. ✅ If all good → Execute buy on Binance
4. 📈 Position Tracker monitors 24/7
5. ⏰ SL or TP executes → Position closed
6. 📝 Journal logs the result
7. 📊 Report sent to user via Telegram
```

---

## 🌐 Web dashboard

The web dashboard (port 5000) lets you view:

- Open positions
- Trade history
- Account balance
- Recent scanner signals
- Performance statistics

```bash
# Start the dashboard
python3 tools/server.py
# Open: http://localhost:5000
```

---

## 🆘 Useful commands

```bash
# Test Binance connection
python3 -c "from tools.crypto_live import *; print(get_binance_ticker('BTCUSDT'))"

# Quick analysis
python3 tools/trading_analytics.py BTC/USDT 1h

# Check system status
ls -la ~/.openclaw/workspace/.env && echo "✅ .env OK" || echo "❌ .env not found"
```
