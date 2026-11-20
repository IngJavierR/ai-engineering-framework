
# AI Engineering Framework

Framework centralizado y versionado para estandarizar
el desarrollo de software asistido por GitHub Copilot.

## Objetivo

Establecer prácticas de ingeniería reutilizables,
verificables y adaptables a distintos proyectos
y clientes.

## Estado

Versión candidata de trabajo: `0.5.0-rc.1`.
Estado: Release candidate local. No existe todavía un tag, GitHub Release ni
artefacto publicado para esta versión.

La release `v0.3.0` permanece inmutable.

## Roadmap y estado de implementación

Estado reconciliado el 2026-11-19 contra el commit local `bfefae6` del
framework y el laboratorio Angular `63d72e5`. Los estados se basan en la
evidencia disponible en estos repositorios; la presencia de artefactos o
pruebas unitarias aisladas no equivale por sí sola a cumplir un criterio de
salida.

| Milestone | Estado | Evidencia y límite actual |
| --- | --- | --- |
| MVP — Fundación y gobierno de Java | Implementado, sin criterio de salida demostrado | Existen instrucciones Java, orquestador, instalador y regresión del framework. No hay en el workspace evidencia ejecutable de un proyecto Spring Boot que rechace conjuntamente una violación arquitectónica y un cambio fuera de alcance. |
| M1 — OpenAPI + DDD + Liquibase | Implementado, con evidencia histórica no reproducida en esta reconciliación | Las skills e instrucciones existen. Este README registra 40 pruebas históricas, incluyendo contrato HTTP y PostgreSQL incremental, pero el laboratorio Java y sus resultados no están presentes para reproducirlos aquí. Por ello no se declara el criterio de salida como demostrado en el estado actual. |
| M2 — Requerimientos + HTML + pruebas | Implementado en modalidad Development / Lab | `customer-profile` se implementó y probó en el laboratorio Angular: unitarias, typecheck, build y Playwright pasaron. La certificación formal permanece `NOT EXECUTED`; no se fabricaron PREPARE ni VERIFY. |
| M3 — Performance + Arquitectura 4+1 | Implementado en modalidad Development / Lab | El laboratorio Java ejecutó Gatling contra Spring Boot y PostgreSQL locales con perfiles smoke, baseline y stress; generó informes HTML y documentó vistas 4+1 Mermaid y ADR. No constituye certificación de capacidad productiva. |
| M3.1 — Functional Testing | Implementado en modalidad Development / Lab | El laboratorio Angular ejecutó 4 escenarios Cypress headless contra `customer-profile`, con captura de artefactos locales ignorados por Git. La suite conserva Playwright como capacidad independiente. |
| M3.3 — Security Validation | Implementado en modalidad Development / Lab | Se completaron reportes de seguridad Markdown y JSON para los laboratorios Angular y Java, sustentados por evidencia local y preparados para validación manual. No constituyen certificación formal. |
| M4 — Distribución corporativa y políticas de cliente | Implementado en modalidad local demostrable | Java y Angular consumen la misma línea de framework con locks y políticas aisladas; bootstrap, idempotencia, conflictos y propuesta local de actualización fueron probados sin crear PR remoto. |
| M5 — Evolución multilenguaje | Implementado en modalidad de piloto | Gobierno transversal, perfiles aislados y fixtures React/FastAPI demostrados; consultar la evaluación de preparación para límites de distribución. |

La autorización SSH firmada es una capacidad experimental adicional de M2. No
se considera por sí misma un criterio de salida del milestone; sin embargo, el
manifiesto disponible tampoco satisface los controles M2 previos existentes:
es ilustrativo, carece de PREPARE y de un ancla externa independiente, y la
decisión local limita explícitamente la autorización a documentación y
evidencia. Consultar [el reporte de cierre de la reconciliación](docs/m2/roadmap-reconciliation-2026-11-19.md).

## Preparación corporativa

La evaluación integral actual concluye **READY_WITH_LIMITATIONS**: el framework
es apto para un piloto interno controlado con fuente local fijada, locks y
revisión humana, pero no para distribución corporativa general ni release
publicada. Consultar [release-readiness.md](docs/release-readiness.md) para la
matriz de madurez, riesgos bloqueantes, condiciones operativas y decisión de
dirección pendiente.

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

El repositorio contiene capacidades transversales y específicas por stack. Son
políticas reutilizables del framework, no componentes de una aplicación.

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
- `.github/skills/gatling-performance/SKILL.md`
  - `references/controlled-profiles.md`
- `.github/skills/cypress-functional-testing/SKILL.md`
  - `references/functional-scenario-guidance.md`
- `.github/skills/security-validation/SKILL.md`
  - `references/reporting-guidance.md`

Las skills guían análisis, planificación y criterios de aceptación.
No sustituyen requisitos funcionales del proyecto consumidor ni
convierten un análisis estático en una validación de ejecución.

### Capacidades presentes y capacidades distribuidas

