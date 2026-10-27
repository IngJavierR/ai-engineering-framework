
# AI Engineering Framework

Framework centralizado y versionado para estandarizar
el desarrollo de software asistido por GitHub Copilot.

## Objetivo

Establecer prácticas de ingeniería reutilizables,
verificables y adaptables a distintos proyectos
y clientes.

## Estado

Versión candidata: 0.3.0
Estado: Pendiente de release. No está publicada.

## Componentes

- AGENTS.md: contrato general de los agentes.
- .github/copilot-instructions.md:
  instrucciones para GitHub Copilot.
- framework.yaml: metadatos y versión.

## Agentes disponibles

### Engineering Orchestrator

Ubicación:
`.github/agents/orchestrator.agent.md`

Responsabilidad:
- Analizar solicitudes de ingeniería.
- Identificar el contexto del repositorio.
- Evaluar impacto y riesgos.
- Proponer planes de implementación.
- Identificar validaciones necesarias.

Restricciones:
- No modifica archivos.
- No implementa código.
- No ejecuta pruebas.
- No coordina todavía otros agentes.

Estado: Disponible para validación en el MVP.

## Capacidades disponibles

El repositorio contiene las siguientes capacidades Java. Son políticas
reutilizables del framework, no componentes de una aplicación.

### Instrucciones instalables

- `.github/instructions/java.instructions.md`: diseño Java, DDD,
  manejo de errores de integridad, pruebas y evidencia de validación.
- `.github/instructions/openapi-ddd.instructions.md`: contrato-first,
  compatibilidad, DDD y pruebas HTTP contra OpenAPI.
- `.github/instructions/liquibase.instructions.md`: cambios
  estructurales mediante Liquibase XML, inmutabilidad y validación de
  migraciones.

### Skills instalables

- `.github/skills/openapi-to-ddd/SKILL.md`
  - `references/ddd-structure.md`
  - `references/contract-compatibility.md`
- `.github/skills/liquibase-versioning/SKILL.md`
  - `references/xml-conventions.md`

Las skills guían análisis, planificación y criterios de aceptación.
No sustituyen requisitos funcionales del proyecto consumidor ni
convierten un análisis estático en una validación de ejecución.

### Capacidades presentes y capacidades distribuidas

Las instrucciones, skills y referencias anteriores están presentes en
el repositorio central y se distribuyen por `tools/install.py` como
ocho archivos gestionados. El orquestador, `AGENTS.md` y
`.github/copilot-instructions.md` pertenecen al mantenimiento del
framework y no se copian a los consumidores.

La distribución no incorpora políticas de cliente ni quality gates
generales. `automatedQualityGates` permanece en `false`.

## Distribución candidata

El instalador requiere un repositorio Git destino y una fuente del
framework sin cambios pendientes. Registra `.ai-framework.lock.json`
con versión, commit de origen y hashes SHA-256 calculados desde los
archivos reales.

### Instalación limpia y dry-run

```bash
python3 tools/install.py \
  --target ../consumer-project \
  --dry-run

python3 tools/install.py \
  --target ../consumer-project
```

El `dry-run` valida el escenario sin escribir archivos. Una instalación
limpia rechaza cualquier archivo ya existente en una ruta gestionada.

### Repetición idempotente

Ejecutar nuevamente el mismo comando solo reconoce la instalación si
el lock y los hashes de todos los archivos gestionados coinciden. No
reescribe archivos ni lock en ese caso.

### Upgrade explícito desde v0.2.0

```bash
python3 tools/install.py \
  --target ../consumer-project \
  --upgrade \
  --dry-run

python3 tools/install.py \
  --target ../consumer-project \
  --upgrade
```

El upgrade no es automático. Solo admite un lock `v0.2.0` verificable:
el manifest histórico debe tener el formato esperado, el archivo Java
previamente gestionado debe conservar su hash local y ese hash debe
coincidir con el contenido del commit de origen registrado. Si la
revisión histórica no puede verificarse, el lock es corrupto o el
archivo fue modificado localmente, el instalador se detiene sin hacer
cambios y se requiere una actualización manual.

