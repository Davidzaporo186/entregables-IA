# Lista de verificación — antes de enviar el 13/11/2026 a las 6:00 p. m.

- [ ] Completar integrantes/grupo del informe PDF (regenerar PDF si cambian integrantes) y declaración de uso de IA según los aportes reales.
- [ ] Instalar Python 3.10–3.12 y `python -m pip install -r requirements.txt`.
- [ ] Ejecutar `python -m pytest -q` (esperado 12 pruebas).
- [ ] Ejecutar `python -m streamlit run app.py` y recorrer dashboard (barra, dispersión, LOOCV, filtros, CSV).
- [ ] Configurar clave de Groq y probar una pregunta compuesta, revisando trazabilidad. Si no hay clave, **no** declarar chat funcional.
- [ ] Si hay internet/recursos, `pip install -r requirements-rag.txt` y activar `RAG_BACKEND=faiss`; probar una consulta. Si no, entregar TF-IDF y consignar la limitación.
- [ ] Ejecutar con clave real `python scripts/evaluate_agent.py --mode llm`, revisar manualmente resultados y actualizar análisis de informe, **si realmente se ejecutó**.
- [ ] Subir **el contenido de `airemed_ia/`** a GitHub, sin archivos `.env` ni secretos.
- [ ] Cada integrante enviar el enlace de GitHub a jipadillab@eafit.edu.co con asunto `si3003-AI-grupo-nombre`.
- [ ] Tener lista una demostración y video alternativo de 3–4 min, recomendado si la red es inestable.

## Guion de demostración (3-4 minutos)

1. (0:00–0:30) Problema, origen SIATA, límites de enero de 2025.
2. (0:30–1:15) Filtros, barras y dispersión; mostrar tabla y la única excedencia.
3. (1:15–2:00) KNN implementado manualmente, MAE LOOCV vs línea base, estimación de una estación.
4. (2:00–3:00) Hacer pregunta al agente que combine `get_pm25` y `search_environmental_docs`. Mostrar llamadas y URLs. Sin clave: demostrar herramientas locales y declarar esa limitación.
5. (3:00–3:30) 12 tests + evaluación de 12 preguntas si Groq fue ejecutado. Limitaciones y declaración de IA.