Las instrucciones, skills y referencias anteriores están presentes en
el repositorio central y se distribuyen por `tools/install.py` como
ocho archivos gestionados. El orquestador, `AGENTS.md` y
`.github/copilot-instructions.md` pertenecen al mantenimiento del
framework y no se copian a los consumidores.

La distribución incorpora locks, bootstrap y políticas aisladas del consumidor,
pero no quality gates generales remotos. `automatedQualityGates` permanece en
`false`.

## Distribución

El instalador requiere un repositorio Git destino y una fuente del framework
sin cambios pendientes. Los locks heredados conservan `java-base`; los perfiles
nuevos usan `universal-governance` y seleccionan explícitamente el stack. No se
infiere el stack desde los archivos del consumidor.

### Capacidades y dependencias

| Capacidad solicitada | Capacidades resueltas | Archivos gestionados |
| --- | --- | ---: |
| Ninguna | `java-base` | 8 |
| `frontend-ui-design` | `java-base`, `frontend-ui-design` | 12 |
| `angular-ui-implementation` | `java-base`, `frontend-ui-design`, `angular-ui-implementation` | 16 |
| `react-ui-implementation` | `java-base`, `frontend-ui-design`, `react-ui-implementation` | 16 |
| Angular y React | `java-base`, `frontend-ui-design`, Angular, React | 20 |
| Gatling | `java-base`, `gatling-performance` | 10 |
| Cypress | `cypress-functional-testing` | 2 |
| Security validation | `security-validation` | 2 |

La capacidad de revisión se instala sin herramientas ni escáneres implícitos:

```bash
python3 tools/install.py --target ../consumer-project \
  --capability security-validation
```

Cada consumidor selecciona y ejecuta sus analizadores locales compatibles; la
skill define cómo registrar alcance, evidencia, hallazgos y limitaciones sin
transferir código a servicios externos.

## Bootstrap y políticas de cliente

`tools/bootstrap.py` es la interfaz de consumo corporativo. Delega la copia,
lock, integridad e idempotencia exclusivamente a `tools/install.py`; no crea un
segundo instalador. Requiere una versión disponible en la fuente local, una
política JSON autorizada y un repositorio Git destino.

```bash
python3 tools/bootstrap.py \
  --target ../consumer-project \
  --version 0.5.0-rc.1 \
  --client-policy docs/m4/examples/client-a-java-policy.json \
  --dry-run
```

Una primera incorporación que encuentre artefactos del framework sin lock se
detiene. `--replace-framework-artifacts` es una decisión explícita de adopción;
no reemplaza archivos locales por defecto. Las instalaciones posteriores usan
el lock existente y solicitan la actualización controlada mediante el
instalador. Cada consumidor recibe su política en
`.ai-framework/policies/<client-id>.json` y estado en
`.ai-framework/bootstrap.json`.

### Precedencia de políticas

1. Los controles obligatorios globales del framework siempre prevalecen.
2. La política de cliente puede habilitar capacidades, añadir reglas y declarar
   excepciones explícitas dentro de su propio consumidor.
3. Una política que solicite deshabilitar controles obligatorios se rechaza.
4. Las políticas no se comparten: cada consumidor mantiene su archivo y lock,
   por lo que una actualización no puede modificar la política de otro.

`--proposal-dir` genera `proposal.json` y `PR_UPDATE.md` para revisión humana
local. El workflow [propose-framework-update.yml](.github/workflows/propose-framework-update.yml)
prepara esta validación para GitHub Actions; no abre ni fusiona Pull Requests
remotos sin una operación autorizada posterior.

## Perfiles multilenguaje

El instalador conserva `java-base` para locks históricos, pero los perfiles
nuevos inician en `universal-governance`. Por ello Angular, React y FastAPI no
reciben instrucciones Java, OpenAPI Java, Liquibase Java ni Gatling salvo que
un consumidor los solicite de forma explícita y compatible.

| Perfil | Gobierno común | Capacidades de stack | Excluye por defecto |
| --- | --- | --- | --- |
| `java-spring` | `universal-governance` | `java-base`, Gatling, seguridad | Angular, React, FastAPI |
| `angular` | `universal-governance` | diseño/implementación Angular, Cypress, seguridad | Java, React, FastAPI |
| `react` | `universal-governance` | diseño/implementación React, Cypress, seguridad | Java, Angular, FastAPI |
| `python-fastapi` | `universal-governance` | FastAPI, seguridad | Java, Angular, React |

```bash
python3 tools/install.py --target ../consumer-project --profile react
python3 tools/install.py --target ../consumer-project --profile python-fastapi
```

Una migración desde un lock heredado basado en `java-base` requiere
`--migrate-stack`. El instalador valida hashes existentes, muestra los
artefactos que retirará en dry-run y nunca elimina capacidades implícitamente.

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

La versión candidata `0.5.0-rc.1` registra `.ai-framework.lock.json` con el
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
regresión de distribución de la release candidate se ejecuta contra repositorios temporales;
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
