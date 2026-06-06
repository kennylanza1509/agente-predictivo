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
│   ├── modelos.py   ← clases POO (SensorVirtual, Equipo, EventoFalla)
│   ├── agente.py    ← orquestador del agente
│   └── __init__.py
├── tools/           ← herramientas: predicción, RAG, correo
├── mcp_server/
│   └── server.py    ← servidor MCP que expone las tools a Claude Code
├── prompts/         ← system prompt del agente
├── data/            ← datos generados + base de conocimiento (RAG)
├── .mcp.json        ← config del servidor MCP (Claude Code se conecta solo)
├── requirements.txt
├── .env.example
└── .gitignore
```

## Instalación

```bash
pip install -r requirements.txt
```

La única dependencia real es `mcp` (el SDK del Model Context Protocol). El resto
del proyecto usa solo la librería estándar de Python.

## Conectar las herramientas vía MCP (Model Context Protocol)

El agente expone sus herramientas a Claude Code mediante un **servidor MCP**, el
protocolo estándar para que un LLM use herramientas externas.

- Definición del servidor: [`mcp_server/server.py`](mcp_server/server.py) — 3 tools:
  `predecir_falla`, `consultar_conocimiento` (RAG) y `enviar_notificacion` (correo).
- Configuración: [`.mcp.json`](.mcp.json). Al abrir Claude Code (`claude`) en esta
  carpeta, el servidor `predimant` se conecta automáticamente y las tools quedan
  disponibles por MCP. Verifícalo con el comando `/mcp`.

```bash
# Probar el servidor MCP manualmente (sin Claude Code):
python mcp_server/server.py        # queda a la espera por stdio (Ctrl+C para salir)
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
- [x] System prompt documentado (`prompts/system_agente.md` + `CLAUDE.md`)
- [x] Orquestador del agente (`src/agente.py`)
- [x] RAG sobre base de conocimiento técnica (`tools/rag.py`, TF-IDF)
- [x] Servidor **MCP** que expone las tools a Claude Code (`mcp_server/server.py`, `.mcp.json`)

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

## Ejecutar el agente completo

```bash
python src/agente.py             # diagnostica y notifica si hay riesgo
python src/agente.py --no-correo # solo diagnostica
```

El "cerebro" que razona puede ser Claude Code: abre `claude` en esta carpeta y
seguirá las instrucciones de `CLAUDE.md` + `prompts/system_agente.md`.

## Consultar la base de conocimiento (RAG)

```bash
python tools/rag.py "vibracion creciente zona C"
```

Busca por TF-IDF en `data/conocimiento/*.md` (criterios de vibración, temperatura
y corriente) y devuelve el fragmento más relevante. El agente lo usa para citar
la norma técnica en su diagnóstico.
