"""
notificar.py — Herramienta (tool) de canal de salida: envía la predicción por correo.

- Reutiliza `predecir_falla` para armar el cuerpo del mensaje.
- Lee las credenciales de un archivo .env (NUNCA van escritas en el código).
- Usa smtplib (librería estándar) con Gmail.

Modo simulación: si faltan credenciales en .env, NO falla; muestra el correo
en pantalla para que puedas probar el flujo. Cuando configures .env, envía de verdad.

Ejecuta:
    python tools/notificar.py            # envía (o simula si faltan credenciales)
    python tools/notificar.py --simular  # fuerza simulación (no envía nunca)
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText

# Reutilizamos la lógica de predicción (predecir_falla.py está en esta misma carpeta).
from predecir_falla import cargar_series, predecir_sensor, UMBRALES, RUTA_CSV

# Configuración del servidor SMTP de Gmail.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# Ruta al archivo .env (en la raíz del proyecto, un nivel arriba de tools/).
RUTA_ENV = os.path.join(os.path.dirname(__file__), "..", ".env")


def cargar_env(ruta):
    """Lee un archivo .env (líneas CLAVE=valor) y las mete en os.environ.

    Ignora líneas vacías y comentarios (#). Es un mini-cargador para no
    depender de librerías externas.
    """
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip())


# Unidades de cada sensor (para mostrarlas en el reporte, más claras que el número solo).
UNIDADES = {"TEMP": "°C", "VIB": "mm/s", "CORR": "A"}

# Orden de severidad, de mayor a menor (para ordenar y para elegir la severidad global).
_RANGO = {"CRÍTICO": 0, "ALERTA": 1, "VIGILAR": 2, "NORMAL": 3}


def _clasificar(r):
    """Traduce el estado/pasos de un sensor a una severidad legible."""
    if r["estado"] == "EN_FALLA":
        return "CRÍTICO"
    if r["estado"] == "ESTABLE":
        return "NORMAL"
    pasos = r.get("pasos_para_falla")
    if pasos is not None and pasos <= 5:
        return "ALERTA"
    return "VIGILAR"


def _acciones(predicciones):
    """Construye acciones concretas y consistentes con lo que dicen los sensores."""
    sev = {p["sensor"]: p["severidad"] for p in predicciones}
    criticos_alerta = {"CRÍTICO", "ALERTA"}
    acciones = []

    temp_mal = sev.get("TEMP") in criticos_alerta
    vib_mal = sev.get("VIB") in criticos_alerta
    corr_mal = sev.get("CORR") in criticos_alerta

    # La firma TEMP + VIB en ascenso apunta a rodamiento / lubricación.
    if temp_mal and vib_mal:
        acciones.append(
            "Inspeccionar y lubricar el rodamiento: temperatura y vibración suben "
            "juntas, firma típica de rodamiento dañado o lubricación deficiente."
        )
    elif temp_mal:
        acciones.append(
            "Revisar la refrigeración: ventilación, suciedad en aletas y carga del motor."
        )
    elif vib_mal:
        acciones.append(
            "Verificar alineación, balanceo y anclaje; revisar el rodamiento."
        )

    if corr_mal:
        acciones.append(
            "Comprobar la carga del proceso: la corriente sube, posible sobrecarga."
        )

    if not acciones:
        acciones.append("Mantener monitoreo rutinario; sin acción inmediata requerida.")
    else:
        # Cierre coherente con la urgencia general.
        if "CRÍTICO" in sev.values():
            acciones.append("Programar PARADA CONTROLADA antes de que la falla se agrave.")
        else:
            acciones.append("Programar la inspección en la próxima ventana de mantenimiento.")
    return acciones


def construir_cuerpo():
    """Arma el texto del correo con el resultado de la predicción.

    El reporte se ordena por urgencia, marca la severidad de cada sensor y
    cierra con acciones concretas coherentes con el diagnóstico.
    """
    series = cargar_series(RUTA_CSV)

    predicciones = []
    for sensor, puntos in series.items():
        umbral = UMBRALES.get(sensor)
        if umbral is None:
            continue
        r = predecir_sensor(sensor, puntos, umbral)
        r["severidad"] = _clasificar(r)
        predicciones.append(r)

    # Ordena de mayor a menor severidad; a igual severidad, el más cercano a fallar.
    predicciones.sort(key=lambda r: (_RANGO[r["severidad"]],
                                     r.get("pasos_para_falla") or 0))

    severidad_global = min((p["severidad"] for p in predicciones),
                           key=lambda s: _RANGO[s], default="NORMAL")

    lineas = [
        "Reporte de mantenimiento predictivo",
        "",
        "Equipo:    MOTOR-01",
        f"Severidad: {severidad_global}",
        "",
        "Estado por sensor (ordenado por urgencia)",
        "-" * 52,
    ]

    for r in predicciones:
        unidad = UNIDADES.get(r["sensor"], "")
        if r["severidad"] == "CRÍTICO":
            detalle = "ya superó el umbral"
        elif r["estado"] == "ESTABLE":
            detalle = "estable, sin tendencia a fallar"
        else:
            detalle = f"fallaría en ~{r['pasos_para_falla']} pasos"
        lineas.append(
            f"[{r['severidad']:<8}] {r['sensor']:<5} "
            f"{r['valor_actual']:>6} {unidad:<4} "
            f"(umbral {r['umbral']} {unidad}) — {detalle}"
        )

    lineas += ["", "Acciones recomendadas", "-" * 52]
    for i, accion in enumerate(_acciones(predicciones), start=1):
        lineas.append(f"{i}. {accion}")

    lineas += ["", "— Agente PrediMant · mantenimiento predictivo (UTH 2026.4)"]

    etiqueta = {
        "CRÍTICO": "[MOTOR-01] CRÍTICO — acción inmediata requerida",
        "ALERTA": "[MOTOR-01] ALERTA de mantenimiento predictivo",
        "VIGILAR": "[MOTOR-01] Aviso: sensores a vigilar",
        "NORMAL": "[MOTOR-01] Estado normal",
    }
    return etiqueta[severidad_global], "\n".join(lineas)


def enviar_correo(asunto, cuerpo, remitente, password, destino):
    """Envía el correo por SMTP (Gmail). Lanza excepción si algo falla."""
    mensaje = MIMEText(cuerpo, _charset="utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = remitente
    mensaje["To"] = destino

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.starttls()              # cifra la conexión
        servidor.login(remitente, password)
        servidor.send_message(mensaje)


def main():
    cargar_env(RUTA_ENV)

    asunto, cuerpo = construir_cuerpo()

    remitente = os.environ.get("EMAIL_REMITENTE")
    password = os.environ.get("EMAIL_PASSWORD")
    destino = os.environ.get("EMAIL_DESTINO")

    forzar_simulacion = "--simular" in sys.argv
    faltan_credenciales = not (remitente and password and destino)

    # Plantillas de ejemplo del .env.example -> tratarlas como "no configurado".
    valores_ejemplo = {"tu_correo@gmail.com", "tu_app_password", "destino@ejemplo.com"}
    son_ejemplo = remitente in valores_ejemplo or destino in valores_ejemplo

    if forzar_simulacion or faltan_credenciales or son_ejemplo:
        motivo = "forzada (--simular)" if forzar_simulacion else "faltan credenciales reales en .env"
        print(f"=== MODO SIMULACIÓN ({motivo}) — el correo NO se envía ===\n")
        print(f"Para:    {destino or '(sin EMAIL_DESTINO)'}")
        print(f"Asunto:  {asunto}")
        print("-" * 50)
        print(cuerpo)
        print("-" * 50)
        print("\nℹ️  Configura .env (copia de .env.example) para enviar de verdad.")
        return

    try:
        enviar_correo(asunto, cuerpo, remitente, password, destino)
        print(f"✓ Correo enviado a {destino}")
        print(f"  Asunto: {asunto}")
    except Exception as e:
        print(f"✗ No se pudo enviar el correo: {e}")
        print("  Revisa EMAIL_REMITENTE / EMAIL_PASSWORD (App Password de Gmail) / EMAIL_DESTINO en .env")


if __name__ == "__main__":
    main()
