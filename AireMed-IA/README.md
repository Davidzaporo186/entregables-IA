# AireMed IA — Proyecto final SI3003, EAFIT

MVP de **calidad del aire del Valle de Aburrá** con datos reales de SIATA de **enero de 2025**. Incluye análisis histórico, regresión KNN propia, validación LOOCV, tres herramientas, RAG y chat LLM opcional con Groq.

> **Alcance:** son datos históricos agregados de 23 estaciones; NO son mediciones actuales, un índice ICA oficial diario ni un pronóstico del siguiente día. Las medias mensuales no deben clasificarse como el ICA de 24 horas.

## 1. Requisitos

- Python **3.10, 3.11 o 3.12**, instalación de paquetes con pip; internet para instalar y para el LLM.
- Código multiplataforma, no requiere Microsoft Azure, Copilot o cuenta de Microsoft.
- El dashboard, CSV y herramientas locales se pueden ejecutar sin ninguna API key.

## 2. Instalación Windows (PowerShell)

```powershell
cd airemed_ia
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Si `py -3.11` no existe, usar `python -m venv .venv` con Python compatible. Si PowerShell bloquea la activación, ejecutar directamente `.venv\Scripts\python.exe -m pip install -r requirements.txt` y `.venv\Scripts\python.exe -m streamlit run app.py`.

## 3. Linux / Mac

```bash
cd airemed_ia
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Navegar a `http://localhost:8501`. Selecciona municipio y estación en la barra lateral; revisa las 3 gráficas y prueba `get_pm25`, `estimate_monthly_mean`, `search_environmental_docs` en el panel inferior.

## 4. LLM real (Groq)

Generar una clave en https://console.groq.com/keys . En Windows PowerShell:

```powershell
$env:GROQ_API_KEY="tu_clave_privada"
python -m streamlit run app.py
```

También puedes pegar la clave en la barra lateral de Streamlit para la sesión. No subir claves a GitHub ni a archivos compartidos. El nombre de modelo por defecto es `llama-3.3-70b-versatile`; si el proveedor lo retira, establecer `GROQ_MODEL` con uno que admita tool calling.

Prueba en el chat: `¿Cuál fue el PM2.5 promedio de CEN-TRAF en enero de 2025 y qué significan las excedencias?`. Abre la trazabilidad de llamadas para demostrar las herramientas.

## 5. RAG: modo ligero o semántico con FAISS

**Modo reproducible predeterminado:** TF-IDF + similitud coseno con corpus curado local de cuatro entradas, funciona sin descargas pesadas ni API.

**Modo de embeddings y FAISS (recomendado para la rúbrica):**

```bash
python -m pip install -r requirements-rag.txt
```

En PowerShell antes de iniciar la app: `$env:RAG_BACKEND="faiss"`. En Linux/macOS: `export RAG_BACKEND=faiss`. La primera consulta descarga el modelo multilingüe `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` de Hugging Face; **requiere internet y ocupa espacio**. Se utiliza un índice FAISS en memoria. Si no puedes descargarlo, usa el modo `tfidf` y documenta la limitación honestamente.

## 6. Pruebas y métricas

```bash
python -m pytest -q
python scripts/evaluate_agent.py --mode offline
```

`docs/resultados_offline.json` documenta la comprobación local de las 3 herramientas. No es una evaluación de las decisiones del LLM.

Para evaluar **12 preguntas con LLM real** (requiere clave, conectividad y posibles cuotas):

```bash
python scripts/evaluate_agent.py --mode llm
```

Verifica manualmente `docs/resultados_llm.json`, pues las citas por URL se comprueban solo heurísticamente.

El modelo clásico está en `src/model.py`, **KNN regresión escrito a mano con NumPy**, `k=3`, con 2 variables de entrada: mínimo diario y máximo diario registrados durante enero. Validación dejando una estación fuera (LOOCV); línea base promedio de las otras estaciones. **No hay evaluación temporal** y no se generaliza a otros meses.

## 7. Fuentes de datos, procedencia y reproducibilidad

Anexo SIATA del informe de enero 2025 (tabla PM2.5, páginas impresas 2; tablas 1.1 y 1.2):

https://siata.gov.co/Informes_Aire/121_InformeProcuraduria_Enero2025/F-GAA-RA-82_InformeProcuraduria_Enero2025_Anexos.pdf

El CSV `data/pm25_enero_2025.csv` se transcribió de ambas tablas para **12 estaciones de Medellín y 11 de otros municipios**. Columnas:

- `muestras_diarias` = CMD; `min_diario` = MIN-D; `media_diaria` = MEAN-D; `max_diario` = MAX-D; `excedencias` = NEND.
- Cada fila es estación/mes y NO una observación diaria; CSV está incluido, no depende de descarga en ejecución.
- Fuente sobre categorías ICA 24 horas: https://www.medellin.gov.co/es/secretaria-medio-ambiente/calidad-del-aire/aire-en-el-valle-de-aburra/
- SIATA sobre red de calidad del aire: https://siata.gov.co/sitio_web/index.php/calidad_aire
- Fragmentos documentales locales con citas: `data/fuentes_rag.json`. Son resúmenes curados, **no documentos oficiales completos**.

## 8. Entregables incluidos

- `app.py`, `src/`, `data/`, `tests/`, `scripts/`, `requirements.txt`, `requirements-rag.txt`.
- `docs/INFORME.pdf` (máximo 4 páginas) y `docs/INFORME.md`.
- `docs/EVALUACION_AGENTE.md`, `docs/resultados_offline.json`, `docs/DECLARACION_IA.md`.
- No incluye secretos ni resultados ficticios de Groq.

## 9. Subir a GitHub

Crea un repositorio vacío, por ejemplo `airemed-ia-eafit`, y en la carpeta del proyecto:

```bash
git init
git add .
git commit -m "Proyecto final AireMed IA"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/airemed-ia-eafit.git
git push -u origin main
```

Puedes subir el contenido desde la web de GitHub si no tienes Git instalado. `.gitignore` excluye `.env`, claves, entornos, cachés y archivos temporales. **Cada integrante debe enviar por correo al profesor el enlace al repo** con asunto `si3003-AI-grupo-nombre` antes del viernes **13 de noviembre de 2026, 6:00 p. m.**

## 10. Limitaciones y ética

- Solo 23 muestras de un único mes: muestra pequeña; variables del propio mes; KNN no es pronóstico meteorológico.
- Las métricas LOOCV son retrospectivas entre estaciones, no una prueba sobre meses nuevos.
- Los textos RAG son cuatro fragmentos editados por el equipo; consultar las URLs originales antes de afirmar regulación.
- El uso del LLM depende de API y conexión; no registrar un puntaje sin ejecutar 12 casos reales.
- Los resultados no sustituyen fuentes oficiales ni recomendaciones profesionales.
- Declarar el uso de IA y comprender el código conforme al pacto pedagógico.
