#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              🦞 ClawTrader — Instalador                     ║
║  Configuración automatizada con soporte ES/EN               ║
║  Binance + Alpaca + Telegram                                ║
╚══════════════════════════════════════════════════════════════╝
"""
import shutil
from pathlib import Path

VERSION = "1.0.0"
SCRIPT_DIR = Path(__file__).resolve().parent
HOME = Path.home()
OPENCLAW_HOME = HOME / ".openclaw"
WORKSPACE = OPENCLAW_HOME / "workspace"
TOOLS_DIR = WORKSPACE / "tools"
SKILLS_DIR = OPENCLAW_HOME / "skills"

# ─── Mensajes multi-idioma ───
MSGS = {
    "es": {
        "welcome":       "🦞 ClawTrader v{VERSION} — Instalador",
        "lang_prompt":   "🌐 Idioma / Language [es/en]: ",
        "welcome_msg":   "Bienvenido al instalador de ClawTrader.\nSe configurará tu asistente de trading autónomo en OpenClaw.",
        "step_keys":     "🔑 PASO 1 — Configuración de APIs",
        "step_deploy":   "📁 PASO 2 — Despliegue de archivos",
        "step_restart":  "🔄 PASO 3 — Reinicio de OpenClaw",
        "step_finish":   "✅ PASO 4 — Finalización",
        "openclaw_ok":   "✅ OpenClaw detectado: {version}",
        "openclaw_path_hint": """
⚠️  OpenClaw está instalado, pero no está en PATH.
Para que funcione en nuevas terminales agrega esto a tu ~/.bashrc o ~/.zshrc:

   export PATH="{bin_dir}:$PATH"
""",
        "openclaw_missing": """
❌ OpenClaw no está instalado.

ClawTrader instala skills y tools dentro de OpenClaw, así que primero necesitas instalar OpenClaw:

   curl -fsSL https://openclaw.ai/install.sh | bash

Después verifica:

   openclaw --version

Cuando eso funcione, vuelve a ejecutar:

   python3 install.py
""",
        "select_binance":"¿Operarás en Binance? (s/N): ",
        "select_alpaca": "¿Operarás en Alpaca Paper Trading? (s/N): ",
        "select_tg":     "¿Configurar notificaciones por Telegram? (s/N): ",
        "ask_binance_key":"Pega tu API Key de Binance: ",
        "ask_binance_sec":"Pega tu Secret Key de Binance: ",
        "ask_alpaca_key":"Pega tu API Key de Alpaca: ",
        "ask_alpaca_sec":"Pega tu Secret Key de Alpaca: ",
        "ask_tg_bot":    "Pega tu Token de Bot de Telegram: ",
        "ask_tg_chat":   "Pega tu Chat ID de Telegram: ",
        "env_created":   "✅ .env creado en {path}",
        "deploy_ok":     "✅ Archivos desplegados correctamente",
        "restart_ok":    "✅ Servicio de OpenClaw reiniciado",
        "restart_warn":  "⚠️  No se pudo reiniciar OpenClaw automáticamente. Reinicia manualmente con: openclaw daemon restart",
        "finish_msg": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Instalación completada.

📌  Próximos pasos:

1. OpenClaw ya fue verificado por el instalador.

2. El workspace ya está configurado en:
   ~/.openclaw/workspace/

3. Para iniciar una sesión de trading:
   → Habla con ClawTrader en Telegram

4. Si necesitas regenerar el .env:
   python3 install.py

5. Documentación en:
   ./docs/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        "err_no_binance": "⚠️  Sin Binance no se puede operar crypto. El instalador continuará pero necesitarás al menos una API.",
    },
    "en": {
        "welcome":       "🦞 ClawTrader v{VERSION} — Installer",
        "lang_prompt":   "🌐 Idioma / Language [es/en]: ",
        "welcome_msg":   "Welcome to the ClawTrader installer.\nYour autonomous trading assistant will be configured for OpenClaw.",
        "step_keys":     "🔑 STEP 1 — API Configuration",
        "step_deploy":   "📁 STEP 2 — File Deployment",
        "step_restart":  "🔄 STEP 3 — Restart OpenClaw",
        "step_finish":   "✅ STEP 4 — Finish",
        "openclaw_ok":   "✅ OpenClaw detected: {version}",
        "openclaw_path_hint": """
