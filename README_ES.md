# PRAXIS Universal Kit

**Herramienta de investigación multiplataforma para medir flujos de trabajo con IA**

PRAXIS Kit te permite medir tu flujo de trabajo con IA — antes y después de adoptar estructura de gobernanza — usando una herramienta de línea de comandos que funciona con cualquier plataforma de IA.

**Parte de una investigación doctoral en la Universidad Complutense de Madrid.**

---

## ¿Qué es PRAXIS?

PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems) es un framework de gobernanza para flujos de trabajo humano-IA. Este kit mide si añadir estructura de gobernanza cambia la efectividad con la que trabajas con herramientas de IA.

La investigación usa un **diseño de medidas repetidas**: tú eres tu propio grupo control. Primero trabajas normalmente (Fase A, línea base), luego añades gobernanza (Fase B, tratamiento). Comparamos tu propio antes/después.

---

## Inicio Rápido

### 1. Instalar

**macOS / Linux:**
```bash
bash install.sh --lang es
```

**Windows (PowerShell):**
```powershell
.\install.ps1 -Lang es
```

**Manual (cualquier plataforma con Python 3.8+):**
```bash
python collector/praxis_cli.py init --lang es
```

### 2. Completa la encuesta inicial (~10 minutos)
```bash
praxis survey pre --lang es
```

### 3. Trabaja normalmente y registra tus tareas de IA

Después de cada tarea significativa asistida por IA:
```bash
praxis log "Lo que lograste" -d 45 -m claude -q 4 -i 2 -h 1
```

| Flag | Significado | Ejemplo |
|------|------------|---------|
| `-d` | Duración en minutos | `-d 45` |
| `-m` | Modelo/herramienta de IA | `-m claude` `-m copilot` `-m cursor` |
| `-q` | Calidad 1-5 | `-q 4` |
| `-i` | Ciclos de generación de IA | `-i 2` (2 intentos) |
| `-h` | Correcciones humanas | `-h 1` (corregido una vez) |

### 4. Después de 7+ días, activa la gobernanza PRAXIS
```bash
praxis activate
```

Esto inyecta archivos de gobernanza en tus herramientas de IA (CLAUDE.md, .cursorrules, AGENTS.md, etc.) e inicia la Fase B.

### 5. Exporta tus datos al finalizar
```bash
praxis export
```

Envía el archivo ZIP generado al investigador.

---

## Comandos

```
praxis status          Muestra fase, días activos, conteo de entradas, promedios
praxis log "tarea"     Registra una tarea (interactivo si no hay argumentos)
praxis activate        Transición Fase A → Fase B (gobernanza activa)
praxis govern "regla"  Registra un evento de gobernanza (Fase B)
praxis survey pre      Encuesta basal pre-estudio
praxis survey post     Encuesta post-estudio (después de la Fase B)
praxis export          Genera ZIP de datos anónimos para el investigador
praxis platforms       Muestra qué herramientas de IA fueron detectadas
praxis withdraw        Elimina todos los datos y retira la participación
```

---

## Plataformas de IA Soportadas

PRAXIS detecta automáticamente e integra con:

| Plataforma | Integración | Archivo de Gobernanza |
|------------|------------|----------------------|
| Claude Code | Profunda | CLAUDE.md |
| OpenAI Codex | Profunda | AGENTS.md |
| Cursor | Profunda | .cursor/rules/praxis.md |
| Windsurf | Profunda | .windsurfrules |
| GitHub Copilot | Estándar | .github/copilot-instructions.md |
| Aider | Estándar | CONVENTIONS.md |
| Continue.dev | Estándar | .continue/rules/praxis.md |
| Cline | Estándar | .clinerules |
| Roo Code | Estándar | .roorules |
| Cualquier otra herramienta de IA | Genérica | PRAXIS_GOVERNANCE.md |

---

## Fase A — Línea Base (1-2 semanas)

Trabaja exactamente como lo haces hoy. Sin gobernanza, sin cambios.

Registra cada tarea asistida por IA con `praxis log`. Esto captura tus métricas naturales de flujo de trabajo: tiempo, calidad, iteraciones, correcciones.

Verifica tu progreso: `praxis status`

---

## Fase B — Gobernanza PRAXIS (2+ semanas)

Después de ejecutar `praxis activate`:

1. Los archivos de gobernanza se inyectan en tus herramientas de IA
2. Personaliza SOUL.md / AGENTS.md según tu trabajo
3. Continúa registrando con `praxis log` (se añade la rúbrica de calidad PRAXIS-Q)
4. Registra eventos de gobernanza: `praxis govern "Añadida regla: testear después de cada despliegue"`

---

## Privacidad

- Todos los datos se almacenan **localmente** en `.praxis/` en el directorio de tu proyecto
- **Sin telemetría**, sin subidas a la nube, sin internet requerido después de la instalación
- `praxis export` crea un ZIP anonimizado — las descripciones de tareas se pueden eliminar
- `praxis withdraw` elimina todo permanentemente en cualquier momento

Qué se recopila:
- Duraciones de tareas, calificaciones de calidad, conteos de iteraciones
- Nombres de modelos de IA que reportas
- Respuestas a encuestas
- Reglas de gobernanza que registras

Qué **nunca** se recopila:
- Contenido de archivos o código fuente
- Registros de conversaciones con IA
- Información de identificación personal

---

## Requisitos

- Python 3.8+
- macOS, Linux o Windows
- No se requiere conexión a internet
- No se requieren permisos de administrador/root
- Sin dependencias de pip — Python stdlib puro

---

## Contexto de la Investigación

**Título:** "Arquitectura metodológica para sistemas autónomos asistidos por IA"
**Investigador:** Javier Herreros Riaza
**Institución:** Universidad Complutense de Madrid — Programa Doctoral CAVP
**Framework:** PRAXIS v1.0

**Licencia:** CC BY-SA 4.0

¿Preguntas? Contacta al investigador a través del documento de información del estudio.

---

*PRAXIS Universal Kit v0.1 — 2026*
