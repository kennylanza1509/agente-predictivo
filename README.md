# Agente de Mantenimiento Predictivo

Proyecto final · **Programación · Maestría en Automatización Industrial · UTH 2026.4**
Autor: Kenny Xavier Lanza Rios ([@kennylanza1509](https://github.com/kennylanza1509))
Variante **2 · Predictive maintenance con datos sintéticos**.

Un agente que recibe datos sintéticos de sensores industriales, razona (con Claude
Code como cerebro) para **anticipar una falla** antes de que ocurra, consulta
documentación técnica vía RAG y **notifica por correo**.

## Estructura

```
agente-predictivo/
├── src/
│   ├── modelos.py   ← clases POO (SensorVirtual, ...)
│   └── __init__.py
├── data/            ← datos generados / PDFs del RAG
├── tests/           ← pruebas
├── requirements.txt
├── .env.example
└── .gitignore
```

## Cómo correr la demo del sensor

```bash
python src/modelos.py
```

Genera una serie de lecturas de temperatura que se degradan hasta la falla.

## Estado

- [x] Clase `SensorVirtual` (genera datos sintéticos)
- [x] Clase `Equipo` (agrupa sensores, estado NORMAL/ALERTA/FALLA)
- [x] Clase `EventoFalla` (registra cambios de estado)
- [x] Histórico en CSV (`src/generar_datos.py` → `data/lecturas.csv`, `data/eventos.csv`)
- [x] Herramienta de predicción de falla (`tools/predecir_falla.py`)
- [x] Tool de notificación por correo (`tools/notificar.py`, smtplib + .env)
- [ ] RAG sobre PDFs técnicos
- [ ] System prompt documentado

## Generar el histórico de datos

```bash
python src/generar_datos.py
```

Crea `data/lecturas.csv` (todas las lecturas) y `data/eventos.csv` (los cambios de estado).

## Predecir la falla

```bash
python tools/predecir_falla.py
```

Lee `data/lecturas.csv`, calcula la tendencia de cada sensor (regresión lineal) y
estima en cuántos pasos cruzará su umbral. Imprime un reporte y un bloque JSON.

## Notificar por correo

```bash
python tools/notificar.py            # envía (o simula si falta .env)
python tools/notificar.py --simular  # solo muestra el correo, no envía
```

Requiere un `.env` (copia de `.env.example`) con `EMAIL_REMITENTE`, `EMAIL_PASSWORD`
(App Password de Gmail) y `EMAIL_DESTINO`. Sin credenciales reales corre en modo simulación.
