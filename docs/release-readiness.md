# Evaluación de preparación corporativa

**Decisión: READY_WITH_LIMITATIONS**

El framework es apto para un piloto controlado con equipos que acepten una
fuente local fijada, locks verificables y revisión humana de actualizaciones.
No está listo para distribución corporativa general ni para declarar una
release publicada: no existe publicación remota/versionado de fuente
verificable, creación remota de Pull Requests ni evidencia formal ejecutada de
autorización M2 para un consumidor real.

## Alcance de esta evaluación

Repositorios verificados el 2026-11-19:

| Repositorio | HEAD | Estado inicial/final |
| --- | --- | --- |
| `ai-engineering-framework` | `dbc1c34` | Limpio durante la validación; esta evaluación añade solo documentación. |
| `ai-engineering-java-lab` | `69211e8` | Limpio; no se modificó código funcional. |
| `angular-customer-profile-consumer` | `1555b8e` | Limpio; no se modificó código funcional. |

La revisión se limita a evidencia local, contratos y mecanismos de
distribución actuales. No certifica servicios remotos, integración GitHub,
producción ni decisiones de autorización corporativa.

## Estado del roadmap original

| Milestone | Estado de preparación | Evidencia / límite |
| --- | --- | --- |
| MVP | PARTIAL | Instrucciones, orquestador, instalador y regresión existen; no se repitió el criterio Spring Boot arquitectónico original en esta ronda. |
| M1 | LAB_ONLY | Gobierno OpenAPI/DDD/Liquibase y laboratorio Java disponibles; parte de la evidencia PostgreSQL/contrato es histórica. |
| M2 | LAB_ONLY | Angular `customer-profile` validado en laboratorio; PREPARE/VERIFY y autorización formal no ejecutados. |
| M3 | LAB_ONLY | Gatling, 4+1 y ADR ejecutados localmente contra Java/PostgreSQL. |
| M3.1 | LAB_ONLY | Cypress ejecutado localmente; Playwright se conserva como evidencia independiente. |
| M3.3 | LAB_ONLY | Reportes Markdown/JSON y comprobaciones locales; no es pentest ni certificación formal. |
| M4 | READY para piloto | Locks, bootstrap, políticas aisladas, conflictos e idempotencia demostrados localmente; PR remoto no ejecutado. |
| M5 | READY para piloto | Perfiles universales/Java/Angular/React/FastAPI y fixtures ejecutados; React/FastAPI son demostraciones aisladas. |

## Matriz de capacidades y madurez

| Capacidad | Madurez | Condiciones documentadas |
| --- | --- | --- |
| Agente e instrucciones globales | READY | Uso local versionado; requieren revisión humana del consumidor. |
| Gobierno Java | READY | Perfil `java-spring` o lock heredado. |
| OpenAPI/DDD y Liquibase XML | READY | Capacidades Java; validación de aplicación depende del consumidor. |
| Contratos frontend HTML/YAML | LAB_ONLY | M2 formal requiere manifiesto ejecutable, PREPARE y evidencia externa. |
| Playwright y Cypress | LAB_ONLY | Ejecutados en Angular local; configuración de CI/servidor corresponde al consumidor. |
| Gatling, 4+1 y ADR | LAB_ONLY | Perfiles de carga solo para objetivos locales/no productivos autorizados. |
| Security validation | READY para piloto | Flujo, schema JSON y reportes disponibles; herramientas se seleccionan localmente por stack. |
| Instalador, locks y bootstrap | READY para piloto | Fuente local limpia, Git, hashes, adopción explícita y política aislada. |
| Políticas de cliente | READY para piloto | No pueden desactivar controles obligatorios; ejemplos no son políticas corporativas reales. |
| Actualización/PR | PARTIAL | Plan y workflow local listos; rama, push y PR remoto no ejecutados. |
| React | READY para piloto | Perfil y fixture TypeScript/Vitest ejecutados. |
| FastAPI | READY para piloto | Perfil y fixture Pydantic/OpenAPI/pytest ejecutados. |
| Autorización SSH y PREPARE/VERIFY | BLOCKED para gobierno formal | Verificadores fail-closed existen, pero no hay evidencia formal aplicable a un consumidor ejecutado. |

## Validaciones ejecutadas en esta evaluación

| Validación actual | Resultado |
| --- | --- |
| Framework `unittest discover -s tests -v` | PASS: 126 pruebas. |
| Integridad de perfiles Java/Angular/React/FastAPI | PASS: gobierno universal en todos; Java solo en `java-spring`. |
| Bootstrap dry-run Java y Angular | PASS. |
| Compilación Java `mvn -q -DskipTests compile` | PASS. |
| Typecheck y build Angular | PASS. |
| Verificación de lock/política | PASS: procedencia, capacidades y políticas independientes. |
| Alcance Git | PASS: no hubo cambios funcionales en los consumidores durante esta evaluación. |

Evidencia histórica no repetida: Gatling, Cypress, Playwright, auditorías de
seguridad y fixtures React/FastAPI; no se modificaron sus componentes desde sus
respectivas ejecuciones documentadas.

