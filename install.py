#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║         🦞 ClawTrader v2 — Instalador                      ║
║  Binance Spot + OpenClaw                                   ║
╚══════════════════════════════════════════════════════════════╝
"""
import shutil
import subprocess
from pathlib import Path

VERSION = "2.0.0"
SCRIPT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
OPENCLAW_HOME = HOME / ".openclaw"
WORKSPACE = OPENCLAW_HOME / "workspace"
TOOLS_DST = WORKSPACE / "tools"
SKILLS_DST = OPENCLAW_HOME / "skills"

# ─── Mensajes ───
MSGS = {
    "es": {
        "welcome": f"🦞 ClawTrader v{VERSION} — Instalador",
        "openclaw_ok": "✅ OpenClaw detectado",
        "openclaw_missing": """
❌ OpenClaw no está instalado. Primero:
   curl -fsSL https://openclaw.ai/install.sh | bash
""",
        "env_ready": "✅ Archivo .env preparado en el workspace",
        "deploy_ok": "✅ Tools desplegadas en workspace de OpenClaw",
        "finish": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Instalación completada.

Comandos útiles:
  python3 tools/clawtrader.py health     → Verificar instalación
  python3 tools/clawtrader.py scan       → Escanear mercado
  python3 tools/clawtrader.py pro-scan   → Scanner profesional

Edita ~/.openclaw/workspace/.env para agregar API keys.
Trading real queda bloqueado hasta activar CLAWTRADER_LIVE_TRADING=true
y CLAWTRADER_DRY_RUN=false.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
    },
    "en": {
        "welcome": f"🦞 ClawTrader v{VERSION} — Installer",
        "openclaw_ok": "✅ OpenClaw detected",
        "openclaw_missing": """
❌ OpenClaw is not installed. First:
   curl -fsSL https://openclaw.ai/install.sh | bash
""",
        "env_ready": "✅ .env file prepared in the OpenClaw workspace",
        "deploy_ok": "✅ Tools deployed to OpenClaw workspace",
        "finish": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Installation complete.

Useful commands:
  python3 tools/clawtrader.py health     → Verify installation
  python3 tools/clawtrader.py scan       → Scan market
  python3 tools/clawtrader.py pro-scan   → Professional scanner

Edit ~/.openclaw/workspace/.env to add API keys.
Live trading stays blocked until CLAWTRADER_LIVE_TRADING=true
and CLAWTRADER_DRY_RUN=false.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
    }
}

def ensure_openclaw():
    exe = shutil.which("openclaw") or (HOME / ".npm-global/bin/openclaw")
    if not exe or not Path(exe).exists():
        print(MSGS["es"]["openclaw_missing"])
        raise SystemExit(1)
    return str(exe)

def prompt(text):
    return input(text).strip()

def prepare_env(lang):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    env_path = WORKSPACE / ".env"
    if env_path.exists():
        print(MSGS[lang]["env_ready"])
        return True

    example = SCRIPT_DIR / ".env.example"
    if example.exists():
        shutil.copy2(example, env_path)
    else:
        env_path.write_text(
            "BINANCE_API_KEY=\n"
            "BINANCE_SECRET_KEY=\n"
            "CLAWTRADER_DRY_RUN=true\n"
            "CLAWTRADER_LIVE_TRADING=false\n"
            "CLAWTRADER_CAPITAL=1000\n"
        )
    env_path.chmod(0o600)
    print(MSGS[lang]["env_ready"])
    return True

def deploy_tools():
    src = SCRIPT_DIR / "tools"
    if not src.exists():
        print("⚠️  No se encuentra tools/ en el directorio actual")
        return False
    TOOLS_DST.mkdir(parents=True, exist_ok=True)
    for f in src.iterdir():
        if f.suffix == ".py":
            shutil.copy2(f, TOOLS_DST / f.name)
    # Copiar ESTRATEGIA.md
    estrategia_src = SCRIPT_DIR / "ESTRATEGIA.md"
    if estrategia_src.exists():
        shutil.copy2(estrategia_src, WORKSPACE / "ESTRATEGIA.md")
    print("✅ Tools desplegadas")
    return True

def deploy_skills(lang):
    src = SCRIPT_DIR / "skills" / lang
    if not src.exists():
        print(f"⚠️  No se encuentra skills/{lang}")
        return False
    SKILLS_DST.mkdir(parents=True, exist_ok=True)
    for sdir in src.iterdir():
        if sdir.is_dir():
            dst = SKILLS_DST / sdir.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(sdir, dst)
    print("✅ Skills desplegadas")
    return True

def restart_openclaw(exe):
    for args in ([exe, "daemon", "restart"], [exe, "gateway", "restart"]):
        try:
            result = subprocess.run(args, capture_output=True, text=True, timeout=20, check=False)
            if result.returncode == 0:
                print("✅ OpenClaw reiniciado")
                return True
        except Exception:
            pass
    print("⚠️  No se pudo reiniciar OpenClaw automaticamente. Ejecuta: openclaw daemon restart")
    return False

def main():
    # Idioma
    lang = input("🌐 Idioma [es/en]: ").strip().lower()
    if lang not in ("es", "en"):
        lang = "es"

    print(f"\n{'='*50}")
    print(MSGS[lang]["welcome"])
    print(f"{'='*50}\n")

    openclaw_exe = ensure_openclaw()

    prepare_env(lang)
    deploy_tools()
    deploy_skills(lang)
    restart_openclaw(openclaw_exe)

    print(MSGS[lang]["finish"])

if __name__ == "__main__":
    main()
