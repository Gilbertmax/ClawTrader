#!/usr/bin/env python3
"""ClawTrader install healthcheck."""
import importlib.util
import json
from pathlib import Path

from load_env import load_env, tools_dir, workspace_dir

REQUIRED_MODULES = ["ccxt", "numpy", "pandas", "requests", "talib", "yfinance"]


def check_module(name):
    return importlib.util.find_spec(name) is not None


def main():
    load_env()
    workspace = workspace_dir()
    tools = tools_dir()
    skills = Path.home() / ".openclaw" / "skills"
    env_path = workspace / ".env"

    result = {
        "workspace": str(workspace),
        "env": env_path.exists(),
        "tools_dir": tools.exists(),
        "skills_dir": skills.exists(),
        "modules": {name: check_module(name) for name in REQUIRED_MODULES},
        "sample_tools": sorted(p.name for p in tools.glob("*.py"))[:8] if tools.exists() else [],
        "sample_skills": sorted(p.name for p in skills.iterdir() if p.is_dir())[:8] if skills.exists() else [],
    }
    result["ok"] = (
        result["env"]
        and result["tools_dir"]
        and result["skills_dir"]
        and all(result["modules"].values())
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
