"""
generar_datos.py — Genera un histórico sintético y lo guarda en CSV.

Corre el monitoreo de un equipo durante N pasos y produce dos archivos en data/:
  - data/lecturas.csv : una fila por cada (paso, sensor) con su valor y estado.
  - data/eventos.csv  : una fila por cada CAMBIO de estado del equipo (los eventos).

Ejecuta:  python src/generar_datos.py
"""

import csv
import os

from modelos import Equipo, SensorVirtual, EventoFalla

# Cuántos pasos de tiempo simular.
N_PASOS = 60

# Carpeta data/ (está un nivel arriba de src/, donde vive este archivo).
CARPETA_DATOS = os.path.join(os.path.dirname(__file__), "..", "data")


def construir_motor():
    """Arma el equipo MOTOR-01 con sus 3 sensores."""
    motor = Equipo(nombre="MOTOR-01", tipo="motor")
    motor.agregar_sensor(SensorVirtual("TEMP", "°C",   70.0, ruido=0.8,  degradacion=0.40, umbral_falla=90.0))
    motor.agregar_sensor(SensorVirtual("VIB",  "mm/s",  2.0, ruido=0.15, degradacion=0.08, umbral_falla=7.0))
    motor.agregar_sensor(SensorVirtual("CORR", "A",    12.0, ruido=0.30, degradacion=0.05, umbral_falla=18.0))
    return motor


def main():
    # Nos aseguramos de que la carpeta data/ exista.
    os.makedirs(CARPETA_DATOS, exist_ok=True)

    motor = construir_motor()

    filas_lecturas = []   # acumula todas las lecturas (para lecturas.csv)
    eventos = []          # acumula los EventoFalla (para eventos.csv)
    estado_anterior = "NORMAL"

    for paso in range(1, N_PASOS + 1):
        reporte = motor.monitorear()
        estado = reporte["estado"]

        # Guardamos cada lectura de cada sensor en este paso.
        for lectura in reporte["lecturas"]:
            filas_lecturas.append({
                "paso": paso,
                "equipo": motor.nombre,
                "sensor": lectura["tag"],
                "valor": lectura["valor"],
                "unidad": lectura["unidad"],
                "en_falla": lectura["en_falla"],
                "estado_equipo": estado,
            })

        # Si el estado general CAMBIÓ respecto al paso anterior, es un evento.
        if estado != estado_anterior:
            evento = EventoFalla(
                paso=paso,
                equipo=motor.nombre,
                nivel=estado,
                descripcion=f"el equipo pasó de {estado_anterior} a {estado}",
            )
            eventos.append(evento)
            estado_anterior = estado

    # --- Escribir lecturas.csv ---
    ruta_lecturas = os.path.join(CARPETA_DATOS, "lecturas.csv")
    with open(ruta_lecturas, "w", newline="", encoding="utf-8") as f:
        columnas = ["paso", "equipo", "sensor", "valor", "unidad", "en_falla", "estado_equipo"]
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas_lecturas)

    # --- Escribir eventos.csv ---
    ruta_eventos = os.path.join(CARPETA_DATOS, "eventos.csv")
    with open(ruta_eventos, "w", newline="", encoding="utf-8") as f:
        columnas = ["paso", "equipo", "nivel", "descripcion"]
        escritor = csv.DictWriter(f, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(evento.como_fila() for evento in eventos)

    # --- Resumen en pantalla ---
    print(f"✓ {len(filas_lecturas)} lecturas guardadas en: data/lecturas.csv")
    print(f"✓ {len(eventos)} eventos guardados en:  data/eventos.csv\n")
    print("Eventos detectados:")
    if eventos:
        for evento in eventos:
            print(f"  {evento}")
    else:
        print("  (ninguno — el equipo se mantuvo NORMAL)")


if __name__ == "__main__":
    main()
