# PRAXIS Universal Kit

**Herramienta de investigación multiplataforma para observar fenómenos de gobernanza en flujos de trabajo asistidos por IA**

PRAXIS Kit instrumenta tu flujo de trabajo con IA para capturar lo que realmente ocurre: emergencia de gobernanza, efectos de personalidad, límites de sesión, patrones de calidad, antes y después de introducir gobernanza estructurada.

**Parte de una investigación doctoral en la Universidad Complutense de Madrid.**

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

Esto inyecta archivos de gobernanza en tus herramientas de IA y transiciona a la Fase B.

### 6. Exportar tus datos
```bash
praxis export
```

Genera un archivo ZIP anonimizado para el análisis de investigación.

---

## Novedades en v0.2

| Característica | Descripción |
|---------------|-------------|
| **L1-R: Gobernanza Relacional** | Registra seguridad percibida, calidez, confianza del usuario y tendencia a la complacencia por sprint (`--l1r`) |
| **P9: Independencia de Arquitectura** | Funciona tanto para un solo modelo (Copilot, Aider) como para multi-agente (OpenClaw, Cowork) |
| **Plantillas de autogobernanza** | Protocolos para sistemas de un solo modelo sin orquestador externo |
| **Calibración de personalidad** | Mecanismo integrado para detectar cuándo el comportamiento de la IA difiere de la configuración de gobernanza |
| **Registro de incidentes** | Captura estructurada de eventos de emergencia de gobernanza (`praxis incident`) |
| **Observaciones de límite de sesión** | Seguimiento de recuperación de memoria y degradación de calibración entre sesiones |
| **Diseño factorial 2x2** | Condiciones experimentales: Modelo (Sonnet/Opus) x Estructura (estructurado/no estructurado) |
| **Enfoque descriptivo** | El kit documenta fenómenos en lugar de evaluar si la gobernanza "mejora" las cosas |

---

## Comandos

```
praxis status          Muestra fase, días activos, conteo de entradas, promedios
praxis log "tarea"     Registra una tarea (interactivo sin argumentos)
praxis incident "desc" Registra un evento de emergencia de gobernanza
praxis activate        Transición Fase A → Fase B (gobernanza activa)
praxis govern "regla"  Registra un evento de gobernanza (Fase B)
praxis survey pre      Encuesta previa al estudio
praxis survey post     Encuesta posterior al estudio
praxis export          Genera ZIP de datos anonimizados para investigación
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
- Las evaluaciones de calidad en la Fase A son autoevaluadas por el participante
- La evaluación externa ciega (PRAXIS-Q) está disponible para los resultados de la Fase B
- Todos los datos se anonimizan y almacenan localmente — nada se envía a ningún servidor automáticamente
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

CC BY-SA 4.0 — ver [LICENSE](LICENSE)

---

*PRAXIS Universal Kit v0.2 — 2026-04-15*
*Investigación doctoral — Universidad Complutense de Madrid*
