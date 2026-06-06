"""
agente.py — Orquestador del agente PrediMant.

Conecta las piezas en un solo flujo:
    1. Lee el histórico y PREDICE la falla (tool predecir_falla).
    2. EVALÚA la severidad de cada sensor y arma un diagnóstico.
    3. Si hay riesgo, NOTIFICA por correo (tool notificar).

En el proyecto, el "cerebro" que razona puede ser Claude Code (ver
prompts/system_agente.md y CLAUDE.md). Este script es la versión determinista
del flujo, útil como entrada ejecutable y para la demo.

Ejecuta:
    python src/agente.py             # diagnostica y, si hay riesgo, envía correo
    python src/agente.py --no-correo # solo diagnostica (no envía)
"""

import os
import sys

# Las herramientas viven en tools/ (un nivel arriba, luego tools/).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from predecir_falla import cargar_series, predecir_sensor, UMBRALES, RUTA_CSV
import notificar


def clasificar_severidad(prediccion):
    """Traduce la predicción de un sensor a un nivel de severidad."""
    if prediccion["estado"] == "EN_FALLA":
        return "CRÍTICA"
    pasos = prediccion["pasos_para_falla"]
    if pasos is None:
        return "NORMAL"
    if pasos <= 5:
        return "CRÍTICA"
    if pasos <= 20:
        return "ALERTA"
    return "VIGILAR"


# Para decidir la severidad global tomamos la "peor" de los sensores.
ORDEN_SEVERIDAD = {"NORMAL": 0, "VIGILAR": 1, "ALERTA": 2, "CRÍTICA": 3}


def diagnosticar():
    """Corre la predicción y devuelve (severidad_global, lista_de_hallazgos)."""
    series = cargar_series(RUTA_CSV)

    hallazgos = []
    severidad_global = "NORMAL"
    for sensor, puntos in series.items():
        umbral = UMBRALES.get(sensor)
        if umbral is None:
            continue
        pred = predecir_sensor(sensor, puntos, umbral)
        sev = clasificar_severidad(pred)
        hallazgos.append({"prediccion": pred, "severidad": sev})

        if ORDEN_SEVERIDAD[sev] > ORDEN_SEVERIDAD[severidad_global]:
            severidad_global = sev

    return severidad_global, hallazgos


def recomendar(severidad_global):
    """Acción recomendada según la severidad global."""
    return {
        "CRÍTICA": "Detener o inspeccionar el equipo de inmediato.",
        "ALERTA":  "Programar mantenimiento en el corto plazo.",
        "VIGILAR": "Mantener bajo observación; revisar en el próximo turno.",
        "NORMAL":  "Sin acción; operación normal.",
    }[severidad_global]


def imprimir_diagnostico(severidad_global, hallazgos):
    """Muestra el diagnóstico con el formato del system prompt."""
    print("Equipo:    MOTOR-01")
    print(f"Severidad: {severidad_global}")
    print("Hallazgos:")
    for h in hallazgos:
        p = h["prediccion"]
        if p["estado"] == "EN_FALLA":
            extra = "ya en falla"
        elif p["pasos_para_falla"] is None:
            extra = "estable"
        else:
            extra = f"falla en ~{p['pasos_para_falla']} pasos"
        print(f"  - {p['sensor']}: {p['valor_actual']} / umbral {p['umbral']} "
              f"-> {h['severidad']} ({extra})")
    print(f"Acción recomendada: {recomendar(severidad_global)}")


def main():
    severidad_global, hallazgos = diagnosticar()

    print("=== Diagnóstico del agente PrediMant ===\n")
    imprimir_diagnostico(severidad_global, hallazgos)
    print()

    # Decide si notifica: solo si hay riesgo real.
    hay_riesgo = severidad_global in ("CRÍTICA", "ALERTA")
    if "--no-correo" in sys.argv:
        print("(modo --no-correo: no se envía notificación)")
    elif hay_riesgo:
        print("Severidad alta -> enviando notificación por correo...\n")
        notificar.main()   # envía (o simula si falta .env)
    else:
        print("Sin riesgo alto -> no se envía correo.")


if __name__ == "__main__":
    main()
