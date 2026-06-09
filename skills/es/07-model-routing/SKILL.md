---
name: model-routing
description: Decide cuándo usar modelos locales rápidos y cuándo reservar modelos cloud para análisis profundo, evitando desperdiciar límites gratuitos.
---

# Model Routing

Usa esta skill para administrar el uso inteligente de modelos locales y cloud.

## Objetivo

Optimizar velocidad, privacidad y uso de límites cloud.

## Modelos recomendados

Modelo rápido local:

llama3.2:latest

Uso:
- respuestas breves
- sesión demo
- checklist
- veredicto rápido
- análisis simple
- preguntas frecuentes

Modelo local profundo:

llama3.1:8b

Uso:
- análisis técnico más completo
- lectura de mercado
- explicación de escenarios
- revisión de una operación específica

Modelo técnico:

qwen2.5-coder:7b

Uso:
- código
- revisión técnica
- automatizaciones
- scripts
- estructura de proyectos

Modelo cloud profundo:

kimi-k2.5:cloud

Uso:
- análisis complejo
- revisión semanal
- bitácoras extensas
- comparación de estrategias
- análisis de capturas difíciles
- diseño de reglas
- auditoría de decisiones
- tareas donde la calidad importe más que la velocidad

## Reglas de uso

No usar modelo cloud para respuestas simples.

No usar modelo cloud para saludos.

No usar modelo cloud para preguntas que pueda resolver un modelo local.

No usar modelo cloud para datos sensibles, credenciales o información privada.

Usar modelo cloud solo si el usuario lo solicita o si el análisis requiere mayor profundidad.

Antes de usar cloud, avisar brevemente:

"Para esto conviene usar modelo cloud por profundidad."

## Política de ahorro

Si la pregunta es corta, usar local.

Si la respuesta esperada es menor a 10 líneas, usar local.

Si hay análisis de más de 20 operaciones, usar cloud.

Si hay varias capturas o contexto complejo, sugerir cloud.

Si el usuario dice "exprime el análisis", usar cloud.

Si el usuario dice "rápido", usar local.

## Frase de decisión

Cuando corresponda, decir:

"Ing. Gilbert, esto lo puedo resolver local rápido."

o

"Ing. Gilbert, para este caso sí conviene usar el modelo cloud porque requiere más profundidad."
