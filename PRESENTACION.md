# 🎬 Guion de Presentación · Agente PrediMant

> Demo de 5-7 minutos · UTH 2026.4 · Kenny Xavier Lanza Rios
> Cada bloque `---` es una "diapositiva". Tiempo sugerido entre paréntesis.

---

## 1. Portada (20 s)

**PrediMant** — Agente de Mantenimiento Predictivo Industrial

- Variante 2: Predictive maintenance con datos sintéticos
- Cerebro: Claude Code (sin API key externa)
- Kenny Lanza · @kennylanza1509

---

## 2. El problema (40 s)

Un motor que falla **sin aviso** = paro de producción, costos, riesgo.

**Idea:** vigilar los sensores, detectar la **tendencia de degradación** y
**avisar antes** de que el equipo falle.

> "No esperar a que se rompa: anticiparlo."

---

## 3. Arquitectura (45 s)

```
datos (sensores) -> histórico CSV -> predicción (tendencia)
                                          |
                                          v
          RAG (cita norma) <- severidad -> diagnóstico -> 📧 correo
```

- **Código Python** = las herramientas deterministas.
- **Claude Code** = el cerebro que razona y decide.
- **MCP (Model Context Protocol)** = el puente estándar: Claude llama las tools
  a través del servidor `predimant` (`mcp_server/server.py`), no por comandos sueltos.

---

## 4. POO: las clases (50 s) — *mostrar código*

- `SensorVirtual` — genera lecturas que se degradan (valor + tendencia + ruido).
- `Equipo` — agrupa sensores y da estado NORMAL / ALERTA / FALLA.
- `EventoFalla` — registra los cambios de estado (el histórico).

*Ejecutar:* celda del notebook con `SensorVirtual` y `Equipo`.

---

## 5. El histórico (30 s) — *mostrar CSV*

`python src/generar_datos.py` → `data/lecturas.csv` (180 lecturas) +
`data/eventos.csv` (cuándo cambió de estado).

> Datos tangibles sobre los que el agente razona.

---

## 6. La predicción (50 s) — *la joya*

`tools/predecir_falla.py` ajusta una **recta** (regresión lineal) a cada sensor y
estima **en cuántos pasos cruza el umbral**.

Ejemplo real de la demo:
- TEMP: ya en falla
- VIB: **fallará en ~4 pasos** ← señal temprana
- CORR: ~65 pasos

> La pendiente que "descubre" (0.408) coincide con la degradación programada (0.40). ✔

---

## 6.5 Las tools vía MCP (35 s) — *requisito clave*

Las herramientas se exponen por **MCP (Model Context Protocol)**, el estándar
con que Claude Code usa tools externas.

- En Claude Code escribe `/mcp` → aparece el servidor **predimant** conectado
  con 3 tools: `predecir_falla`, `consultar_conocimiento`, `enviar_notificacion`.

> "El agente no llama scripts sueltos: usa el protocolo estándar MCP."

---

## 7. RAG: cita la norma (45 s)

`tools/rag.py` (TF-IDF) busca en la base de conocimiento y **fundamenta** el
diagnóstico:

> "VIB en zona C según criterio tipo ISO 10816 → planificar parada."

No es una opinión: cita la fuente técnica.

---

## 8. El agente en acción (50 s) — *clímax*

`python src/agente.py`

→ Diagnóstico con severidad **CRÍTICA** + referencia técnica + **correo enviado**.

*Mostrar la bandeja de entrada con el correo recibido.* 📧

---

## 9. Cierre (30 s)

✅ 3 clases POO · ✅ tool de predicción · ✅ RAG · ✅ correo real · ✅ system prompt · ✅ servidor MCP

- Todo en **Python estándar**, sin API keys, sin librerías pesadas.
- Repo público: github.com/kennylanza1509/agente-predictivo

**Gracias.** ¿Preguntas?

---

## Comandos para la demo en vivo (chuleta)

```bash
# 0a) instalar dependencias (una sola vez):
pip install -r requirements.txt

# 0b) (opcional) acentos correctos en Windows:
set PYTHONUTF8=1

# En Claude Code, verificar el servidor MCP conectado:
#   /mcp        -> debe listar el servidor "predimant" con 3 tools

# 1) generar el histórico
python src/generar_datos.py

# 2) ver la predicción
python tools/predecir_falla.py

# 3) consultar la base técnica (RAG)
python tools/rag.py "vibracion creciente zona C"

# 4) el agente completo (diagnostica + envía correo)
python src/agente.py

# (o el cuaderno paso a paso)
#   notebooks/demo.ipynb
```
