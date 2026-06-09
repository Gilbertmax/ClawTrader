"""
load_env.py — Carga .env desde el workspace raíz.
Usar en scripts que no tengan python-dotenv disponible.
"""
import os

def load_env(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if not os.path.exists(path):
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
