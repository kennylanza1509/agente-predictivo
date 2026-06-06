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


def construir_cuerpo():
    """Arma el texto del correo con el resultado de la predicción."""
    series = cargar_series(RUTA_CSV)

    lineas = ["Reporte de mantenimiento predictivo — MOTOR-01", ""]
    hay_alerta = False

    for sensor, puntos in series.items():
        umbral = UMBRALES.get(sensor)
        if umbral is None:
            continue
        r = predecir_sensor(sensor, puntos, umbral)

        if r["estado"] == "EN_FALLA":
            detalle = "YA EN FALLA (superó el umbral)"
            hay_alerta = True
        elif r["estado"] == "ESTABLE":
            detalle = "estable, sin tendencia a fallar"
        else:
            detalle = f"fallará en ~{r['pasos_para_falla']} pasos"
            hay_alerta = True

        lineas.append(
            f"- {sensor}: actual {r['valor_actual']} / umbral {r['umbral']} "
            f"-> {detalle}"
        )

    lineas.append("")
    lineas.append("Acción sugerida: programar inspección de los sensores en alerta.")

    asunto = "[MOTOR-01] ALERTA de mantenimiento predictivo" if hay_alerta \
        else "[MOTOR-01] Estado normal"
    return asunto, "\n".join(lineas)


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
