# Contribuir a ClawTrader

Gracias por querer colaborar. ClawTrader es un proyecto open source para construir un asistente de trading configurable, seguro y fácil de instalar. Como toca temas de APIs, credenciales y posible ejecución financiera, las reglas de contribución son más estrictas que en un proyecto normal.

## Principios

- Seguridad primero.
- Trading real desactivado por defecto.
- Código portable, sin rutas personales.
- Documentación honesta: no prometas ganancias.
- Skills en español e inglés con la misma estructura.
- Cambios pequeños, claros y fáciles de revisar.

## Reglas Obligatorias

No subas credenciales ni datos sensibles:

```text
.env
API keys
secret keys
tokens de Telegram
cuentas personales
balances reales
archivos de sesiones privadas
```

No hardcodees rutas locales:

```text
No: /home/usuario/...
No: C:\Users\...
Si: Path.home() / ".openclaw" / "workspace"
```

No actives trading real por defecto. Cualquier cambio relacionado con órdenes debe respetar:

```env
CLAWTRADER_DRY_RUN=true
CLAWTRADER_LIVE_TRADING=false
```

No agregues lógica que mande órdenes reales sin validación, control de riesgo y confirmación explícita de configuración.

## Estructura Del Proyecto

```text
tools/        Scripts Python y utilidades
skills/es/    Skills en español
skills/en/    Skills en inglés
docs/es/      Documentación en español
docs/en/      Documentación en inglés
install.py    Instalador interactivo
deploy.sh     Despliegue de skills/tools
```

Si agregas una skill en `skills/es`, agrega su equivalente en `skills/en`. Si agregas documentación en `docs/es`, agrega su equivalente en `docs/en`.

## Flujo Recomendado

1. Haz fork del proyecto.
2. Crea una rama con nombre claro:

```bash
git checkout -b fix/install-paths
git checkout -b feat/new-risk-check
git checkout -b docs/contributing-guide
```

3. Realiza cambios pequeños.
4. Corre verificaciones locales.
5. Abre un pull request explicando qué cambió y cómo lo probaste.

## Verificaciones Mínimas

Antes de enviar un PR:

```bash
python3 -m compileall -q install.py tools
python3 tools/healthcheck.py
python3 tools/market_scanner.py
```

Para probar instalación sin tocar tu configuración real:

```bash
tmp=$(mktemp -d)
HOME="$tmp" python3 install.py
```

Si modificas el dashboard:

```bash
python3 tools/server.py --host 127.0.0.1 --port 8765
curl -s http://127.0.0.1:8765/health
```

## Reglas Para Tools Python

- Usa `Path.home()` y rutas configurables.
- Carga `.env` con `tools/load_env.py`.
- No uses credenciales hardcodeadas.
- No escribas estado en `/tmp` si puede vivir en `~/.openclaw/workspace/state`.
- Mantén `dry-run` como comportamiento seguro.
- Maneja errores de API sin romper el proceso.
- Evita dependencias nuevas si no son necesarias.

## Reglas Para Skills

Cada skill debe tener front matter:

```yaml
---
name: skill-name
description: Descripción clara y breve.
---
```

Las skills deben:

- Ser específicas.
- Evitar promesas de rentabilidad.
- Incluir reglas de riesgo cuando aplique.
- Tener equivalente ES/EN.
- No incluir nombres personales, rutas locales ni datos privados.
- Marcar como `[LEGACY]` cualquier skill mantenida solo por compatibilidad.

## Reglas Para Documentación

La documentación debe:

- Explicar pasos reproducibles.
- No pedir imprimir secretos en consola.
- No vender base64 como cifrado.
- Distinguir demo, paper trading y trading real.
- Decir claramente que el trading implica riesgo de pérdida.

## Pull Requests

Un buen PR incluye:

- Resumen breve.
- Archivos tocados.
- Riesgos del cambio.
- Comandos de verificación ejecutados.
- Capturas o logs si aplica.

Plantilla sugerida:

```markdown
## Resumen

## Cambios

## Riesgos

## Verificación
- [ ] python3 -m compileall -q install.py tools
- [ ] python3 tools/healthcheck.py
- [ ] Instalación probada en HOME temporal
```

## Cambios De Seguridad

Si el PR toca ejecución de órdenes, credenciales, permisos de API, Binance, Alpaca o Telegram, debe explicar:

- Qué permisos necesita.
- Cómo evita operar real por accidente.
- Qué pasa si faltan credenciales.
- Cómo se audita el resultado.
- Cómo se revierte o desactiva.

## Comunidad

Próximamente habrá un servidor de Discord para coordinar ideas, soporte y contribuciones.

Mientras tanto, puedes mandar mensaje por Discord a:

```text
gilbertmax
```

## Licencia

Al contribuir aceptas que tus cambios se publiquen bajo la licencia MIT del proyecto.
