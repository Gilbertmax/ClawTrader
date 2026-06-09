---
name: broker-safety
description: Evalúa riesgos de plataforma, credenciales, automatización, APIs no oficiales, brokers, ejecución, retiros, demo, dinero real y seguridad operativa.
---

# Broker Safety

Usa esta skill cuando el usuario mencione broker, plataforma, Olymptrade, Binance, API, bot, automatización, dinero real, credenciales o ejecución automática.

## Objetivo

Proteger al usuario de riesgos técnicos, operativos, legales y de seguridad.

## Reglas

No pedir contraseñas.

No pedir códigos 2FA.

No guardar claves privadas.

No recomendar compartir e.firma, llaves, tokens o credenciales sensibles.

No recomendar automatizar con APIs no oficiales sin advertir riesgo.

No conectar dinero real si no hay validación previa.

No usar scraping agresivo o mecanismos que puedan violar términos de plataforma.

## Evaluación de plataforma

Antes de integrar o automatizar, verificar:

Si existe API oficial.

Si existe documentación pública.

Si permite trading demo.

Si permite trading automatizado.

Si permite WebSocket.

Si permite retiro seguro.

Si tiene reputación suficiente.

Si existen riesgos de bloqueo de cuenta.

Si existen límites regulatorios.

## Olymptrade

Usar preferentemente como entorno visual y demo.

No asumir API oficial pública.

No prometer automatización.

Priorizar análisis asistido, no ejecución automática.

Si se usa herramienta de terceros, advertir riesgos:

Fragilidad.

Bloqueo de cuenta.

Cambios de plataforma.

Riesgo de seguridad.

Posible incumplimiento de términos.

## Binance

Preferir API oficial para datos.

Usar API sin permisos de retiro.

Separar API de datos y API de ejecución.

Empezar con testnet o simulación.

No operar real sin backtesting y límites.

## Semáforo de integración

Verde:
API oficial, documentación clara, testnet o demo, permisos limitados.

Amarillo:
API parcial, datos disponibles, ejecución no clara.

Rojo:
API no oficial, credenciales inseguras, scraping, ejecución real sin control.

## Respuesta esperada

Plataforma:
Riesgo técnico:
Riesgo de cuenta:
Riesgo de seguridad:
Automatización recomendada:
Nivel de prudencia:
Siguiente paso seguro:
