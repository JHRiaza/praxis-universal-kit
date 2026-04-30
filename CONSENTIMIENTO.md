# Formulario de Consentimiento Informado para Participación en Investigación

## Información del Estudio

**Título:** Arquitectura metodológica para sistemas autónomos asistidos por IA: Estudio cuasi-experimental sobre la adopción del framework de gobernanza PRAXIS

**Investigador principal:** Javier Herreros Riaza
**Institución:** Programa de Doctorado en Comunicación Audiovisual y Publicidad (CAVP)
**Framework:** PRAXIS v1.1

---

## Propósito del Estudio

Esta investigación documenta qué sucede cuando las personas usan un framework de gobernanza (PRAXIS) para su trabajo asistido por IA. El estudio observa flujos de trabajo reales de forma pasiva y mediante checkouts calibrados para identificar fenómenos de gobernanza como la emergencia de reglas, la calibración de confianza y los efectos en los límites de sesión.

---

## En Qué Consiste la Participación

### Duración
- **Período de observación:** Mínimo 3-4 semanas de trabajo asistido por IA

### Qué hará
1. Instalar el Kit PRAXIS en su computadora
2. Completar una encuesta pre-estudio (~10 minutos)
3. Usar `praxis start` / `praxis stop` para capturar sus sesiones de trabajo con IA
4. Después de cada sesión, ejecutar `praxis checkout` para calibrar los datos (resumen de tarea, calidad, observaciones de gobernanza)
5. Registrar eventos de gobernanza cuando cree o modifique reglas
6. Completar una encuesta post-estudio (~12 minutos)
7. Exportar sus datos anónimos para el investigador

### Qué se recopila

**Recopilado (con su conocimiento):**
- Métricas de tareas: descripción, duración, calificación de calidad (1-5), ciclos de generación de IA, correcciones humanas
- Nombres de modelos/herramientas de IA que usted reporta
- Puntuaciones de calidad y observaciones de gobernanza (checkout)
- Observaciones L1-R (opcionales): sus percepciones sobre la seguridad, calidez, confianza y tendencia a la complacencia de la IA por tarea
- Eventos de gobernanza: reglas que crea, incidentes, modificaciones
- Observaciones de límite de sesión: recuperación de memoria y calibración entre sesiones
- Respuestas a encuestas (pre y post)
- Fechas de sesión y conteos de sesión
- Asignación de condición experimental (si participa en el estudio factorial 2×2)
- Evaluación externa de calidad: un evaluador independiente puede puntuar sus resultados anonimizados mediante PRAXIS-Q

**Nunca se recopila:**
- El contenido de su código fuente, documentos o archivos
- Registros de conversaciones o prompts de IA
- Información de identificación personal más allá de su ID de participante
- Nada fuera del directorio `.praxis/`

---

## Privacidad y Seguridad de Datos

### Almacenamiento
Todos los datos se almacenan **localmente** en su computadora en un directorio `.praxis/`. Nada se sube automáticamente a ningún servidor o servicio en la nube.

### Seudonimización
Su ID de participante se genera automáticamente a partir de un hash determinista de características de la máquina (nombre de host, dirección MAC, sistema operativo). Esto es **seudonimización**, no anonimización completa: dada la identidad de la máquina, el ID puede ser verificado. No incluye su nombre, correo electrónico ni información directamente identificable. El mismo participante en una máquina diferente recibirá un ID diferente.

Al exportar datos (`praxis export`), el sistema:
- Elimina cualquier dato potencialmente identificable de las entradas de métricas
- Usa solo su ID de participante (formato: `PRAXIS-XXXXXXXX`)
- Le permite opcionalmente redactar descripciones de tareas
- Crea un archivo ZIP adecuado para la entrega a la investigación

### Publicación
- En todas las publicaciones, aparecerá como "Participante P###" o equivalente
- Su nombre no aparecerá en ninguna publicación a menos que proporcione consentimiento escrito explícito adicional
- Las respuestas individuales pueden citarse de forma anónima para ilustrar hallazgos

### Conservación de datos
- Sus datos locales permanecen en su computadora bajo su control
- Los datos enviados son conservados por el investigador durante la duración de la investigación doctoral (finalización estimada: 2027)
- Puede solicitar la eliminación de sus datos enviados en cualquier momento

---

## Sus Derechos

Como participante en la investigación, usted tiene derecho a:

- **Retirarse** en cualquier momento sin consecuencias usando `praxis withdraw` (elimina todos los datos locales permanentemente)
- **Revisar** los datos recopilados sobre usted antes de la entrega
- **Redactar** descripciones de tareas de sus datos exportados (use `praxis export --redact-tasks`)
- **Negarse** a responder cualquier pregunta de la encuesta
- **Solicitar** una copia de los hallazgos de la investigación cuando el estudio esté completo
- **Contactar** al investigador con cualquier pregunta o inquietud

---

## Beneficios

Al participar, usted:
- Recibe el Kit PRAXIS configurado para sus herramientas de IA específicas
- Obtiene información sobre sus propios patrones de flujo de trabajo de IA a partir de sus métricas personales
- Contribuye a una investigación doctoral que puede beneficiar a la comunidad más amplia de usuarios de IA
- Será reconocido en los agradecimientos de la tesis (si lo desea)
- Tendrá acceso a los hallazgos finales de la investigación

---

## Riesgos

- Compromiso de tiempo de unos minutos al día para registrar tareas
- Breve período de ajuste al adoptar gobernanza si se activa
- No se conocen riesgos psicológicos, físicos ni económicos

---

## Contacto

Para preguntas sobre esta investigación:

**Investigador:** Javier Herreros Riaza
**Institución:** 
**Programa:** Doctorado CAVP

---

## Declaración de Consentimiento

Al ejecutar el instalador PRAXIS y responder "sí" al aviso de consentimiento, usted declara que:

- [ ] Ha leído y comprendido este formulario de consentimiento
- [ ] Comprende qué datos se recopilan y cómo se utilizarán
- [ ] Comprende que puede retirarse en cualquier momento usando `praxis withdraw`
- [ ] Tiene 18 años de edad o más
- [ ] Consiente participar en este estudio de investigación

Su consentimiento se registra con una marca de tiempo en `.praxis/state.json` en su máquina local.

---

*PRAXIS Universal Kit v0.2*
*Investigación Doctoral*
*Framework: CC BY-SA 4.0*
