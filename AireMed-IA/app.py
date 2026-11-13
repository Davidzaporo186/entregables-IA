import os
import pandas as pd
import plotly.express as px
import streamlit as st
from src.data import load_data, DATA_SOURCE
from src.model import evaluate_loocv, estimate_station
from src.tools import get_pm25, estimate_monthly_mean, search_environmental_docs
from src.agent import ask_llm

st.set_page_config(page_title="AireMed IA", page_icon="🌿", layout="wide")
st.title("🌿 AireMed IA | Valle de Aburrá")
st.caption("MVP académico: PM2.5, estadísticas verificadas de enero 2025 · NO datos en tiempo real")

df = load_data()
with st.sidebar:
    st.header("Configuración")
    municipio = st.selectbox("Municipio", ["Todos"] + sorted(df.municipio.unique().tolist()))
    filtered = df if municipio == "Todos" else df[df.municipio == municipio]
    estacion = st.selectbox("Estación para el estimador", filtered.estacion.tolist())
    st.write("Período disponible: **enero 2025**")
    api_key = st.text_input("Groq API Key (opcional)", type="password", value=os.getenv("GROQ_API_KEY", ""))
    st.caption("Sin clave: estadísticas y herramientas locales funcionan; el chat LLM no.")
    st.caption("RAG activo: " + os.getenv("RAG_BACKEND", "tfidf") + " (FAISS opcional).")
    st.link_button("Ver fuente oficial SIATA", DATA_SOURCE)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Estaciones", len(filtered))
m2.metric("Media de estaciones", f"{filtered.media_diaria.mean():.1f} µg/m³")
m3.metric("Mayor media mensual", f"{filtered.media_diaria.max():.1f} µg/m³")
m4.metric("Excedencias registradas", int(filtered.excedencias.sum()))

st.subheader("1. Análisis exploratorio")
col1, col2 = st.columns(2)
with col1:
    fig = px.bar(filtered.sort_values('media_diaria', ascending=False), x='estacion', y='media_diaria', color='municipio',
                 title='PM2.5: promedio de mediciones diarias por estación (enero 2025)', labels={'media_diaria': 'µg/m³', 'estacion': 'Estación'})
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.scatter(filtered, x='min_diario', y='max_diario', color='municipio', hover_name='estacion', size='media_diaria',
                      title='Rango de mediciones diarias por estación', labels={'min_diario': 'Mínimo diario (µg/m³)', 'max_diario': 'Máximo diario (µg/m³)'})
    st.plotly_chart(fig2, use_container_width=True)
st.info("Los valores son estadísticas de enero 2025: NO son mediciones del día actual. La media de estaciones no es un ICA oficial. Las categorías ICA de 24 horas no se aplican a las medias del mes.")

st.subheader("2. Técnica clásica: KNN implementado desde cero")
metrics = evaluate_loocv(df)
c1, c2, c3 = st.columns(3)
c1.metric("MAE KNN (LOOCV)", f"{metrics['mae_knn']:.2f} µg/m³")
c2.metric("MAE línea base", f"{metrics['mae_baseline']:.2f} µg/m³")
pred = estimate_station(df, estacion)
c3.metric(f"Estimación: {estacion}", f"{pred:.2f} µg/m³")
st.caption("Cada predicción excluye la estación evaluada. Características: mínimo y máximo diario del mismo mes. Objetivo: estimar la media mensual; no es predicción de días futuros.")
comparison = pd.DataFrame({'Estación': df.estacion, 'Observado': metrics['observed'], 'KNN': metrics['predictions'], 'Línea base': metrics['baseline_predictions']})
st.plotly_chart(px.scatter(comparison, x='Observado', y='KNN', hover_name='Estación', title='Valores reales vs estimaciones fuera de muestra (µg/m³)'), use_container_width=True)
st.dataframe(comparison.round(2), use_container_width=True, hide_index=True)

st.subheader("3. Agente conversacional con RAG y herramientas")
st.markdown("**Herramientas:** `get_pm25`, `estimate_monthly_mean`, `search_environmental_docs`.")
question = st.chat_input("Ejemplo: ¿Cuál fue el PM2.5 de CEN-TRAF y qué dice la documentación?")
if 'chat' not in st.session_state:
    st.session_state.chat = []
for item in st.session_state.chat:
    with st.chat_message(item['role']):
        st.markdown(item['content'])
if question:
    st.session_state.chat.append({'role': 'user', 'content': question})
    with st.chat_message('user'):
        st.markdown(question)
    with st.chat_message('assistant'):
        if api_key:
            try:
                result = ask_llm(question, api_key, model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), history=st.session_state.chat[:-1])
                reply = result['answer']
                st.markdown(reply)
                with st.expander('Trazabilidad de herramientas'):
                    st.json(result['calls'])
            except Exception as exc:
                reply = f"Error de conexión con agente LLM: {exc}"
                st.error(reply)
        else:
            reply = "Para conversar con el agente LLM, introduce GROQ_API_KEY en la barra lateral. Mientras tanto, puedes consultar las 3 herramientas locales abajo."
            st.warning(reply)
        st.session_state.chat.append({'role': 'assistant', 'content': reply})

with st.expander("Ejecutar herramientas sin API (demostración reproducible)"):
    t1, t2, t3 = st.columns(3)
    with t1:
        if st.button('get_pm25'):
            st.json(get_pm25(estacion))
    with t2:
        if st.button('estimate_monthly_mean'):
            st.json(estimate_monthly_mean(estacion))
    with t3:
        if st.button('search_environmental_docs'):
            st.json(search_environmental_docs('contaminación PM2.5 y recomendaciones'))

st.subheader("4. Tabla y fuentes")
st.dataframe(filtered, use_container_width=True, hide_index=True)
st.download_button('Descargar CSV', filtered.to_csv(index=False).encode('utf-8-sig'), 'pm25_siata_enero_2025.csv', 'text/csv')
st.markdown(f"**Origen:** [SIATA, anexo estadístico enero 2025]({DATA_SOURCE}). **Categorías orientativas:** [Alcaldía de Medellín](https://www.medellin.gov.co/es/secretaria-medio-ambiente/calidad-del-aire/aire-en-el-valle-de-aburra/).")
st.caption("Herramienta académica descriptiva y experimental. No sustituye las publicaciones oficiales ni el asesoramiento sanitario.")
