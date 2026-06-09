#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║              🦞 ClawTrader — Instalador                     ║
║  Configuración automatizada con soporte ES/EN               ║
║  Binance + Alpaca + Telegram                                ║
╚══════════════════════════════════════════════════════════════╝
"""
import os, sys, json, shutil, subprocess, getpass

VERSION = "1.0.0"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
HOME = os.path.expanduser("~")

# ─── Mensajes multi-idioma ───
MSGS = {
    "es": {
        "welcome":       "🦞 ClawTrader v{VERSION} — Instalador",
        "lang_prompt":   "🌐 Idioma / Language [es/en]: ",
        "welcome_msg":   "Bienvenido al instalador de ClawTrader.\nSe configurará tu asistente de trading autónomo en OpenClaw.",
        "step_keys":     "🔑 PASO 1 — Configuración de APIs",
        "step_deploy":   "📁 PASO 2 — Despliegue de archivos",
        "step_crons":    "⏰ PASO 3 — Programación de monitoreo",
        "step_finish":   "✅ PASO 4 — Finalización",
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
        "finish_msg": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Instalación completada.

📌  Próximos pasos:

1. Asegúrate de tener OpenClaw instalado:
   npm install -g openclaw

2. El workspace ya está configurado en:
   ~/.openclaw/workspace/

3. Para iniciar una sesión de trading:
   → Habla con ClawTrader en Telegram

4. Si necesitas regenerar el .env:
   python3 ~/ClawTrader/install.py

5. Documentación en:
   ~/ClawTrader/docs/

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
        "step_crons":    "⏰ STEP 3 — Monitoring Schedule",
        "step_finish":   "✅ STEP 4 — Finish",
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
        "finish_msg": """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅  Installation complete.

📌  Next steps:

1. Make sure OpenClaw is installed:
   npm install -g openclaw

2. Workspace configured at:
   ~/.openclaw/workspace/

3. To start a trading session:
   → Talk to ClawTrader on Telegram

4. To regenerate .env:
   python3 ~/ClawTrader/install.py

5. Documentation at:
   ~/ClawTrader/docs/

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
    env_path = os.path.join(WORKSPACE, ".env")
    os.makedirs(WORKSPACE, exist_ok=True)
    
    with open(env_path, "w") as f:
        f.write("# ClawTrader — Credenciales (generado por instalador)\n")
        f.write("# NO subir a GitHub\n\n")
        for k, v in env_data.items():
            if v:
                f.write(f"{k}={v}\n")
    
    print(f"\n✅ {say('env_created', lang, path=env_path)}")
    
    # ─── Crear .env.example ───
    example_path = os.path.join(WORKSPACE, ".env.example")
    with open(example_path, "w") as f:
        f.write("# .env.example — Copia como .env y completa tus keys\n")
        f.write("# BINANCE\n")
        f.write("BINANCE_API_KEY=***\n")
        f.write("BINANCE_SECRET_KEY=***\n\n")
        f.write("# ALPACA (opcional — paper trading demo)\n")
        f.write("# ALPACA_API_KEY=***\n")
        f.write("# ALPACA_SECRET_KEY=***\n")
        f.write("# ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2\n\n")
        f.write("# TELEGRAM (opcional — notificaciones)\n")
        f.write("# TELEGRAM_BOT_TOKEN=***\n")
        f.write("# TELEGRAM_CHAT_ID=***\n")
    
    print(f"✅ .env.example creado en {example_path}")
    
    # ─── Crear keys_b64.json ───
    if use_binance and env_data.get("BINANCE_API_KEY") and env_data.get("BINANCE_SECRET_KEY"):
        import base64
        b64_data = {
            "binance": {
                "api_key_b64": base64.b64encode(env_data["BINANCE_API_KEY"].encode()).decode(),
                "secret_key_b64": base64.b64encode(env_data["BINANCE_SECRET_KEY"].encode()).decode()
            }
        }
        keys_b64_path = os.path.join(os.path.dirname(WORKSPACE), "tools", "keys_b64.json")
        os.makedirs(os.path.dirname(keys_b64_path), exist_ok=True)
        with open(keys_b64_path, "w") as f:
            json.dump(b64_data, f, indent=2)
        print(f"✅ keys_b64.json creado para market_scanner.py")
    
    # ─── PASO 2: Despliegue ───
    print(f"\n--- {say('step_deploy', lang)} ---\n")
    
    # Copiar scripts si hay source
    src_tools = os.path.join(SCRIPT_DIR, "tools")
    dst_tools = os.path.join(os.path.dirname(WORKSPACE), "tools")
    if os.path.exists(src_tools) and src_tools != dst_tools:
        os.makedirs(dst_tools, exist_ok=True)
        for f in os.listdir(src_tools):
            if f.endswith(".py") or f.endswith(".json"):
                shutil.copy2(os.path.join(src_tools, f), dst_tools)
    
    # Copiar skills
    src_skills = os.path.join(SCRIPT_DIR, "skills")
    dst_skills = os.path.expanduser("~/.openclaw/skills")
    if os.path.exists(src_skills):
        os.makedirs(dst_skills, exist_ok=True)
        for skill_dir in os.listdir(src_skills):
            sdir = os.path.join(src_skills, skill_dir)
            if os.path.isdir(sdir):
                ddir = os.path.join(dst_skills, skill_dir)
                os.makedirs(ddir, exist_ok=True)
                for sf in os.listdir(sdir):
                    shutil.copy2(os.path.join(sdir, sf), ddir)
    
    print(say("deploy_ok", lang))
    
    # ─── PASO 4: Fin ───
    print(f"\n--- {say('step_finish', lang)} ---")
    print(say("finish_msg", lang))
    
    # ─── Crear carpeta del proyecto en Documentos ───
    docs_project = os.path.join(HOME, "Documentos", "ClawTrader")
    os.makedirs(docs_project, exist_ok=True)
    print(f"📁 Proyecto espejo creado en: {docs_project}")

if __name__ == "__main__":
    main()
