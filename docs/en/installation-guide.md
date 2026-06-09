# 🦞 ClawTrader — Installation Guide

> This guide will walk you step by step from zero to having ClawTrader up and running.

---

## 📋 Prerequisites

Before starting, make sure you have:

- **Node.js** ≥ v18
  ```bash
  node --version  # Should show v18 or higher
  ```
- **Python 3.9+**
  ```bash
  python3 --version  # Should show Python 3.9 or higher
  ```
- **pip** (Python package manager)
  ```bash
  pip3 --version
  ```
- **Git**
  ```bash
  git --version
  ```

## Step 1: Clone the project

```bash
git clone https://github.com/your-user/ClawTrader.git
cd ClawTrader
```

Or if you already have the files locally, just navigate to the folder:

```bash
cd ClawTrader
```

## Step 2: Create Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Linux/Mac
# or
venv\Scripts\activate      # On Windows
```

You'll see `(venv)` at the beginning of your command line.

## Step 3: Install Python dependencies

```bash
pip install -r requirements.txt
```

If `TA-Lib` fails, install the C library first:

```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# Mac
brew install ta-lib

# Then install the wrapper
pip install TA-Lib
```

## Step 4: Install OpenClaw

```bash
npm install -g openclaw
```

Verify it's installed:

```bash
openclaw --version
```

## Step 5: Create a Binance account

> 💡 If you don't have an account yet, create one with my referral link:
> [Create Binance account](https://www.binance.com/referral/earn-together/refer2earn-usdc/claim?hl=es-LA&ref=GRO_28502_BYDAT&utm_source=referral_entrance)

### Create an API Key on Binance

1. Log in to your Binance account
2. Go to **API Management**:
   - Profile → API Management
3. Click **Create API**
4. Select the type: **API Key**
5. Complete security verification (2FA, email)
6. In **API Restrictions**, enable:
   - ✅ **Enable Reading**
   - ✅ **Enable Spot & Margin Trading**
   - ❌ **Enable Withdrawals** — DO NOT enable for security
7. Note your **API Key** and **Secret Key** (Secret Key is shown ONLY once)

⚠️ **NEVER share your Secret Key or upload it to GitHub**

## Step 6: Run the interactive installer

The installer validates `openclaw --version` at startup. If OpenClaw is not installed or is not in `PATH`, it fails before asking for credentials.

```bash
python3 install.py
```

The installer will guide you through:
1. **Language** — Choose English (en) or Spanish (es)
2. **Binance** — Enter your API Key and Secret Key
3. **Alpaca** (optional) — For paper trading
4. **Telegram** (optional) — For notifications

When finished, the following will be created:
- `~/.openclaw/workspace/.env` — Your credentials
- `~/.openclaw/workspace/state/` — Local state and temporary reports

## Step 7: Deploy tools and skills

```bash
# For Spanish skills
bash deploy.sh es

# For English skills
bash deploy.sh en
```

This copies ClawTrader's scripts and skills into the OpenClaw workspace.

## Step 8: Launch ClawTrader!

```bash
openclaw
```

## 🔧 Troubleshooting

### Error: "No module named ccxt"
```bash
pip install ccxt
```

### Error: "openclaw: command not found"
```bash
npm install -g openclaw
```

### Binance permission error
- Verify the API Key has **Spot Trading** permissions
- If using IP Restriction, add your server/machine IP

### TA-Lib error
```bash
# Instead of pip install TA-Lib, use:
pip install TA-Lib --no-binary TA-Lib
```

### Skills not appearing in OpenClaw
```bash
# Verify skills are in the correct location:
ls ~/.openclaw/skills/
# You should see folders like 00-trader-core, 01-market-structure, etc.
```

## ✅ Installation verification

Run these commands to verify everything is correct:

```bash
# 1. Verify virtual environment
which python3

# 2. Verify the environment file exists without printing secrets
test -f ~/.openclaw/workspace/.env && echo ".env OK"

# 3. Verify tools
ls tools/*.py | wc -l

# 4. Verify skills
ls skills/en/ | head -5

# 5. Test public Binance connection
python3 tools/clawtrader.py snapshot --exchanges binance --symbols BTC/USDT

# 6. Verify OpenClaw
openclaw --version
```

---

**Having issues?** Check documentation in `docs/` or open an issue on GitHub.
