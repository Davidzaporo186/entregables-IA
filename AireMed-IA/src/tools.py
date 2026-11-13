"""Two quantitative tools plus retrieval, callable by an LLM."""
from .data import load_data, pm_category
from .model import estimate_station, evaluate_loocv
from .rag import search_docs


def get_pm25(estacion):
    df = load_data()
    rows = df.loc[df.estacion.str.upper() == estacion.upper()]
    if rows.empty:
        return {"error": f"Estación desconocida. Usa alguna de: {', '.join(df.estacion)}"}
    row = rows.iloc[0]
    return {"estacion": row.estacion, "municipio": row.municipio, "periodo": row.periodo,
            "promedio_mensual_pm25": float(row.media_diaria), "minimo_diario": float(row.min_diario),
            "maximo_diario": float(row.max_diario), "excedencias": int(row.excedencias),
            "nota_interpretacion": "No convertir la media mensual en categoría ICA de 24 horas.",
            "advertencia": "Dato histórico agregado de enero 2025; no corresponde al día de hoy.",
            "fuente": "https://siata.gov.co/Informes_Aire/121_InformeProcuraduria_Enero2025/F-GAA-RA-82_InformeProcuraduria_Enero2025_Anexos.pdf"}


def estimate_monthly_mean(estacion):
    df = load_data()
    try:
        pred = estimate_station(df, estacion)
        observed = float(df.loc[df.estacion == estacion, 'media_diaria'].iloc[0])
        return {"estacion": estacion, "periodo": "2025-01", "estimacion_media_mensual_pm25": round(pred, 2),
                "media_observada_para_comparacion": observed,
                "mae_validacion_cruzada": round(evaluate_loocv(df)['mae_knn'], 2),
                "advertencia": "Estimación retrospectiva fuera de muestra basada en extremos del mismo mes, NO pronóstico de mañana."}
    except (ValueError, IndexError) as exc:
        return {"error": str(exc)}


def search_environmental_docs(pregunta):
    return {"documentos": search_docs(pregunta), "nota": "Corpus local curado; enlaces a fuentes originales."}


FUNCTIONS = {
    "get_pm25": get_pm25,
    "estimate_monthly_mean": estimate_monthly_mean,
    "search_environmental_docs": search_environmental_docs,
}

SCHEMAS = [
    {"type": "function", "function": {"name": "get_pm25", "description": "Consulta el promedio real de PM2.5 de una estación para enero 2025 (no datos actuales).", "parameters": {"type": "object", "properties": {"estacion": {"type": "string", "description": "Código de estación por ejemplo CEN-TRAF"}}, "required": ["estacion"]}}},
    {"type": "function", "function": {"name": "estimate_monthly_mean", "description": "Estima retrospectivamente la media mensual de una estación con un KNN propio (no pronostica mañana).", "parameters": {"type": "object", "properties": {"estacion": {"type": "string"}}, "required": ["estacion"]}}},
    {"type": "function", "function": {"name": "search_environmental_docs", "description": "Busca y devuelve documentos ambientales con enlaces de fuentes", "parameters": {"type": "object", "properties": {"pregunta": {"type": "string"}}, "required": ["pregunta"]}}}
]