⚠️  OpenClaw is installed, but it is not in PATH.
To make it work in new terminals, add this to your ~/.bashrc or ~/.zshrc:

   export PATH="{bin_dir}:$PATH"
""",
        "openclaw_missing": """
❌ OpenClaw is not installed.

ClawTrader installs skills and tools inside OpenClaw, so you need to install OpenClaw first:

   curl -fsSL https://openclaw.ai/install.sh | bash

Then verify:

   openclaw --version

When that works, run again:

   python3 install.py
""",
        "select_binance":"Will you trade on Binance? (y/N): ",
        "select_alpaca": "Will you trade on Alpaca Paper Trading? (y/N): ",
        "select_tg":     "Configure Telegram notifications? (y/N): ",
        "ask_binance_key":"Paste your Binance API Key: ",
        "ask_binance_sec":"Paste your Binance Secret Key: ",
        "ask_alpaca_key":"Paste your Alpaca API Key: ",
        "ask_alpaca_sec":"Paste your Alpaca Secret Key: ",
        "ask_tg_bot":    "Paste your Telegram Bot Token: ",
        "ask_tg_chat":   "Paste your Telegram Chat ID: ",
        "env_created":   "✅ .env created at {path}",
        "deploy_ok":     "✅ Files deployed successfully",
        "restart_ok":    "✅ OpenClaw service restarted",
        "restart_warn":  "⚠️  OpenClaw could not be restarted automatically. Restart manually with: openclaw daemon restart",
        "finish_msg": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Installation complete.

📌  Next steps:

1. OpenClaw was verified by the installer.

2. Workspace configured at:
   ~/.openclaw/workspace/

3. To start a trading session:
   → Talk to ClawTrader on Telegram

4. To regenerate .env:
   python3 install.py

5. Documentation at:
   ./docs/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        "err_no_binance": "⚠️  Without Binance you can't trade crypto. The installer will continue but you'll need at least one API.",
    }
}

def say(key, lang="es", **kw):
    return MSGS[lang][key].format(**kw)

def prompt(msg, default="", lang="es"):
    v = input(msg).strip()
    return v if v else default

def prompt_yesno(msg, default="n", lang="es"):
    while True:
        v = input(msg).strip().lower()
        if v in ("s", "y", "si", "yes", "sí"):
            return True
        if v in ("n", "no", ""):
            return False
        print("  Responde s/n o y/n")

def ensure_openclaw(lang):
    exe = shutil.which("openclaw")
    fallback = HOME / ".npm-global" / "bin" / "openclaw"
    path_hint = False
    if not exe and fallback.exists():
        exe = str(fallback)
        path_hint = True
    if not exe:
        print(MSGS[lang]["openclaw_missing"])
        raise SystemExit(1)

    try:
        import subprocess
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

    print(say("openclaw_ok", lang, version=version))
    if path_hint:
        print(MSGS[lang]["openclaw_path_hint"].format(bin_dir=fallback.parent))
    return exe

def restart_openclaw(exe, lang):
    import subprocess
    for command in (["daemon", "restart"], ["gateway", "restart"]):
        try:
            result = subprocess.run(
                [exe, *command],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if result.returncode == 0:
                print(say("restart_ok", lang))
                return True
        except Exception:
            continue

    print(say("restart_warn", lang))
    return False

def main():
    # ─── Idioma ───
    lang = input(MSGS["es"]["lang_prompt"]).strip().lower()
    if lang not in ("es", "en"):
        lang = "es"
    
    print(f"\n{'='*60}")
    print(say("welcome", lang, VERSION=VERSION))
    print(f"{'='*60}\n")
    print(say("welcome_msg", lang))
    print()
    openclaw_exe = ensure_openclaw(lang)

    # ─── PASO 1: Keys ───
    print(f"\n--- {say('step_keys', lang)} ---\n")
    
    env_data = {}
    
    # Binance
    use_binance = prompt_yesno(say("select_binance", lang), lang=lang)
    if use_binance:
        env_data["BINANCE_API_KEY"] = prompt(say("ask_binance_key", lang), lang=lang)
        env_data["BINANCE_SECRET_KEY"] = prompt(say("ask_binance_sec", lang), lang=lang)
    else:
        print(say("err_no_binance", lang))
    
    # Alpaca
    use_alpaca = prompt_yesno(say("select_alpaca", lang), lang=lang)
    if use_alpaca:
        env_data["ALPACA_API_KEY"] = prompt(say("ask_alpaca_key", lang), lang=lang)
        env_data["ALPACA_SECRET_KEY"] = prompt(say("ask_alpaca_sec", lang), lang=lang)
        env_data["ALPACA_BASE_URL"] = "https://paper-api.alpaca.markets/v2"
    
    # Telegram
    use_tg = prompt_yesno(say("select_tg", lang), lang=lang)
    if use_tg:
        env_data["TELEGRAM_BOT_TOKEN"] = prompt(say("ask_tg_bot", lang), lang=lang)
        env_data["TELEGRAM_CHAT_ID"] = prompt(say("ask_tg_chat", lang), lang=lang)
    
    # ─── Generar .env ───
    env_data["CLAWTRADER_DRY_RUN"] = "true"
    env_data["CLAWTRADER_LIVE_TRADING"] = "false"
    env_data["CLAWTRADER_CAPITAL"] = env_data.get("CLAWTRADER_CAPITAL", "1000")
    env_data["CLAWTRADER_STATUS_DIR"] = str(WORKSPACE / "state")

    env_path = WORKSPACE / ".env"
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    
    with open(env_path, "w") as f:
        f.write("# ClawTrader — Credenciales (generado por instalador)\n")
        f.write("# NO subir a GitHub\n\n")
        for k, v in env_data.items():
            if v:
                f.write(f"{k}={v}\n")
    
    print(f"\n✅ {say('env_created', lang, path=env_path)}")
    
    # ─── Crear .env.example ───
    example_path = WORKSPACE / ".env.example"
    with open(example_path, "w") as f:
        f.write("# .env.example — Copia como .env y completa tus keys\n")
        f.write("# BINANCE\n")
        f.write("BINANCE_API_KEY=\n")
        f.write("BINANCE_SECRET_KEY=\n\n")
        f.write("# ALPACA (opcional — paper trading demo)\n")
        f.write("# ALPACA_API_KEY=\n")
        f.write("# ALPACA_SECRET_KEY=\n")
        f.write("# ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2\n\n")
        f.write("# TELEGRAM (opcional — notificaciones)\n")
        f.write("# TELEGRAM_BOT_TOKEN=\n")
        f.write("# TELEGRAM_CHAT_ID=\n")
        f.write("\n# SEGURIDAD\n")
        f.write("CLAWTRADER_DRY_RUN=true\n")
        f.write("CLAWTRADER_LIVE_TRADING=false\n")
        f.write("CLAWTRADER_CAPITAL=1000\n")
        f.write(f"CLAWTRADER_STATUS_DIR={WORKSPACE / 'state'}\n")
    
    print(f"✅ .env.example creado en {example_path}")
    
    # ─── PASO 2: Despliegue ───
    print(f"\n--- {say('step_deploy', lang)} ---\n")
    
    # Copiar scripts si hay source
    src_tools = SCRIPT_DIR / "tools"
    dst_tools = TOOLS_DIR
    if src_tools.exists() and src_tools != dst_tools:
        dst_tools.mkdir(parents=True, exist_ok=True)
        for f in src_tools.iterdir():
            if f.suffix == ".py":
                shutil.copy2(f, dst_tools / f.name)
    
    # Copiar skills
    src_skills = SCRIPT_DIR / "skills" / lang
    if src_skills.exists():
        SKILLS_DIR.mkdir(parents=True, exist_ok=True)
        for sdir in src_skills.iterdir():
            if sdir.is_dir():
                ddir = SKILLS_DIR / sdir.name
                if ddir.exists():
                    shutil.rmtree(ddir)
                shutil.copytree(sdir, ddir)
    
    print(say("deploy_ok", lang))

    # ─── PASO 3: Reiniciar OpenClaw ───
    print(f"\n--- {say('step_restart', lang)} ---\n")
    restart_openclaw(openclaw_exe, lang)
    
    # ─── PASO 4: Fin ───
    print(f"\n--- {say('step_finish', lang)} ---")
    print(say("finish_msg", lang))
    
    state_dir = WORKSPACE / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Estado local creado en: {state_dir}")

if __name__ == "__main__":
    main()
