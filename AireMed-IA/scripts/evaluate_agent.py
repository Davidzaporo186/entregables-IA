
"""
Evaluacion reproducible del proyecto AireMed IA - EAFIT.

Modo offline:
Comprueba las herramientas locales.

Modo llm:
Evalua 12 preguntas reales utilizando Groq.

Incluye:
- Pausas entre consultas.
- Reintentos ante errores 429.
- Evaluacion de herramientas.
- Revision preliminar de citas.
- Registro de errores.
- Exportacion de resultados JSON.
"""

import argparse
import json
import os
import sys
import time

from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent import ask_llm
from src.tools import FUNCTIONS


# PREGUNTAS DE EVALUACION

CASES = [
    (
        "¿Cuál fue el PM2.5 promedio de CEN-TRAF en enero 2025?",
        ["get_pm25"],
        ["SIATA"]
    ),
    (
        "¿Cuál fue la media de MED-SELE?",
        ["get_pm25"],
        ["SIATA"]
    ),
    (
        "¿Cuántas excedencias tuvo MED-VILL?",
        ["get_pm25"],
        ["SIATA"]
    ),
    (
        "¿Cómo estimas la media de ITA-CJUS?",
        ["estimate_monthly_mean"],
        []
    ),
    (
        "Estima MED-ALTA y compárala con el promedio real",
        ["estimate_monthly_mean", "get_pm25"],
        ["SIATA"]
    ),
    (
        "¿Qué significa PM2.5 según la red de monitoreo?",
        ["search_environmental_docs"],
        ["SIATA"]
    ),
    (
        "¿Qué monitorea SIATA y por qué?",
        ["search_environmental_docs"],
        ["SIATA"]
    ),
    (
        "¿Cuáles son las bandas de PM2.5 de 24 horas?",
        ["search_environmental_docs"],
        ["Alcaldía"]
    ),
    (
        "Consulta CEN-TRAF y explica qué es una excedencia",
        ["get_pm25", "search_environmental_docs"],
        ["SIATA"]
    ),
    (
        "¿Qué concentración hay ahora en mi casa?",
        [],
        []
    ),
    (
        "¿Cuánto PM2.5 habrá mañana?",
        [],
        []
    ),
    (
        "¿Cuánto midió la estación inexistente ABC-XYZ?",
        ["get_pm25"],
        []
    )
]


# CONFIGURACION

PAUSA_ENTRE_PREGUNTAS = 30
MAX_REINTENTOS = 4
ESPERA_REINTENTO = 20


def evaluar_offline():
    """
    Comprueba las herramientas sin llamar al LLM.
    """

    ejemplos = {
        "get_pm25": {
            "estacion": "CEN-TRAF"
        },
        "estimate_monthly_mean": {
            "estacion": "ITA-CJUS"
        },
        "search_environmental_docs": {
            "pregunta": "PM2.5 monitoreo ambiental"
        }
    }

    resultados = {}

    for nombre, argumentos in ejemplos.items():

        try:
            respuesta = FUNCTIONS[nombre](**argumentos)

            correcto = (
                bool(respuesta)
                and isinstance(respuesta, dict)
                and "error" not in respuesta
            )

            resultados[nombre] = {
                "ok": correcto,
                "resultado": respuesta
            }

        except Exception as error:

            resultados[nombre] = {
                "ok": False,
                "error": str(error)
            }

    return {
        "modo": "offline_solo_herramientas",
        "fecha": datetime.now(timezone.utc).isoformat(),
        "resultados": resultados,
        "advertencia": (
            "Esta evaluacion no prueba las decisiones "
            "ni las respuestas del modelo LLM."
        )
    }


def consultar_con_reintentos(pregunta, api_key):
    """
    Ejecuta el agente con reintentos ante errores
    temporales de limite de solicitudes de Groq.
    """

    for intento in range(MAX_REINTENTOS):

        try:
            return ask_llm(pregunta, api_key)

        except Exception as error:

            mensaje = str(error).lower()

            limite = (
                "429" in mensaje
                or "rate limit" in mensaje
                or "too many requests" in mensaje
            )

            if not limite:
                raise

            if intento == MAX_REINTENTOS - 1:
                raise

            espera = ESPERA_REINTENTO * (intento + 1)

            print(
                f"Limite de Groq alcanzado. "
                f"Reintento {intento + 1}/{MAX_REINTENTOS - 1}. "
                f"Pausa: {espera} segundos.",
                flush=True
            )

            time.sleep(espera)


def obtener_fuentes(llamadas):
    """
    Obtiene las URL entregadas por las herramientas.
    """

    fuentes = []

    for llamada in llamadas:

        resultado = llamada.get("result", {})

        if not isinstance(resultado, dict):
            continue

        fuente = resultado.get("fuente")

        if isinstance(fuente, str) and fuente:
            fuentes.append(fuente)

        documentos = resultado.get("documentos", [])

        if isinstance(documentos, list):

            for documento in documentos:

                if not isinstance(documento, dict):
                    continue

                url = documento.get("url")

                if isinstance(url, str) and url:
                    fuentes.append(url)

    return list(dict.fromkeys(fuentes))


def verificar_citas(respuesta, fuentes):
    """
    Comprobacion preliminar de citas.

    Detecta si la respuesta contiene URLs obtenidas
    de las herramientas, pero no verifica por si sola
    si el contenido esta correctamente fundamentado.
    """

    if not respuesta or not fuentes:
        return False

    for fuente in fuentes:

        if fuente in respuesta:
            return True

    return False


