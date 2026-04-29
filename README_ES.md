# PRAXIS Universal Kit

**Kit de observabilidad para entender qué le está haciendo la IA a tu trabajo, tu confianza y tus decisiones**

PRAXIS instrumenta flujos reales de trabajo humano-IA para hacer visibles patrones que normalmente permanecen ocultos: rework, calibración de confianza, degradación entre sesiones, efectos de personalidad y reglas que emergen bajo presión.

**Parte de una investigación doctoral en la Universidad Complutense de Madrid.**

---

## ¿Qué me aporta como usuario?

PRAXIS no es solo un logger de investigación. Devuelve un **diagnóstico de tu flujo de trabajo**.

Te ayuda a ver:
- dónde la IA ahorra tiempo y dónde crea retrabajo
- cuándo estás confiando demasiado en una salida persuasiva
- si los resets de sesión están dañando calidad o continuidad
- cuánta corrección humana sigue necesitando tu workflow
- qué reglas emergen de fallos reales en vez de teoría

---

## ¿Qué es PRAXIS?

PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems) es un framework de investigación que documenta lo que sucede cuando humanos y sistemas de IA trabajan juntos en condiciones de producción sostenidas.

Este kit es el **instrumento de medición**: captura datos para que los investigadores puedan estudiar fenómenos de gobernanza como:
- Reglas que emergen orgánicamente de los fallos (emergencia de gobernanza)
- Cómo la personalidad de la IA afecta tu confianza y comportamiento (gobernanza relacional)
- Qué ocurre al cambiar de modelo de IA manteniendo la misma configuración de gobernanza (portabilidad de personalidad)
- Cómo se recuperan la memoria y la calibración entre sesiones
- Si la estructura del flujo de trabajo tiene influencia medible en los resultados

---

## Inicio Rápido

### 1. Instalar

**macOS / Linux:**
```bash
bash install.sh
```

**Windows (PowerShell):**
```powershell
.\install.ps1
```

**Manual (cualquier plataforma con Python 3.8+):**
```bash
python collector/praxis_cli.py init
```

### 2. Completar la encuesta previa (~10 minutos)
```bash
praxis survey pre
```

### 3. Registrar tus tareas con IA

Después de cada tarea significativa asistida por IA:
```bash
praxis log "Lo que lograste" -d 45 -m claude -q 4 -i 2 -h2 1
```

| Flag | Significado | Ejemplo |
|------|------------|---------|
| `-d` | Duración en minutos | `-d 45` |
| `-m` | Modelo/herramienta de IA | `-m claude` `-m copilot` `-m cursor` |
| `-q` | Calidad autoevaluada 1-5 | `-q 4` |
| `-i` | Ciclos de generación de IA | `-i 2` (2 intentos) |
| `-h2` | Correcciones humanas | `-h2 1` (corregido una vez) |
| `--l1r` | Registrar observaciones de gobernanza relacional | `--l1r` (preguntas interactivas) |

### 4. Registrar eventos de gobernanza

Cuando algo falla y aprendes de ello:
```bash
praxis incident "La IA usó una versión obsoleta de la librería"
```
Esto pregunta: qué pasó, causa raíz, y si debe crearse una nueva regla.

### 5. Activar la gobernanza estructurada (cuando estés listo)
```bash
praxis activate
```

Esto activa el modo de observación estructurada.

### 6. Exportar tus datos
```bash
praxis export
```

Genera un archivo ZIP anonimizado para el análisis de investigación, incluyendo tu diagnóstico de workflow.

### 7. Ver tu diagnóstico
```bash
praxis diagnose
```

---

## Novedades en v0.9.2

