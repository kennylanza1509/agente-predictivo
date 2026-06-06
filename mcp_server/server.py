"""
server.py — Servidor MCP del agente PrediMant.

Expone las herramientas del proyecto a través del **Model Context Protocol
(MCP)**, el estándar abierto con el que Claude Code (el cerebro del agente) se
comunica con herramientas externas.

En vez de invocar los scripts por Bash, ahora Claude Code se conecta a este
servidor (ver `.mcp.json` en la raíz) y llama las tools por el protocolo MCP.
Reutiliza la lógica que ya existe en `tools/` — no duplica nada.

Tools expuestas:
  - predecir_falla         -> tendencia y pasos-para-falla de cada sensor
  - consultar_conocimiento -> RAG sobre la base técnica (TF-IDF)
  - enviar_notificacion    -> manda (o simula) el correo de alerta

Transporte: stdio (el que usa Claude Code para servidores MCP locales).

Ejecuta (lo lanza Claude Code automáticamente vía .mcp.json):
    python mcp_server/server.py
"""

import os
import sys

# Las herramientas viven en ../tools y se importan entre sí por nombre simple
# (notificar.py hace `from predecir_falla import ...`), así que añadimos esa
# carpeta al path para poder reutilizarlas tal cual.
TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "tools")
sys.path.insert(0, TOOLS_DIR)

from predecir_falla import cargar_series, predecir_sensor, UMBRALES, RUTA_CSV
from rag import MotorRAG
import notificar as notificar_mod

from mcp.server.fastmcp import FastMCP

# Nombre del servidor MCP (así aparece el agente ante Claude Code).
mcp = FastMCP("predimant")


@mcp.tool()
def predecir_falla() -> dict:
    """Predice la falla de cada sensor del MOTOR-01 según su tendencia.

    Lee el histórico (data/lecturas.csv), ajusta una regresión lineal a cada
    sensor y estima en cuántos pasos cruzará su umbral. Devuelve la lista de
    predicciones con valor actual, umbral, pendiente, estado y pasos-para-falla.
    """
    series = cargar_series(RUTA_CSV)
    resultados = []
    for sensor, puntos in series.items():
        umbral = UMBRALES.get(sensor)
        if umbral is None:
            continue
        resultados.append(predecir_sensor(sensor, puntos, umbral))
    return {"predicciones": resultados}


@mcp.tool()
def consultar_conocimiento(consulta: str, k: int = 1) -> dict:
    """Busca en la base de conocimiento técnico (RAG · TF-IDF).

    Dada una consulta (p. ej. "vibracion creciente zona C"), devuelve los `k`
    fragmentos más relevantes de data/conocimiento/ para fundamentar y CITAR
    el diagnóstico con una fuente técnica.
    """
    motor = MotorRAG()
    resultados = motor.consultar(consulta, k=k)
    # Redondeamos el score para una salida más limpia.
    for r in resultados:
        r["score"] = round(r["score"], 3)
    return {"consulta": consulta, "resultados": resultados}


@mcp.tool()
def enviar_notificacion(simular: bool = True) -> dict:
    """Envía por correo el reporte de mantenimiento predictivo.

    Construye el cuerpo a partir de la predicción y lo manda por SMTP (Gmail),
    leyendo las credenciales de .env. Con `simular=True` (por defecto) NO envía:
    devuelve el asunto y cuerpo para revisión. Pon `simular=False` para enviar
    de verdad.
    """
    notificar_mod.cargar_env(notificar_mod.RUTA_ENV)
    asunto, cuerpo = notificar_mod.construir_cuerpo()

    if simular:
        return {"enviado": False, "modo": "simulado",
                "asunto": asunto, "cuerpo": cuerpo}

    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    destino = os.environ.get("EMAIL_DESTINO")
    if not (remitente and password and destino):
        return {"enviado": False, "error": "faltan credenciales en .env",
                "asunto": asunto}

    notificar_mod.enviar_correo(asunto, cuerpo, remitente, password, destino)
    return {"enviado": True, "destino": destino, "asunto": asunto}


if __name__ == "__main__":
    # Transporte stdio: Claude Code habla con el servidor por entrada/salida
    # estándar (no abre puertos de red).
    mcp.run()
