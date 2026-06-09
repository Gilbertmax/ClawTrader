# 🦞 ClawTrader — Guía de Instalación

> Esta guía te llevará paso a paso desde cero hasta tener ClawTrader funcionando.

---

## 📋 Prerrequisitos

Antes de empezar, asegúrate de tener:

- **Node.js** ≥ v18
  ```bash
  node --version  # Debe mostrar v18 o superior
  ```
- **Python 3.9+**
  ```bash
  python3 --version  # Debe mostrar Python 3.9 o superior
  ```
- **pip** (gestor de paquetes de Python)
  ```bash
  pip3 --version
  ```
- **Git**
  ```bash
  git --version
  ```

## Paso 1: Clonar el proyecto

```bash
git clone https://github.com/tu-usuario/ClawTrader.git
cd ClawTrader
```

O si ya tienes los archivos localmente, simplemente navega a la carpeta:

```bash
cd ClawTrader
```

## Paso 2: Crear entorno virtual de Python

```bash
python3 -m venv venv
source venv/bin/activate   # En Linux/Mac
# ó
venv\Scripts\activate      # En Windows
```

Verás `(venv)` al inicio de la línea de comandos.

## Paso 3: Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

Si `TA-Lib` da problemas, instala primero la librería C:

```bash
# Ubuntu/Debian
sudo apt-get install ta-lib

# Mac
brew install ta-lib

# Luego instala el wrapper
pip install TA-Lib
```

## Paso 4: Instalar OpenClaw

```bash
npm install -g openclaw
```

Verifica que esté instalado:

```bash
openclaw --version
```

## Paso 5: Crear una cuenta en Binance

> 💡 Si aún no tienes cuenta, puedes crear una con mi enlace de referido:
> [Crear cuenta en Binance](https://www.binance.com/referral/earn-together/refer2earn-usdc/claim?hl=es-LA&ref=GRO_28502_BYDAT&utm_source=referral_entrance)

### Crear API Key en Binance

1. Inicia sesión en tu cuenta de Binance
2. Ve a **API Management** (Gestión de API):
   - Perfil → API Management
3. Haz clic en **Create API**
4. Selecciona el tipo: **API Key**
5. Completa la verificación de seguridad (2FA, email)
6. En **Restricciones de API**, habilita:
   - ✅ **Enable Reading** (Lectura)
   - ✅ **Enable Spot & Margin Trading** (Trading Spot)
   - ❌ **Enable Withdrawals** (Retiros) — NO habilitar por seguridad
7. Anota tu **API Key** y **Secret Key** (la Secret Key SOLO se muestra una vez)

⚠️ **NUNCA compartas tu Secret Key ni la subas a GitHub**

## Paso 6: Ejecutar el instalador interactivo

El instalador valida `openclaw --version` al inicio. Si OpenClaw no está instalado o no está en `PATH`, fallará antes de pedir credenciales.

```bash
python3 install.py
```

El instalador te guiará por:
1. **Idioma** — Elige español (es) o inglés (en)
2. **Binance** — Ingresa tu API Key y Secret Key
3. **Alpaca** (opcional) — Para paper trading
4. **Telegram** (opcional) — Para notificaciones

Al finalizar, se habrá creado:
- `~/.openclaw/workspace/.env` — Tus credenciales
- `~/.openclaw/workspace/state/` — Estado local y reportes temporales

## Paso 7: Desplegar tools y skills

```bash
# Si quieres los skills en español
bash deploy.sh es

# Si quieres los skills en inglés
bash deploy.sh en
```

Esto copiará los scripts y skills de ClawTrader al workspace de OpenClaw.

## Paso 8: ¡Iniciar ClawTrader!

```bash
openclaw
```

## 🔧 Solución de problemas

### Error: "No module named ccxt"
```bash
pip install ccxt
```

### Error: "openclaw: command not found"
```bash
npm install -g openclaw
```

### Error de permisos en Binance
- Verifica que la API Key tenga permisos de **Spot Trading**
- Si usas IP Restriction, añade la IP de tu servidor/máquina

### Error con TA-Lib
```bash
# En lugar de pip install TA-Lib, usa:
pip install TA-Lib --no-binary TA-Lib
```

### No aparecen las skills en OpenClaw
```bash
# Verifica que los skills estén en la ubicación correcta:
ls ~/.openclaw/skills/
# Deberías ver las carpetas 00-trader-core, 01-market-structure, etc.
```

## ✅ Verificación de instalación

Ejecuta estos comandos para verificar que todo está correcto:

```bash
# 1. Verificar entorno virtual
which python3

# 2. Verificar que existe el archivo de entorno sin mostrar secretos
test -f ~/.openclaw/workspace/.env && echo ".env OK"

# 3. Verificar tools
ls tools/*.py | wc -l

# 4. Verificar skills
ls skills/es/ | head -5

# 5. Probar conexión pública a Binance
python3 tools/clawtrader.py snapshot --exchanges binance --symbols BTC/USDT

# 6. Verificar OpenClaw
openclaw --version
```

---

**¿Problemas?** Consulta la documentación en `docs/` o abre un issue en GitHub.
