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
- [ ] Clase `Equipo`
- [ ] Detección/predicción de falla
- [ ] RAG sobre PDFs técnicos
- [ ] Tool de notificación por correo
- [ ] System prompt documentado
