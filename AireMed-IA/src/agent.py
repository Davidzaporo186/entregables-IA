
"""
AireMed IA - Agente conversacional con Groq.
Proyecto Final de Inteligencia Artificial - EAFIT.

Incluye:
- Agente LLM.
- Llamadas a herramientas.
- Recuperacion documental RAG.
- Trazabilidad de consultas.
- Control de rondas y errores.
"""

import json
import requests

from .tools import FUNCTIONS, SCHEMAS


API_URL = "https://api.groq.com/openai/v1/chat/completions"

DEFAULT_MODEL = "openai/gpt-oss-120b"


SYSTEM_PROMPT = """
Eres AireMed IA, un agente academico ambiental en espanol.

Trabajas exclusivamente con datos historicos de PM2.5
del Valle de Aburra correspondientes a enero de 2025.

REGLAS:

1. No tienes datos de contaminacion en tiempo real.
2. No puedes predecir la contaminacion de manana.
3. Para consultar valores de estaciones utiliza get_pm25.
4. Para realizar estimaciones utiliza estimate_monthly_mean.
5. Para informacion ambiental utiliza search_environmental_docs.
6. Si una pregunta requiere varias herramientas, utiliza las necesarias.
7. No inventes datos, documentos ni fuentes.
8. Incluye las URL de las fuentes cuando esten disponibles.
9. No interpretes un promedio mensual como categoria ICA de 24 horas.
10. Las estimaciones KNN son retrospectivas, no pronosticos.
11. Si falta informacion, indicalo claramente.
12. Responde en espanol de forma clara y comprensible.
"""


def consultar_groq(payload, api_key):
    """
    Envia una solicitud a Groq y devuelve el mensaje generado.
    """

    try:
        response = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=35
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]

    except requests.HTTPError as error:
        detalle = getattr(
            getattr(error, "response", None),
            "text",
            ""
        )

        raise RuntimeError(
            f"Error HTTP de Groq: {error}. "
            f"Detalle: {detalle[:700]}"
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"Error de conexion con Groq: {error}"
        ) from error

    except (KeyError, ValueError, TypeError) as error:
        raise RuntimeError(
            "Groq devolvio una respuesta con formato incorrecto."
        ) from error


def ejecutar_herramienta(name, args, cache):
    """
    Ejecuta una herramienta autorizada.
    Evita repetir consultas identicas utilizando cache.
    """

    try:
        if name not in FUNCTIONS:
            return {
                "error": f"Herramienta no autorizada: {name}"
            }

        argumentos = json.loads(args or "{}")

        if not isinstance(argumentos, dict):
            return {
                "error": "Los argumentos deben ser un objeto JSON."
            }

        cache_key = (
            name,
            json.dumps(
                argumentos,
                sort_keys=True,
                ensure_ascii=False
            )
        )

        if cache_key in cache:
            return cache[cache_key]

        resultado = FUNCTIONS[name](**argumentos)

        cache[cache_key] = resultado

        return resultado

    except (
        ValueError,
        TypeError,
        KeyError,
        RuntimeError
    ) as error:
        return {
            "error": str(error)
        }


def generar_respuesta_final(question, api_key, model, tool_log):
    """
    Genera una respuesta final cuando se agotan las rondas.
    No ejecuta nuevas herramientas.
    """

    resultados = [
        {
            "herramienta": item["name"],
            "resultado": item["result"]
        }
        for item in tool_log
    ]

    contexto = json.dumps(
        resultados,
        ensure_ascii=False,
        default=str
    )[:15000]

    mensajes_finales = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\nResponde con los resultados disponibles. "
                "No solicites herramientas adicionales. "
                "No inventes datos y cita las fuentes."
            )
        },
        {
            "role": "user",
            "content": (
                f"Pregunta original: {question}\n\n"
                f"Resultados obtenidos:\n{contexto}\n\n"
                "Genera una respuesta final en español."
            )
        }
    ]

    payload = {
        "model": model,
        "messages": mensajes_finales,
        "tool_choice": "none",
        "temperature": 0.1
    }

    try:
        try:
            respuesta = consultar_groq(payload, api_key)

        except RuntimeError as error:
            # Si Groq rechaza tool_choice="none",
            # se intenta nuevamente sin ese parametro.
            if "400" not in str(error):
                raise

            payload.pop("tool_choice", None)

            respuesta = consultar_groq(payload, api_key)

        contenido = respuesta.get("content")

        if isinstance(contenido, str) and contenido.strip():
            return {
                "answer": contenido,
                "calls": tool_log
            }

        return {
            "answer": (
                "El modelo no devolvió una respuesta final. "
                "Consulta la trazabilidad de herramientas "
                "para revisar los resultados obtenidos."
            ),
            "calls": tool_log
        }

    except Exception as error:
        return {
            "answer": (
                "No se pudo generar la respuesta final. "
                "Consulta la trazabilidad de herramientas. "
                f"Detalle: {error}"
            ),
            "calls": tool_log
        }


def ask_llm(
    question,
    api_key,
    model=DEFAULT_MODEL,
    max_rounds=4,
    history=None
):
    """
    Ejecuta el ciclo del agente LLM.

    1. Recibe una pregunta.
    2. Consulta el modelo de Groq.
    3. Detecta llamadas a herramientas.
    4. Ejecuta las herramientas necesarias.
    5. Guarda los resultados y la trazabilidad.
    6. Genera una respuesta final.
    """

    if not api_key:
        raise ValueError(
            "Configura GROQ_API_KEY para activar el agente LLM."
        )

    if not question or not question.strip():
        raise ValueError(
            "La pregunta no puede estar vacia."
        )

    if max_rounds < 1:
        raise ValueError(
            "max_rounds debe ser mayor o igual a 1."
        )

    history = (history or [])[-6:]

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    for item in history:
        if (
            item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
        ):
            messages.append({
                "role": item["role"],
                "content": item["content"][:2500]
            })

    messages.append({
        "role": "user",
        "content": question[:4000]
    })

    tool_log = []
    cache = {}

    for ronda in range(max_rounds):

        payload = {
            "model": model,
            "messages": messages,
            "tools": SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.1
        }

        respuesta = consultar_groq(
            payload,
            api_key
        )

        calls = respuesta.get("tool_calls") or []

        if not calls:
            contenido = respuesta.get("content")

            if (
                isinstance(contenido, str)
                and contenido.strip()
            ):
                return {
                    "answer": contenido,
                    "calls": tool_log
                }

            return generar_respuesta_final(
                question,
                api_key,
                model,
                tool_log
            )

        messages.append(respuesta)

        for call in calls:
            function = call.get("function") or {}

            name = function.get("name", "")

            args = function.get(
                "arguments",
                "{}"
            )

            resultado = ejecutar_herramienta(
                name,
                args,
                cache
            )

            tool_log.append({
                "name": name,
                "args": args,
                "result": resultado
            })

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(
                    resultado,
                    ensure_ascii=False,
                    default=str
                )
            })

    # Se alcanzo el limite de rondas.
    # Responder con los resultados ya disponibles.

    return generar_respuesta_final(
        question,
        api_key,
        model,
        tool_log
    )