def evaluar_llm(api_key):
    """
    Evalua las 12 preguntas utilizando el agente real.
    """

    registros = []

    total = len(CASES)

    for indice, caso in enumerate(CASES, start=1):

        pregunta, esperadas, referencias = caso

        print(
            f"\nEvaluando pregunta {indice}/{total}",
            flush=True
        )
        print(pregunta, flush=True)

        try:

            salida = consultar_con_reintentos(
                pregunta,
                api_key
            )

            llamadas = salida.get("calls", [])
            respuesta = salida.get("answer", "")

            usadas = sorted({
                llamada.get("name", "")
                for llamada in llamadas
                if llamada.get("name")
            })

            faltantes = sorted(
                set(esperadas) - set(usadas)
            )

            adicionales = sorted(
                set(usadas) - set(esperadas)
            )

            # Se comprueba que todas las herramientas
            # requeridas hayan sido utilizadas.
            herramientas_correctas = not faltantes

            fuentes = obtener_fuentes(llamadas)

            cita_detectada = verificar_citas(
                respuesta,
                fuentes
            )

            registro = {
                "numero": indice,
                "pregunta": pregunta,
                "esperadas": esperadas,
                "usadas": usadas,
                "faltantes": faltantes,
                "adicionales": adicionales,
                "herramientas_correctas": herramientas_correctas,
                "respuesta": respuesta,
                "fuentes_recuperadas": fuentes,
                "cita_url_detectada": cita_detectada,
                "referencias_esperadas": referencias,
                "revision_citas": "Requiere revision humana",
                "estado": (
                    "correcto"
                    if herramientas_correctas
                    else "incorrecto"
                ),
                "error": None
            }

            print(
                "Herramientas:",
                usadas,
                flush=True
            )

            print(
                "Resultado:",
                registro["estado"],
                flush=True
            )

        except Exception as error:

            registro = {
                "numero": indice,
                "pregunta": pregunta,
                "esperadas": esperadas,
                "usadas": [],
                "faltantes": esperadas,
                "adicionales": [],
                "herramientas_correctas": False,
                "respuesta": "",
                "fuentes_recuperadas": [],
                "cita_url_detectada": False,
                "referencias_esperadas": referencias,
                "revision_citas": "No evaluable",
                "estado": "error",
                "error": str(error)
            }

            print(
                "Error:",
                str(error)[:350],
                flush=True
            )

        registros.append(registro)

        # La pausa ayuda a reducir los errores 429.
        if indice < total:

            print(
                f"Pausa de {PAUSA_ENTRE_PREGUNTAS} "
                "segundos antes de continuar...",
                flush=True
            )

            time.sleep(PAUSA_ENTRE_PREGUNTAS)

    # CALCULO DE METRICAS

    evaluados = [
        registro for registro in registros
        if registro["estado"] != "error"
    ]

    correctos = sum(
        registro["herramientas_correctas"]
        for registro in evaluados
    )

    errores = sum(
        registro["estado"] == "error"
        for registro in registros
    )

    total_evaluados = len(evaluados)

    exactitud = (
        correctos / total_evaluados
        if total_evaluados > 0
        else None
    )

    cobertura = total_evaluados / total

    citas_detectadas = sum(
        registro["cita_url_detectada"]
        for registro in evaluados
    )

    return {
        "mode": "llm_real",
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "total_preguntas": total,
        "preguntas_evaluadas": total_evaluados,
        "errores_api": errores,
        "herramientas_correctas": correctos,
        "accuracy_tools": exactitud,
        "cobertura_evaluacion": cobertura,
        "respuestas_con_url_recuperada": citas_detectadas,
        "criterio": (
            "Se verifica que se hayan utilizado todas las "
            "herramientas requeridas. Las herramientas "
            "adicionales se registran para revision humana."
        ),
        "nota": (
            "La deteccion de citas es automatica y "
            "requiere revision humana de pertinencia. "
            "Los errores de API no se consideran "
            "respuestas incorrectas del agente."
        ),
        "cases": registros
    }


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["offline", "llm"],
        default="offline"
    )

    parser.add_argument(
        "--output",
        default=None
    )

    args = parser.parse_args()

    if args.mode == "llm":

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            parser.error(
                "Configura GROQ_API_KEY antes "
                "de ejecutar la evaluacion LLM."
            )

        resultado = evaluar_llm(api_key)

        nombre_archivo = "resultados_llm.json"

    else:

        resultado = evaluar_offline()

        nombre_archivo = "resultados_offline.json"

    ruta = Path(
        args.output
        or ROOT / "docs" / nombre_archivo
    )

    ruta.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ruta.write_text(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("\nEvaluacion finalizada.")
    print("Guardado:", ruta)

    if args.mode == "llm":

        print(
            "Preguntas evaluadas:",
            resultado["preguntas_evaluadas"]
        )

        print(
            "Errores de API:",
            resultado["errores_api"]
        )

        print(
            "Herramientas correctas:",
            resultado["herramientas_correctas"]
        )

        if resultado["accuracy_tools"] is not None:

            print(
                "Exactitud:",
                f"{resultado['accuracy_tools'] * 100:.1f}%"
            )

        else:

            print(
                "Exactitud: no calculable"
            )

        print(
            "Cobertura:",
            f"{resultado['cobertura_evaluacion'] * 100:.1f}%"
        )

    else:

        for nombre, datos in resultado["resultados"].items():

            print(
                nombre,
                "OK" if datos["ok"] else "ERROR"
            )


if __name__ == "__main__":
    main()
