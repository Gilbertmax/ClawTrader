#!/usr/bin/env python3
"""ClawTrader install healthcheck."""
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

from load_env import load_env, tools_dir, workspace_dir

REQUIRED_MODULES = ["ccxt", "numpy", "pandas", "requests", "talib", "yfinance"]


def check_module(name):
    return importlib.util.find_spec(name) is not None


def check_openclaw():
    exe = shutil.which("openclaw")
    if not exe:
        return {"installed": False, "version": None}
    try:
        result = subprocess.run(
            [exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        version = (result.stdout or result.stderr or exe).strip().splitlines()[0]
    except Exception:
        version = exe
    return {"installed": True, "version": version}


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
        "openclaw": check_openclaw(),
        "modules": {name: check_module(name) for name in REQUIRED_MODULES},
        "sample_tools": sorted(p.name for p in tools.glob("*.py"))[:8] if tools.exists() else [],
        "sample_skills": sorted(p.name for p in skills.iterdir() if p.is_dir())[:8] if skills.exists() else [],
    }
    result["ok"] = (
        result["env"]
        and result["tools_dir"]
        and result["skills_dir"]
        and result["openclaw"]["installed"]
        and all(result["modules"].values())
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
