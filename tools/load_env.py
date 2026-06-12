"""
load_env.py — Carga .env desde el workspace raíz.
Usar en scripts que no tengan python-dotenv disponible.
"""
import os
from pathlib import Path

def load_env(path=None):
    if path is None:
        candidates = [
            Path(__file__).resolve().parents[1] / ".env",
            Path.home() / ".openclaw" / "workspace" / ".env",
        ]
        path = next((p for p in candidates if p.exists()), candidates[-1])
    else:
        path = Path(path)
    if not path.exists():
        print(f"  ⚠️  .env no encontrado en {path}")
        return False
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip("\"'")
            if not os.environ.get(k):
                os.environ[k] = v
    return True

def workspace_dir():
    return Path(os.environ.get("CLAWTRADER_WORKSPACE", Path.home() / ".openclaw" / "workspace")).expanduser()

def tools_dir():
    return Path(os.environ.get("CLAWTRADER_TOOLS_DIR", workspace_dir() / "tools")).expanduser()

def status_dir():
    path = Path(os.environ.get("CLAWTRADER_STATUS_DIR", workspace_dir() / "state")).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path

def env_float(name, default):
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return float(default)

def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "s", "si", "sí"}
