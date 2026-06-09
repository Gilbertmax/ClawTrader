---
name: trading-project-dev
description: Desarrollo del proyecto local trading-agent usando Python, Ollama y arquitectura modular.
---

# Trading Project Developer

Ruta principal:

/home/gilbertoglez/AI/trading-agent

Python:
3.11

## Objetivo

Construir un agente financiero inteligente para:

- análisis técnico
- señales
- backtesting
- paper trading
- bitácora
- evaluación de estrategias
- simulación

## Reglas

Antes de modificar código:

1. Revisar estructura completa.
2. No romper lógica existente.
3. Mantener código funcional.
4. Explicar riesgos.
5. No conectar dinero real.
6. Priorizar demo y simulación.
7. Mantener arquitectura modular.

## Arquitectura

app/brokers
app/core
app/strategies
app/services
app/storage
app/ai
app/config
data
logs
backtests
docs

## Librerías principales

pandas
numpy
python-binance
ta
fastapi
sqlalchemy
plotly
requests