### Conflictos e integridad

El instalador no sobrescribe archivos propios del consumidor. Rechaza
conflictos en archivos nuevos, symlinks en rutas gestionadas o ancestros
del destino, traversal de rutas y locks no válidos. Antes de escribir,
valida los conflictos y prepara los artefactos en staging.

Durante una instalación o upgrade conserva respaldos para recuperar
errores manejables de reemplazo. Los respaldos se eliminan únicamente
cuando archivos y lock se publicaron correctamente. No existe
atomicidad global ante `SIGKILL`, apagados o fallos de sistema de
archivos; en esos casos pueden requerirse recuperación manual desde
staging o respaldos.

## Gobierno de APIs y base de datos

Las instrucciones y skills consolidadas establecen que:

- OpenAPI se trata como contrato HTTP autoritativo y las pruebas de
  conformidad comparan respuestas HTTP reales contra schemas declarados.
- Las validaciones negativas cubren, cuando el contrato los declara,
  campos requeridos, tipos, formatos, longitudes, restricciones y
  `additionalProperties`.
- Los validadores parciales documentan sus construcciones no soportadas;
  no se presentan como conformidad OpenAPI completa.
- La compatibilidad se analiza en sentido backward y forward para
  requests, responses y consumidores estrictos. Propiedades opcionales,
  propiedades omitidas, nulabilidad JSON y nulabilidad de persistencia
  se evalúan por separado.
- La arquitectura DDD mantiene separados dominio, aplicación,
  infraestructura e interfaces HTTP; los contratos existentes se
  preservan.
- Todo cambio estructural se versiona mediante Liquibase XML, con
  changesets nuevos. Los changesets aplicados permanecen inmutables y
  su integridad se contrasta con contenido o hashes de una línea base
  verificable.
- Las migraciones incrementales se validan, cuando existe tooling,
  sobre el esquema anterior con registros existentes; se verifica
  preservación de datos, `DATABASECHANGELOG`, índices y constraints en
  el motor real, y concurrencia cuando la regla modificada lo requiere.
- Los riesgos de rollback que eliminan columnas o datos se documentan;
  la recuperación hacia adelante puede ser preferible.

## Evidencia de validación

Los estados de evidencia no son estados de workflow de las skills:

| Estado | Significado |
| --- | --- |
| `GENERATED` | Se produjeron artefactos; no implica compilación. |
| `COMPILED` | La compilación terminó correctamente con evidencia. |
| `TESTED` | Se ejecutaron pruebas con resultados verificables y alcance conocido. |
| `VALIDATED` | Los criterios de aceptación declarados tienen evidencia suficiente para ese alcance. |
| `NOT_RUN` | Una comprobación aplicable permanece pendiente. |

Las skills pueden usar estados de workflow como `ANALYZED`,
`READY_FOR_IMPLEMENTATION`, `READY_FOR_VALIDATION` o `BLOCKED`. Estos
describen el progreso del trabajo y no reemplazan la evidencia anterior.

La suite del instalador contiene 14 pruebas automatizadas ejecutadas y
aprobadas durante R2.3. Esta evidencia cubre instalación, repetición,
dry-run, locks, upgrade verificado desde v0.2.0, symlinks y recuperación
de fallos manejables. No demuestra una validación end-to-end de la
distribución candidata en un consumidor.

## Riesgos pendientes para R3

- Ejecutar una validación end-to-end en un consumidor temporal o
  representativo antes de release.
- Verificar la distribución candidata desde una instalación v0.2.0 y
  una instalación limpia fuera de la suite unitaria.
- Validar en un consumidor los flujos OpenAPI HTTP reales y las
  migraciones Liquibase sobre PostgreSQL con datos previos cuando su
  alcance lo requiera.
- No declarar quality gates generales hasta que existan automatización,
  definición de alcance y evidencia verificable.

## Versiones anteriores

La versión `0.2.0` distribuyó únicamente la instrucción Java y registró
un lock de un solo archivo. La candidata `0.3.0` mantiene una ruta de
upgrade explícita y verificable desde esa instalación.