| Característica | Descripción |
|---------------|-------------|
| **L1-R: Gobernanza Relacional** | Registra seguridad percibida, calidez, confianza del usuario y tendencia a la complacencia por sprint (`--l1r`) |
| **P9: Independencia de Arquitectura** | Funciona tanto para un solo modelo (Copilot, Aider) como para multi-agente (OpenClaw, Cowork) |
| **Plantillas de autogobernanza** | Protocolos para sistemas de un solo modelo sin orquestador externo |
| **Calibración de personalidad** | Mecanismo integrado para detectar cuándo el comportamiento de la IA difiere de la configuración de gobernanza |
| **Registro de incidentes** | Captura estructurada de eventos de emergencia de gobernanza (`praxis incident`) |
| **Observaciones de límite de sesión** | Seguimiento de recuperación de memoria y degradación de calibración entre sesiones |
| **Diseño factorial 2x2** | Condiciones experimentales: Modelo (Sonnet/Opus) x Estructura (estructurado/no estructurado) |
| **Diagnóstico para el participante** | Convierte los logs en un espejo útil del propio workflow |
| **Envío con throttling** | El envío opcional puede limitarse por participante para no saturar el inbox |
| **Enfoque descriptivo** | El kit documenta fenómenos en lugar de evaluar si la gobernanza "mejora" las cosas |

---

## Comandos

```
praxis status          Muestra fase, días activos, conteo de entradas, promedios
praxis diagnose        Muestra tu diagnóstico de workflow
praxis log "tarea"     Registra una tarea (interactivo sin argumentos)
praxis incident "desc" Registra un evento de emergencia de gobernanza
praxis activate        Activa el modo de observación estructurada
praxis govern "regla"  Registra un evento de gobernanza
praxis survey pre      Encuesta previa al estudio
praxis survey post     Encuesta posterior al estudio
praxis export          Genera ZIP de datos anonimizados para investigación
praxis submit          Exporta y envía datos cuando esté habilitado
praxis platforms       Muestra las plataformas de IA detectadas
```

---

## Plataformas Soportadas

| Plataforma | Archivo de Gobernanza | Tipo |
|------------|----------------------|------|
| OpenClaw | SOUL.md + AGENTS.md + HEARTBEAT.md | Orquestador multi-agente |
| Claude Cowork | CLAUDE.md | Multi-agente |
| Codex | AGENTS.md | Agente en sandbox |
| Cursor | .cursorrules / .cursor/rules/ | IDE con IA |
| Windsurf | .windsurfrules | IDE con IA |
| Copilot | .github/copilot-instructions.md | Asistente de IA |
| Aider | .aider.conf.yml + conventions | Agente CLI |
| Continue.dev | .continue/config.json | Extensión de IDE |
| Cline | .cline/instructions.md | Extensión de IDE |
| Roo Code | .roo/rules.md | Extensión de IDE |
| Genérica | PRAXIS_GOVERNANCE.md | Cualquier sistema |

---

## Contexto de Investigación

Este kit forma parte de una tesis doctoral que documenta fenómenos de gobernanza en sistemas de producción asistidos por IA durante el período 2025-2027. Las preguntas de investigación:

1. ¿Qué fenómenos de gobernanza emergen cuando los sistemas de IA operan bajo instrumentación estructurada?
2. ¿Cómo afecta la personalidad de la IA (tono, seguridad, calidez) a la confianza y el comportamiento del usuario?
3. ¿Muestra la estructura del flujo de trabajo una influencia medible en los resultados, independientemente de la capacidad del modelo?
4. ¿Qué aspectos no cubren los marcos de gobernanza de IA actuales (AI Act de la UE, OCDE, NIST)?

**Información importante:**
- Las evaluaciones de calidad son autoevaluadas por el participante
- La evaluación externa ciega está disponible para resultados de observación estructurada
- Todos los datos se anonimizan y almacenan localmente - nada se envía a ningún servidor automáticamente
- Los participantes pueden retirarse en cualquier momento

---

## Citar este trabajo

```bibtex
@software{herreros2026praxis,
  author = {Herreros Riaza, Javier},
  title = {PRAXIS Universal Kit},
  version = {0.2.0},
  year = {2026},
  publisher = {Universidad Complutense de Madrid},
  url = {https://github.com/jhriaza/praxis-universal-kit}
}
```

## Licencia

CC BY-SA 4.0 - ver [LICENSE](LICENSE)

---

*PRAXIS Universal Kit v0.9.2 - 2026-04-29*
*Investigación doctoral - Universidad Complutense de Madrid*
