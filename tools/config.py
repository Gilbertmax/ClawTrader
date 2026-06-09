#!/usr/bin/env python3
"""Shared ClawTrader configuration."""
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from load_env import env_bool, env_float, load_env, status_dir, tools_dir, workspace_dir


@dataclass
class ClawTraderConfig:
    workspace: Path
    tools_dir: Path
    status_dir: Path
    dry_run: bool
    live_trading: bool
    capital: float
    binance_configured: bool
    alpaca_configured: bool
    telegram_configured: bool

    def safe_dict(self):
        data = asdict(self)
        data["workspace"] = str(self.workspace)
        data["tools_dir"] = str(self.tools_dir)
        data["status_dir"] = str(self.status_dir)
        return data


def get_config():
    load_env()
    return ClawTraderConfig(
        workspace=workspace_dir(),
        tools_dir=tools_dir(),
        status_dir=status_dir(),
        dry_run=env_bool("CLAWTRADER_DRY_RUN", True),
        live_trading=env_bool("CLAWTRADER_LIVE_TRADING", False),
        capital=env_float("CLAWTRADER_CAPITAL", 1000),
        binance_configured=bool(os.environ.get("BINANCE_API_KEY") and os.environ.get("BINANCE_SECRET_KEY")),
        alpaca_configured=bool(os.environ.get("ALPACA_API_KEY") and os.environ.get("ALPACA_SECRET_KEY")),
        telegram_configured=bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID")),
    )

