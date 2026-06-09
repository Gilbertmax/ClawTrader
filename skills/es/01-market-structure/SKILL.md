---
name: market-structure
description: Analiza estructura de mercado, tendencia, soportes, resistencias, rupturas, retrocesos, liquidez y price action para validar operaciones.

> 📚 Referencia: `documentacion/TRADING_STRATEGIES_COMPLETE.md` contiene el manual completo de estrategias, patrones de velas, indicadores y análisis multi-timeframe. Consultarlo para profundizar en cualquier tema.
---

# Market Structure

Usa esta skill cuando el usuario comparta una captura, activo, gráfico, temporalidad o posible entrada y necesite lectura técnica del mercado.

## Objetivo

Determinar si el mercado tiene estructura suficiente para justificar una operación o si la entrada es forzada.

## Prioridades

1. La estructura manda sobre el indicador
2. El contexto manda sobre la vela actual
3. La tendencia mayor manda sobre la señal menor
4. El precio manda sobre la opinión
5. El score del scanner es filtro, no excusa para forzar entrada

## Lectura de tendencia

Identificar:

- **Máximos y mínimos crecientes** (HH + HL = tendencia alcista)
- **Máximos y mínimos decrecientes** (LH + LL = tendencia bajista)
- **Rangos laterales** (el precio oscila entre S/R claro)
- **Rupturas fallidas** (falso breakout con mecha larga y cierre dentro)
- **Cambio de estructura** (último HL roto = posible cambio de tendencia)
- **Impulso y retroceso** (fase de momentum vs fase de corrección)
- **Zona de acumulación** (rango prolongado antes de breakout alcista)
- **Zona de distribución** (rango prolongado antes de breakout bajista)

## Multi-Timeframe Analysis obligatorio

Para CADA análisis:
1. **Mirar 4H/1D:** ¿Cuál es la tendencia dominante?
2. **Mirar 1H:** ¿Hay setup en dirección de la tendencia?
3. **Mirar 15m:** ¿Hay patrón de entrada claro?

**Regla:** Si el TF alto y el TF bajo se contradicen, NO operar.
Si el patrón no es claro al 100% en 15m, esperar.

## Lectura de zonas

Marcar mentalmente:

Soporte inmediato.

Resistencia inmediata.

Zona de rechazo.

Zona de ruptura.

Zona de liquidez.

Zona de manipulación probable.

Zona donde la entrada ya llega tarde.

## Evaluación de entrada

Una entrada de compra mejora si:

El precio respeta soporte.

Hay mínimos crecientes.

Hay ruptura y retesteo.

Hay rechazo claro de zona baja.

La vela de confirmación no está sobreextendida.

El stop lógico no queda demasiado lejos.

Una entrada de venta mejora si:

El precio rechaza resistencia.

Hay máximos decrecientes.

Hay ruptura bajista y retesteo.

Hay rechazo claro de zona alta.

La vela de confirmación no está sobreextendida.

El stop lógico no queda demasiado lejos.

## Señales débiles

Considera débil una operación si:

Está en medio del rango.

No tiene zona clara.

La entrada persigue una vela grande.

La invalidación está indefinida.

El mercado acaba de tener movimiento brusco.

La temporalidad baja contradice la temporalidad mayor.

El precio está cerca de soporte para venta.

El precio está cerca de resistencia para compra.

## Clasificación de contexto

Tendencial limpio.

Tendencial agotado.

Rango operable.

Rango sucio.

Alta volatilidad.

Baja volatilidad.

Manipulación probable.

Entrada tardía.

Sin operación.

## Confirmaciones útiles

Ruptura con cierre.

Retesteo.

Rechazo con mecha.

Volumen creciente si está disponible.

Confluencia con EMA.

Divergencia solo como apoyo, no como señal principal.

## Respuesta esperada

Contexto estructural:
Zonas clave:
Dirección favorecida:
Riesgo técnico:
Entrada limpia:
Entrada tardía:
Invalidación técnica:
Conclusión:
