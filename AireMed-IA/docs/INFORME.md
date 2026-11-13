# AireMed IA — Informe final

**Asignatura:** SI3003 – Inteligencia Artificial  
**Universidad:** EAFIT  
**Fecha:** 13 de noviembre de 2026  
**Integrante y responsable del proyecto:** David Zapata (trabajo individual)

## 1. Problema y objetivo

La contaminación por material particulado fino (PM2.5) es relevante para el Valle de Aburrá. Aunque existen mediciones públicas, interpretar cifras y documentos técnicos no siempre es sencillo. Por eso desarrollé **AireMed IA**, un prototipo académico para consultar y comparar estadísticas históricas de estaciones, estimar promedios mensuales con una técnica clásica y hacer preguntas a un agente conversacional respaldado por fuentes ambientales. **No ofrece mediciones en tiempo real ni pronósticos para el día siguiente.**

## 2. Datos y fuentes

Usé el anexo estadístico del **Informe Procuraduría de SIATA, enero de 2025**, sección PM2.5, tablas 1.1 y 1.2. El conjunto incluye **23 estaciones** (12 en Medellín y 11 en otros municipios) y resúmenes CMD (cantidad de muestras diarias), MIN-D, MEAN-D, MAX-D y NEND (excedencias). Las concentraciones están en µg/m³. Cada fila del CSV resume un mes para una estación, **no** corresponde a una serie diaria ni a un dato actual.

La aplicación lee `data/pm25_enero_2025.csv`, lo que facilita reproducir la demostración sin consultar una API externa. Para contexto documental se emplearon textos curados a partir de SIATA y la Alcaldía de Medellín.

**Fuentes:**
- SIATA: https://siata.gov.co/Informes_Aire/121_InformeProcuraduria_Enero2025/F-GAA-RA-82_InformeProcuraduria_Enero2025_Anexos.pdf
- Alcaldía de Medellín: https://www.medellin.gov.co/es/secretaria-medio-ambiente/calidad-del-aire/aire-en-el-valle-de-aburra/

## 3. Técnica de IA clásica y evaluación

Implementé un **KNN de regresión con NumPy**, sin usar un estimador KNN ya entrenado por una librería. Se eligió `k = 3`, con distancia euclidiana y normalización usando únicamente las estaciones del conjunto de entrenamiento. Como variables de entrada se utilizaron MIN-D y MAX-D del mes; la salida fue la media mensual MEAN-D.

Para medir el error se aplicó **leave-one-out (LOOCV)**: se excluyó cada estación, se calculó su estimación con las otras 22 y se repitió el procedimiento para las 23 estaciones. Se comparó contra una línea base que predice el promedio de las estaciones de entrenamiento.

| Métrica | Resultado |
|---|---:|
| MAE KNN | 1,6072 µg/m³ |
| MAE línea base | 3,0893 µg/m³ |
| Reducción relativa del MAE | aproximadamente 47,97 % |

El KNN obtuvo un error menor que la línea base en este conjunto. Sin embargo, el experimento es **retrospectivo y espacial**, no una validación temporal: los valores mínimo y máximo pertenecen al mismo mes que la variable estimada. El número de registros también es limitado.

## 4. Agente LLM y recuperación documental (RAG)

El agente usa Groq y el modelo configurado `openai/gpt-oss-120b`. Implementé un ciclo de llamadas a herramientas, registro de trazabilidad, límite de rondas y manejo de errores. El sistema puede invocar:

- `get_pm25(estacion)`: obtiene las estadísticas históricas de una estación.
- `estimate_monthly_mean(estacion)`: consulta el estimador retrospectivo KNN.
- `search_environmental_docs(pregunta)`: recupera fragmentos documentales con sus fuentes.

Para RAG hay un corpus local reducido de fragmentos resumidos y enlazados de fuentes ambientales. El proyecto permite recuperación por **TF-IDF** y, opcionalmente, por **embeddings con FAISS**. Se comprobó en la ejecución local que la herramienta devuelve resultados con `backend: faiss`. Estos fragmentos no equivalen al contenido completo de los documentos oficiales y pueden no ser suficientes para todas las preguntas.

## 5. Dashboard

Construí la interfaz con **Streamlit y Plotly**. Se puede filtrar por municipio y estación, comparar promedios mensuales, visualizar mínimos y máximos, ver estimaciones frente a valores observados y descargar una tabla CSV. El chat incluye una sección de trazabilidad y también existe una demostración de las herramientas locales que no necesita clave API.

Las medias mensuales **no deben clasificarse con las categorías de ICA basadas en promedios de 24 horas**.

## 6. Pruebas y resultados del agente

Ejecuté la batería de pruebas automáticas con **13 de 13 pruebas aprobadas**. También evalué el agente real con **12 preguntas** que cubren consultas numéricas, estimaciones, recuperación documental, preguntas combinadas y límites del sistema.

| Indicador de la evaluación final | Resultado |
|---|---:|
| Preguntas ejecutadas | 12/12 |
| Casos con herramientas requeridas | 11/12 |
| Porcentaje de selección de herramientas | 91,7 % |
| Errores de API en esa ejecución | 0 |

El **91,7 %** corresponde a la presencia de las herramientas requeridas según el evaluador. No es una medida de la veracidad general de todas las respuestas ni garantiza que cada cita sea pertinente; las citas y posibles herramientas adicionales requieren revisión manual. Los resultados se guardaron en `docs/resultados_llm.json`.

## 7. Limitaciones y conclusión

Las limitaciones principales son el período de datos (enero de 2025), el tamaño de la muestra, el corpus documental resumido y la dependencia de conectividad y cuotas de Groq para el chat. El sistema es un **MVP académico**, no un servicio oficial de vigilancia ambiental ni una herramienta de diagnóstico o recomendación médica.

El proyecto permitió aplicar una técnica clásica implementada manualmente y combinarla con un agente LLM que consulta datos y documentos. Una mejora futura sería ampliar la serie histórica, evaluar por períodos temporales e incorporar documentos ambientales más completos.

**Reproducibilidad:** consultar `README.md` para instalar `requirements.txt`, activar opcionalmente `requirements-rag.txt`, ejecutar `pytest`, abrir Streamlit y evaluar el agente. El uso de IA generativa se explica en `docs/DECLARACION_IA.md`.
