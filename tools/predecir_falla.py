"""
predecir_falla.py — Herramienta (tool) de predicción de falla.

Lee el histórico de lecturas (data/lecturas.csv), calcula la TENDENCIA de cada
sensor mediante una regresión lineal simple y estima en cuántos pasos cruzará
su umbral de falla.

Esta es una "tool" pensada para que el agente (Claude Code) la invoque por Bash:

    python tools/predecir_falla.py

Imprime un reporte legible y también un bloque JSON (para que el agente lo lea
de forma estructurada).
"""

import os
import csv
import json

# Ruta al histórico (un nivel arriba de tools/, dentro de data/).
RUTA_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "lecturas.csv")

# Umbrales de cada sensor (mismos que usamos al generar los datos).
# En un proyecto más grande esto vendría del propio Equipo; aquí lo dejamos
# explícito para que la tool sea autónoma.
UMBRALES = {
    "TEMP": 90.0,
    "VIB": 7.0,
    "CORR": 18.0,
}


def cargar_series(ruta_csv):
    """Lee el CSV y agrupa los valores por sensor.

    Devuelve un diccionario:  {"TEMP": [(paso, valor), ...], "VIB": [...], ...}
    """
    series = {}
    with open(ruta_csv, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            sensor = fila["sensor"]
            paso = int(fila["paso"])
            valor = float(fila["valor"])
            series.setdefault(sensor, []).append((paso, valor))
    return series


def regresion_lineal(puntos):
    """Calcula la recta y = pendiente*x + interseccion que mejor ajusta.

    `puntos` es una lista de pares (x, y). Devuelve (pendiente, interseccion).
    Fórmula estándar de mínimos cuadrados (solo aritmética básica).
    """
    n = len(puntos)
    suma_x = sum(x for x, _ in puntos)
    suma_y = sum(y for _, y in puntos)
    suma_xy = sum(x * y for x, y in puntos)
    suma_xx = sum(x * x for x, _ in puntos)

    denominador = n * suma_xx - suma_x * suma_x
    if denominador == 0:
        return 0.0, suma_y / n  # recta horizontal (sin tendencia)

    pendiente = (n * suma_xy - suma_x * suma_y) / denominador
    interseccion = (suma_y - pendiente * suma_x) / n
    return pendiente, interseccion


def predecir_sensor(sensor, puntos, umbral):
    """Estima en cuántos pasos el sensor cruzará su umbral."""
    pendiente, interseccion = regresion_lineal(puntos)
    paso_actual = puntos[-1][0]
    valor_actual = puntos[-1][1]

    # Si ya superó el umbral, ya está en falla.
    if valor_actual >= umbral:
        estado = "EN_FALLA"
        pasos_para_falla = 0
    elif pendiente <= 0:
        # No hay tendencia creciente: no se prevé falla.
        estado = "ESTABLE"
        pasos_para_falla = None
    else:
        # ¿En qué paso x la recta alcanza el umbral?  umbral = pendiente*x + b
        paso_cruce = (umbral - interseccion) / pendiente
        pasos_para_falla = max(0, round(paso_cruce - paso_actual))
        estado = "DEGRADANDO"

    return {
        "sensor": sensor,
        "valor_actual": round(valor_actual, 2),
        "umbral": umbral,
        "pendiente_por_paso": round(pendiente, 4),
        "estado": estado,
        "pasos_para_falla": pasos_para_falla,
    }


def main():
    series = cargar_series(RUTA_CSV)

    resultados = []
    for sensor, puntos in series.items():
        umbral = UMBRALES.get(sensor)
        if umbral is None:
            continue
        resultados.append(predecir_sensor(sensor, puntos, umbral))

    # --- Reporte legible para humanos ---
    print("=== Predicción de falla (basada en tendencia) ===\n")
    for r in resultados:
        if r["estado"] == "EN_FALLA":
            msg = "⛔ YA EN FALLA (superó el umbral)"
        elif r["estado"] == "ESTABLE":
            msg = "✅ estable, sin tendencia a fallar"
        else:
            msg = f"⚠️  fallará en ~{r['pasos_para_falla']} pasos"
        print(f"{r['sensor']:>5} | actual {r['valor_actual']:>6.2f} / umbral {r['umbral']:>5} "
              f"| +{r['pendiente_por_paso']:.3f}/paso | {msg}")

    # --- Bloque JSON estructurado (para que el agente lo consuma) ---
    print("\n--- JSON ---")
    print(json.dumps({"predicciones": resultados}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
