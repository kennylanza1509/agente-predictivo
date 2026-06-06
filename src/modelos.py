"""
modelos.py — Clases POO del agente de mantenimiento predictivo.

Variante 2 del proyecto: Predictive maintenance con datos sintéticos.

Contiene:
  - SensorVirtual: genera lecturas sintéticas de UN sensor que se degrada.
  - Equipo: agrupa VARIOS sensores y calcula el estado general del activo.

Usa solo la librería estándar de Python (random), así que corre sin instalar nada.
"""

import random


class SensorVirtual:
    """Un sensor simulado que produce lecturas a lo largo del tiempo.

    La idea de "mantenimiento predictivo": un equipo sano da lecturas
    estables alrededor de un valor normal; un equipo que se está dañando
    muestra una TENDENCIA (las lecturas suben de a poco) más RUIDO aleatorio.

    Atributos:
        tag:          identificador del sensor (ej. "TEMP-MOTOR-01").
        unidad:       unidad de medida (ej. "°C", "mm/s", "A").
        valor_base:   valor normal cuando el equipo está sano.
        ruido:        cuánto varían las lecturas al azar (desviación).
        degradacion:  cuánto sube el valor en cada paso de tiempo
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
        """Genera y devuelve UNA lectura nueva del sensor (un diccionario)."""
        # Componente de degradación: crece con el tiempo si degradacion > 0.
        deriva = self.degradacion * self._paso
        # Componente de ruido: un valor aleatorio centrado en 0.
        ruido_aleatorio = random.gauss(0, self.ruido)

        valor = round(self.valor_base + deriva + ruido_aleatorio, 2)

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


class Equipo:
    """Un activo industrial (motor, bomba, ...) con varios sensores.

    Agrupa objetos `SensorVirtual` y, en cada momento, los lee a todos
    y calcula un ESTADO GENERAL del equipo:
        - "FALLA"   : al menos un sensor superó su umbral.
        - "ALERTA"  : ningún sensor en falla, pero alguno está cerca
                      (>= 90 % de su umbral). Señal temprana = predictivo.
        - "NORMAL"  : todos los sensores en rango sano.

    Atributos:
        nombre:   identificador del equipo (ej. "MOTOR-01").
        tipo:     tipo de activo (ej. "motor", "bomba").
        sensores: lista de SensorVirtual que monitorean el equipo.
    """

    # A partir de qué fracción del umbral consideramos "ALERTA" temprana.
    FRACCION_ALERTA = 0.9

    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo = tipo
        self.sensores = []  # empieza sin sensores; se agregan con agregar_sensor()

    def agregar_sensor(self, sensor):
        """Suma un SensorVirtual al equipo."""
        self.sensores.append(sensor)

    def _evaluar(self, lecturas):
        """Decide el estado general a partir de las lecturas de este instante."""
        nivel = "NORMAL"
        # Recorremos en paralelo cada sensor con su lectura.
        for sensor, lectura in zip(self.sensores, lecturas):
            if lectura["en_falla"]:
                return "FALLA"  # con una sola falla, el equipo ya está en falla
            # ¿Cerca del umbral? -> alerta temprana (lo predictivo).
            if sensor.umbral_falla is not None:
                if lectura["valor"] >= self.FRACCION_ALERTA * sensor.umbral_falla:
                    nivel = "ALERTA"
        return nivel

    def monitorear(self):
        """Lee TODOS los sensores una vez y devuelve el estado del equipo.

        Devuelve un diccionario:
            {"equipo": ..., "estado": "NORMAL|ALERTA|FALLA", "lecturas": [...]}
        """
        lecturas = [s.leer() for s in self.sensores]
        return {
            "equipo": self.nombre,
            "estado": self._evaluar(lecturas),
            "lecturas": lecturas,
        }


class EventoFalla:
    """Registra un cambio de estado del equipo (un "evento" de mantenimiento).

    Cada vez que el equipo pasa de un nivel a otro (NORMAL -> ALERTA -> FALLA)
    guardamos un EventoFalla. Esto es el "historial" que luego el agente
    analiza para anticipar y recomendar mantenimiento.

    Atributos:
        paso:        instante (paso de tiempo) en que ocurrió el evento.
        equipo:      nombre del equipo afectado.
        nivel:       nuevo estado ("ALERTA" o "FALLA").
        descripcion: texto legible de lo que pasó.
    """

    def __init__(self, paso, equipo, nivel, descripcion):
        self.paso = paso
        self.equipo = equipo
        self.nivel = nivel
        self.descripcion = descripcion

    def como_fila(self):
        """Devuelve el evento como diccionario, listo para escribir en CSV."""
        return {
            "paso": self.paso,
            "equipo": self.equipo,
            "nivel": self.nivel,
            "descripcion": self.descripcion,
        }

    def __str__(self):
        """Texto legible (lo que se ve al hacer print de un EventoFalla)."""
        return f"[paso {self.paso}] {self.equipo}: {self.nivel} — {self.descripcion}"


# --- Demo: esto solo corre si ejecutas este archivo directamente ---
# (python src/modelos.py). Si lo importas desde otro archivo, no se ejecuta.
if __name__ == "__main__":
    print("=== Demo: Equipo MOTOR-01 con 3 sensores ===\n")

    # Creamos el equipo y le agregamos 3 sensores que se degradan a distinto ritmo.
    motor = Equipo(nombre="MOTOR-01", tipo="motor")
    motor.agregar_sensor(SensorVirtual("TEMP", "°C",   70.0, ruido=0.8, degradacion=0.40, umbral_falla=90.0))
    motor.agregar_sensor(SensorVirtual("VIB",  "mm/s",  2.0, ruido=0.15, degradacion=0.08, umbral_falla=7.0))
    motor.agregar_sensor(SensorVirtual("CORR", "A",    12.0, ruido=0.30, degradacion=0.05, umbral_falla=18.0))

    # Encabezado de la tabla.
    print(f"{'paso':>4} | {'TEMP':>8} | {'VIB':>8} | {'CORR':>8} | estado")
    print("-" * 52)

    for paso in range(1, 41):
        reporte = motor.monitorear()
        # Sacamos el valor de cada sensor en el orden en que se agregaron.
        temp, vib, corr = reporte["lecturas"]
        print(f"{paso:>4} | "
              f"{temp['valor']:>6.2f} {temp['unidad']:<1} | "
              f"{vib['valor']:>6.2f} {vib['unidad']:<2} | "
              f"{corr['valor']:>6.2f} {corr['unidad']:<1} | "
              f"{reporte['estado']}")
