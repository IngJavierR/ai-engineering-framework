
# AI Engineering Framework

Framework centralizado y versionado para estandarizar
el desarrollo de software asistido por GitHub Copilot.

## Objetivo

Establecer prácticas de ingeniería reutilizables,
verificables y adaptables a distintos proyectos
y clientes.

## Estado

Versión de trabajo: 0.4.0
Estado: Experimental. No existe un tag, release ni artefacto publicado para
esta versión.

La release `v0.3.0` permanece inmutable.

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

## Distribución

El instalador requiere un repositorio Git destino y una fuente del
framework sin cambios pendientes. Java base se instala siempre y las
capacidades frontend son opt-in explícito. No se infiere el stack desde
los archivos del consumidor.

### Capacidades y dependencias

| Capacidad solicitada | Capacidades resueltas | Archivos gestionados |
| --- | --- | ---: |
| Ninguna | `java-base` | 8 |
| `frontend-ui-design` | `java-base`, `frontend-ui-design` | 12 |
| `angular-ui-implementation` | `java-base`, `frontend-ui-design`, `angular-ui-implementation` | 16 |
| `react-ui-implementation` | `java-base`, `frontend-ui-design`, `react-ui-implementation` | 16 |
| Angular y React | `java-base`, `frontend-ui-design`, Angular, React | 20 |

`angular-ui-implementation` y `react-ui-implementation` dependen de
`frontend-ui-design`; al seleccionar ambas, la skill de diseño compartida
se deduplica. Cada skill y cada referencia se copia por archivo declarado,
sin copia recursiva de directorios.

### Instalación limpia y dry-run

```bash
# Java base por defecto
python3 tools/install.py --target ../consumer-project

# Solo planificación frontend compartida
python3 tools/install.py \
  --target ../consumer-project \
  --capability frontend-ui-design

# Angular incluye frontend-ui-design
python3 tools/install.py \
  --target ../consumer-project \
  --capability angular-ui-implementation

# React incluye frontend-ui-design
python3 tools/install.py \
  --target ../consumer-project \
  --capability react-ui-implementation

# Angular y React comparten una única instalación de diseño
python3 tools/install.py \
  --target ../consumer-project \
  --capability angular-ui-implementation \
  --capability react-ui-implementation

# La misma resolución, sin escribir archivos
python3 tools/install.py \
  --target ../consumer-project \
  --capability angular-ui-implementation \
  --dry-run
```

El `dry-run` resuelve capacidades y valida las precondiciones del mismo
modo que la instalación, pero no crea archivos, lock, staging ni respaldos.
Una instalación limpia rechaza cualquier archivo preexistente en una ruta
gestionada.

### Lock, reinstalación y upgrade

La versión experimental 0.4.0 registra `.ai-framework.lock.json` con el
schema `capability-lock/v1`, identidad del framework, versión, URL de fuente,
commit, lista determinista de capacidades resueltas y hashes SHA-256 por
artefacto.

Una reinstalación con el mismo commit, versión, capacidades y hashes valida
la instalación sin reescribir archivos ni lock. Un cambio de capacidades
requiere `--upgrade`:

```bash
python3 tools/install.py \
  --target ../consumer-project \
  --capability angular-ui-implementation \
  --capability react-ui-implementation \
  --upgrade \
  --dry-run

python3 tools/install.py \
  --target ../consumer-project \
  --capability angular-ui-implementation \
  --capability react-ui-implementation \
  --upgrade
```

Los upgrades son aditivos: no se permiten eliminaciones implícitas de
capacidades ni artefactos gestionados. El instalador mantiene compatibilidad
verificable con locks históricos `v0.2.0` y `v0.3.0`. Antes de un upgrade
verifica el commit registrado, la identidad y versión de su `framework.yaml`,
el manifest, las capacidades cuando aplica y los hashes históricos y locales.
Si el commit histórico no está disponible, el lock es incoherente, un archivo
fue modificado localmente o existe un nuevo archivo no gestionado en conflicto,
se detiene sin escribir y debe hacerse una actualización manual.

### Conflictos, seguridad y recuperación

El instalador rechaza modificaciones locales en archivos gestionados, archivos
no gestionados en rutas nuevas, symlinks normales o rotos en rutas gestionadas
o ancestros, traversal y locks inválidos. Antes de publicar prepara staging y
conserva respaldos para recuperar fallos manejables de reemplazo; los respaldos
se eliminan solo cuando archivos y lock se publican correctamente.

No existe atomicidad global ante `SIGKILL`, apagados o fallos irrecuperables
del sistema de archivos. En esos casos puede ser necesaria recuperación manual
desde staging o respaldos.

### Límites de la distribución frontend

Instalar una skill frontend no instala herramientas Python, validadores,
contratos M2, pruebas, PREPARE ni VERIFY. Tampoco ejecuta build, typecheck,
pruebas frontend ni comandos del consumidor.

Una skill instalada no autoriza una implementación y no implica el estado
`VALIDATED`. Antes de ejecutar un plan frontend deben estar disponibles y
haberse ejecutado los controles externos M2 requeridos, incluido el flujo
PREPARE/VERIFY y su evidencia aplicable.

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

La suite del instalador cubre instalación, repetición, dry-run, locks,
upgrades verificables, symlinks y recuperación ante fallos manejables. La
regresión de distribución 0.4.0 se ejecuta contra repositorios temporales;
no certifica la ejecución funcional de skills en un consumidor real.

## Limitaciones y validación funcional futura

La validación funcional de OpenAPI, DDD y Liquibase XML fue realizada durante M1 sobre el laboratorio Java, con 40 pruebas automatizadas exitosas, incluidas pruebas de contrato HTTP y migración incremental sobre PostgreSQL con datos preexistentes.

La release `v0.3.0` superó sus pruebas de instalación, actualización desde
v0.2.0, idempotencia e integridad de artefactos distribuidos.

Permanece pendiente una validación funcional independiente que demuestre el
comportamiento de GitHub Copilot utilizando skills distribuidas en un
consumidor nuevo.

El framework todavía no incorpora quality gates generales automatizados y no ofrece atomicidad global de instalación ante interrupciones abruptas.

## Versiones anteriores

La versión `0.2.0` distribuyó únicamente la instrucción Java y registró
un lock de un solo archivo. La versión `0.3.0` mantiene una ruta de
upgrade explícita y verificable desde esa instalación.
