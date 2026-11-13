# Evaluación del agente — protocolo reproducible

Se definieron 12 preguntas fijas en `scripts/evaluate_agent.py` que abarcan consultas de estaciones, estimaciones, recuperación de documentos, preguntas compuestas, límites temporales y errores.

## Dos evaluaciones distintas

1. **Sin API, realizada automáticamente:** `python scripts/evaluate_agent.py --mode offline`. Prueba que las tres herramientas funcionan localmente. **No evalúa la selección por un LLM**.
2. **Con Groq, por ejecutar con clave válida:** configurar `GROQ_API_KEY` y correr `python scripts/evaluate_agent.py --mode llm`. Guarda `docs/resultados_llm.json` con las 12 respuestas, herramientas llamadas, coincidencia exacta con herramientas esperadas y detección automática preliminar de citas URL.

No reportar una tasa de aciertos del agente hasta ejecutar el modo `llm`. La detección de URLs no evalúa relevancia semántica y necesita revisión humana.

## Casos (en el mismo orden del script)

| # | Prueba | Herramientas esperadas |
|---|---|---|
| 1 | Promedio CEN-TRAF | get_pm25 |
| 2 | Media MED-SELE | get_pm25 |
| 3 | Excedencias MED-VILL | get_pm25 |
| 4 | Estimación ITA-CJUS | estimate_monthly_mean |
| 5 | Estimación y observado MED-ALTA | estimate_monthly_mean |
| 6 | Qué significa PM2.5 | search_environmental_docs |
| 7 | Qué monitorea SIATA | search_environmental_docs |
| 8 | Bandas PM2.5 24 h | search_environmental_docs |
| 9 | CEN-TRAF y excedencia | get_pm25 + search_environmental_docs |
| 10 | Medición actual en la vivienda | ninguna; expresar limitación |
| 11 | Predicción para mañana | ninguna; expresar limitación |
| 12 | Estación ABC-XYZ | get_pm25; error controlado |

## Análisis mínimo para el informe

- Proporción de casos que seleccionaron todas y solo las herramientas esperadas.
- Proporción de respuestas que aportan URL pertinente cuando corresponde (revisión manual).
- Errores de API, llamadas innecesarias, respuestas sin citas, alucinaciones temporales.
- En ausencia de clave API reportar **no evaluado**, no 100 %.