## Riesgos bloqueantes para distribución corporativa general

1. **Fuente y versiones remotas:** la selección de versión usa únicamente la
   fuente local disponible. No existe catálogo remoto firmado, release publicada
   ni artefacto distribuible verificable.
2. **Actualización por Pull Request:** se genera una propuesta local y un
   workflow preparado, pero no se ha demostrado creación de rama, push, PR,
   checks remotos ni control de permisos GitHub.
3. **Gobierno formal de implementación:** SSH/PREPARE/VERIFY es fail-closed,
   pero no hay una ruta formal ejercitada con evidencia externa para un
   consumidor real. No debe presentarse como listo para aprobaciones
   corporativas obligatorias.

## Limitaciones aceptables para un piloto

- Distribución desde un checkout local limpio fijado por commit y lock.
- Políticas de demostración reemplazadas por políticas aprobadas del equipo.
- Actualizaciones propuestas localmente y aplicadas tras revisión humana.
- Alcance restringido a Java/Angular existentes y fixtures React/FastAPI.
- Ejecución de validaciones en CI del equipo consumidor, no inferida del
  framework.

## Deuda técnica futura

- Resolver la advertencia de deprecación FastAPI/Starlette `TestClient`.
- Definir catálogo, firma/procedencia y ciclo de publicación remotos.
- Automatizar PR remoto con permisos mínimos, checks y revisión obligatoria.
- Añadir herramientas de advisories Java a la ruta de seguridad del consumidor.
- Ejecutar una demostración formal M2 con manifest, autorización y ancla
  externa verificables.

## Condiciones de operación y soporte para piloto

1. Usar un commit de framework limpio y registrar el lock generado.
2. Seleccionar el perfil correcto (`java-spring`, `angular`, `react` o
   `python-fastapi`) y revisar cualquier `--migrate-stack` en dry-run.
3. Versionar una política de cliente aprobada, aislada dentro del consumidor.
4. No usar `--replace-framework-artifacts` o `--replace-client-policy` sin
   revisión explícita de los archivos afectados.
5. Ejecutar build, pruebas y controles propios del consumidor antes de merge.
6. Tratar las skills como guía; no como certificación ni sustituto de la
   autorización humana.

## Recomendación de distribución y versionado

Autorizar un piloto interno con distribución local fijada y dos equipos
voluntarios. No crear una release pública ni distribución corporativa amplia
hasta resolver los tres bloqueantes anteriores. La siguiente decisión de
dirección técnica debe aprobar o rechazar ese piloto, definir el propietario de
la fuente/versionado remoto y aceptar explícitamente el modelo de autorización
formal requerido.

## Limpieza y consolidación

**Resultado: CLEANUP_NOT_REQUIRED para archivos versionados.** Se revisaron
209 archivos versionados en los tres repositorios: 85 en el framework, 61 en
el laboratorio Java y 63 en el laboratorio Angular. No se eliminó ningún
archivo versionado porque cada candidato documentado pertenece a una capacidad
vigente, una prueba de regresión, una política/lock activa, un contrato/schema,
una matriz de trazabilidad, un ADR o evidencia final de milestone.

### Residuos regenerables eliminados

Se eliminaron únicamente archivos no versionados e ignorados:

| Repositorio | Residuos eliminados | Justificación |
| --- | --- | --- |
| Framework | `.DS_Store`, `__pycache__`, `.pyc`, `.bootstrap-test-tmp`, cachés pytest/egg-info de fixture FastAPI | Cachés de intérprete, fixtures temporales y metadatos del sistema, regenerables por pruebas. |
| Java lab | `.DS_Store` y `target/` | Metadatos del sistema y salida Maven regenerable. |
| Angular lab | `.DS_Store`, `.angular/`, `dist/`, videos Cypress | Cachés/builds/videos de ejecución regenerables; `node_modules/` se conserva como dependencia activa local no versionada. |

### Elementos preservados deliberadamente

- Fixtures React/FastAPI bajo `tests/fixtures/`: demuestran y validan M5.
- Contratos M2, schemas, skills, agentes, instrucciones, validadores,
  instalador y bootstrap: forman parte del producto distribuible.
- Locks, políticas de cliente y propuestas locales: sostienen M4 y la
  reproducibilidad del consumo.
- Reportes M2–M5, matrices, ADR y vistas 4+1: evidencia histórica vigente,
  no documentación provisional.

No se corrigieron referencias: la búsqueda de referencias confirmó que los
ejemplos, outputs y mockups siguen cubiertos por validadores o contratos.

### Integridad posterior

- Framework: `unittest discover -s tests -v` — PASS, 126 pruebas.
- Java: `mvn -q -DskipTests compile` — PASS; lock y política vigentes.
- Angular: typecheck app/tests y build — PASS; lock transversal sin
  `java-base` y política vigente.
- Perfiles `java-spring`, `angular`, `react` y `python-fastapi` — PASS en
  resolución; no se afectaron políticas, locks ni migraciones.
- Los tres worktrees quedaron limpios después de retirar los artefactos
  generados por estas validaciones.
