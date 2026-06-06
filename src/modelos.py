"""
modelos.py — Clases POO del agente de mantenimiento predictivo.

Variante 2 del proyecto: Predictive maintenance con datos sintéticos.
Por ahora solo contiene `SensorVirtual`, la clase que GENERA lecturas
sintéticas de un sensor industrial (temperatura, vibración, presión, etc.)
que se van degradando poco a poco hacia una falla.

Usa solo la librería estándar de Python (random, math), así que corre
sin instalar nada extra.
"""

import random
import math


class SensorVirtual:
    """Un sensor simulado que produce lecturas a lo largo del tiempo.

    La idea de "mantenimiento predictivo": un equipo sano da lecturas
    estables alrededor de un valor normal; un equipo que se está dañando
    muestra una TENDENCIA (las lecturas suben de a poco) más RUIDO aleatorio.
    Con esos datos sintéticos luego entrenaremos/razonaremos para anticipar
    la falla antes de que ocurra.

    Atributos:
        tag:        nombre/identificador del sensor (ej. "TEMP-MOTOR-01").
        unidad:     unidad de medida (ej. "°C", "mm/s", "bar").
        valor_base: valor normal cuando el equipo está sano.
        ruido:      cuánto varían las lecturas al azar (desviación).
        degradacion: cuánto sube el valor en cada paso de tiempo
                     (0 = equipo sano y estable; >0 = se está dañando).
        umbral_falla: valor a partir del cual se considera FALLA.
    """

    def __init__(self, tag, unidad, valor_base, ruido=0.5,
                 degradacion=0.0, umbral_falla=None):
        self.tag = tag
        self.unidad = unidad
        self.valor_base = valor_base
        self.ruido = ruido
        self.degradacion = degradacion
        self.umbral_falla = umbral_falla
        # Lleva la cuenta de cuántas lecturas se han generado (el "tiempo").
        self._paso = 0

    def leer(self):
        """Genera y devuelve UNA lectura nueva del sensor.

        Fórmula: valor_base + (degradación acumulada) + (ruido aleatorio).
        Devuelve un diccionario con los datos de la medición.
        """
        # Componente de degradación: crece con el tiempo si degradacion > 0.
        deriva = self.degradacion * self._paso
        # Componente de ruido: un valor aleatorio centrado en 0.
        ruido_aleatorio = random.gauss(0, self.ruido)

        valor = self.valor_base + deriva + ruido_aleatorio
        valor = round(valor, 2)

        # ¿Está en falla? Solo si definimos un umbral.
        en_falla = self.umbral_falla is not None and valor >= self.umbral_falla

        self._paso += 1  # avanza el "reloj" del sensor

        return {
            "tag": self.tag,
            "paso": self._paso,
            "valor": valor,
            "unidad": self.unidad,
            "en_falla": en_falla,
        }

    def generar_serie(self, n):
        """Genera una lista de `n` lecturas consecutivas (una serie temporal)."""
        return [self.leer() for _ in range(n)]


# --- Demo: esto solo corre si ejecutas este archivo directamente ---
# (python src/modelos.py). Si lo importas desde otro archivo, no se ejecuta.
if __name__ == "__main__":
    print("=== Demo: SensorVirtual de temperatura de un motor ===\n")

    # Un sensor de temperatura que arranca sano (~70 °C) pero se va
    # degradando 0.4 °C por lectura. Falla si pasa de 90 °C.
    sensor = SensorVirtual(
        tag="TEMP-MOTOR-01",
        unidad="°C",
        valor_base=70.0,
        ruido=0.8,
        degradacion=0.4,
        umbral_falla=90.0,
    )

    for lectura in sensor.generar_serie(60):
        # Barra visual simple para "ver" la tendencia en la terminal.
        barra = "#" * int((lectura["valor"] - 60))
        alerta = "  <-- ¡FALLA!" if lectura["en_falla"] else ""
        print(f"paso {lectura['paso']:>2} | "
              f"{lectura['valor']:>6.2f} {lectura['unidad']} | {barra}{alerta}")
