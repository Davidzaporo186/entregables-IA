from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "pm25_enero_2025.csv"
DATA_SOURCE = "https://siata.gov.co/Informes_Aire/121_InformeProcuraduria_Enero2025/F-GAA-RA-82_InformeProcuraduria_Enero2025_Anexos.pdf"


def load_data(path=CSV_PATH):
    df = pd.read_csv(path)
    required = {"estacion", "municipio", "periodo", "muestras_diarias", "min_diario", "media_diaria", "max_diario", "excedencias"}
    if not required.issubset(df.columns):
        raise ValueError(f"Columnas faltantes: {required - set(df.columns)}")
    if df.estacion.duplicated().any():
        raise ValueError("La muestra histórica debe tener una sola fila por estación")
    if not ((df.min_diario <= df.media_diaria) & (df.media_diaria <= df.max_diario)).all():
        raise ValueError("Estadísticas PM2.5 inconsistentes")
    return df


def pm_category(value):
    """Band of average PM2.5 concentration, not the official ICA score."""
    if value <= 12:
        return "Buena (banda de PM2.5)"
    if value <= 37:
        return "Aceptable (banda de PM2.5)"
    if value <= 55:
        return "Dañina para grupos sensibles (banda de PM2.5)"
    if value <= 150:
        return "Dañina para la salud (banda de PM2.5)"
    if value <= 250:
        return "Muy dañina (banda de PM2.5)"
    return "Peligrosa (banda de PM2.5)"
