# Changelog

Los cambios se registran por versión preparada para publicación o
publicada. Una entrada sin fecha no implica que exista un tag, release
ni artefacto publicado.

## [0.8.0-rc.1] - En preparación

### Cambiado (incompatible)

- B1: DDD con límites hexagonales es obligatorio para todo backend. La nueva
  skill `backend-ddd-architecture` define capas, regla de dependencias, bounded
  contexts y validación neutral al stack; `api-contract-first`,
  `fastapi-development` y `java-spring-development` dependen de ella.
- B2: `.github/instructions/java.instructions.md` se reemplaza por la skill
  `java-spring-development`. `openapi-to-ddd/references/ddd-structure.md` pasa
  a `java-spring-development/references/ddd-layout.md`.
- B3: `fastapi-development` adopta DDD con `references/ddd-layout.md`.
- B4: `openapi-ddd` y `liquibase` dejan de aplicarse por `**/*.java`; se
  activan solo por contratos y changelogs. La gobernanza universal incorpora
  DDD backend y Liquibase obligatorio.
- B5: los consumidores con locks que contienen los artefactos retirados deben
  actualizar con `--upgrade --migrate-stack`.

### Corregido

- B6: `validate_lock` ya no rechaza como "internally inconsistent" un lock
  válido cuando el inventario actual cambió los artefactos de una capacidad; la
  consistencia se verifica contra el inventario del commit del lock.
- B7: `source_manifest()` resuelve la capacidad base actual en lugar del
  manifiesto histórico v0.3.0.

## [0.7.0-rc.5] - En preparación

### Corregido

- C1: `ignored_defaults.py` usa `git ls-files` en lugar de recorrido en disco para detectar
  archivos versionados; los caches y venvs no descartaron más patrones por defecto.
- C2: `.env` y `.env.local` se agregan como patrones universales en todos los stacks.
- C3: `pom.xml` bajo `performance/gatling/` activa únicamente el stack `gatling`, no `java`.
- C4: VERIFY ejecuta la comprobación de rama Git antes que las validaciones de contenido;
  `GIT-003` incluye la rama esperada y la actual.
- C5: la salida JSON del workflow backend no contiene vocabulario `frontend`.
- C6: los quickstarts tienen un bloque `Preparación`, usan `app` como nombre de consumidor,
  `$FW/tools/...` para todos los comandos y `RECEIPT=$(ls -t ...)` para el receipt.
- C7: prueba de onboarding reescrita con fixture monorepo completo y flujo backend completo.
- C8: `tools/release_gate.sh` verifica la suite, las pruebas lentas, el profile `java-spring`
  y la sección del CHANGELOG antes de emitir `RELEASE_GATE_PASS`.
- C9: `tests/test_regression_rc.py` verifica receipts RC4, lista de archivos `java-spring`
  y validación de ejemplos.

## [0.7.0-rc.4] - En preparación

### Corregido

- R1/R2: los defaults ignorados se detectan desde todos los stacks del
  consumidor y quedan anclados entre PREPARE y VERIFY.
- R3: los quickstarts usan una rama de feature y los cambios de rama identifican
  la rama esperada y la actual.
- R4/R6: el frontend monorepo prefija todo su alcance y los contratos en
  `--contract-dir` no se duplican fuera del consumidor.
- R5: el inventario de ignorados usa directorios y una comprobación Git por lote.
- R7: el quickstart backend unifica evidencia/custodia y versiona el contrato.
- R8: la referencia Compose de Liquibase usa imagen construida, healthcheck y
  variables de entorno sin credenciales literales.
- R9: el workflow backend mantiene vocabulario backend en su salida.

## [0.7.0-rc.3] - En preparación

### Añadido

- Perfil genérico `backend` y composición contract-first reutilizable para
  Java Spring, FastAPI y otros servicios REST.
- Esquemas `backend-service-input/v1` y `backend-test-cases/v1`, ejemplo
  `customer-api`, scaffold y validador local de OpenAPI, casos, Liquibase y
  escenarios Gatling.
- Quickstart backend y referencia única para diseñar casos backend.

### Cambiado

- OpenAPI, Liquibase y Gatling se distribuyen como capacidades neutrales;
  `java-base` conserva sus artefactos para verificar locks existentes.
- FastAPI adopta contrato aprobado como fuente de verdad y Liquibase para
  cambios estructurales.

### Corregido

- H1: `--consumer` se resuelve de forma uniforme desde el directorio actual.
- H2: el scaffold no ensucia el consumidor y refresh informa árboles sucios.
- H3: los artefactos ignorados declarados no bloquean PREPARE/VERIFY.
- H4: VERIFY evalúa commits descendientes de la base dentro del alcance.
- H5: Gatling analiza solo fuentes/configuración y no namespaces Maven.
- H6: la plantilla backend contiene respuesta 404 y caso negativo coherente.
- H7: VERIFY requiere changesets y simulaciones que referencien escenarios.
- H8: el scaffold frontend admite `--frontend-root` para monorepos.
- H9: el workflow backend informa `backendEvidence` y sus límites reales.

## [0.6.0-rc.1] - Release candidate local, no publicada

Mejoras de ergonomía y seguridad de instalación posteriores a `v0.5.0-rc.1`.
No existe tag, release ni artefacto publicado para esta versión.

### Añadido

- Instalación multi-stack mediante perfiles repetibles y combinación explícita
  de perfiles/capacidades también desde bootstrap, sin introducir Java en
  Angular, React o FastAPI.
- `make_anchor.py`, `new_feature.py` y `refresh_manifest.py` para preparar
  insumos M2, hashes, metadatos de consumidor y anchors verificables.
- Quickstart de Copilot con secuencia M2, dependencias de validación, prompts y
  explicación de `VERIFY`.

### Corregido

- Globs de instrucciones Java limitados a Java y recursos Java para evitar que
  rutas comunes de Python/TypeScript reciban gobierno Java.
- La unión aditiva de perfiles durante upgrade conserva capacidades existentes;
  la eliminación sigue requiriendo migración explícita de stack.

### Diferido

- La verificación criptográfica de `authorizedDecisions` permanece fail-closed
  (`SEM-AUTH-001`) hasta disponer de una política de confianza y firmas reales.

## [0.5.0-rc.1] - Release candidate local, no publicada

La primera release candidate reúne las capacidades MVP–M5 para un piloto
interno controlado. No existe aún el tag `v0.5.0-rc.1`, GitHub Release ni
artefacto publicado.

### Añadido

- Gobierno transversal y perfiles explícitos `java-spring`, `angular`,
  `react` y `python-fastapi`, sin imponer artefactos Java a stacks no Java.
- Capacidades React, FastAPI, Cypress, Gatling y validación de seguridad.
- `bootstrap.py`, políticas aisladas por cliente, propuestas locales de
  actualización y protección explícita frente a conflictos.
- Reportes de rendimiento, arquitectura 4+1, ADR, trazabilidad funcional y
  seguridad para laboratorios autorizados.
- Contrato neutral `security-findings/v1` y evaluación de preparación
  corporativa `READY_WITH_LIMITATIONS`.

### Compatibilidad y actualización

- Los locks `v0.2.0`, `v0.3.0` y `capability-lock/v1` existentes siguen
  verificándose mediante la ruta de upgrade controlada.
- Las migraciones desde locks heredados basados en `java-base` requieren
  `--migrate-stack`; no se eliminan artefactos ni capacidades implícitamente.
- Se recomienda un `--dry-run` con fuente limpia y revisión humana antes de
  cualquier adopción, reemplazo de política o migración de stack.

### Limitaciones conocidas

- La fuente/versionado remoto firmado, Pull Requests remotos y la autorización
  formal M2 no se han demostrado en esta release candidate.
- Gatling, Cypress, Playwright y seguridad tienen evidencia de laboratorio;
  no constituyen certificación de producción.

## [0.4.0] - Experimental, en preparación

No existe todavía un tag, release ni artefacto publicado para esta
versión.

### Distribución por capacidades

- Java base permanece obligatorio con ocho archivos gestionados.
- `frontend-ui-design` se instala solo mediante selección explícita.
- `angular-ui-implementation` y `react-ui-implementation` resuelven la
  dependencia compartida `frontend-ui-design` una sola vez.
- Los perfiles resueltos gestionan 8, 12, 16, 16 o 20 archivos para base,
  diseño, Angular, React y Angular+React, respectivamente.

### Lock e integridad

- Nuevo lock `capability-lock/v1` con capacidades resueltas deterministas,
  commit de origen y hashes SHA-256 de cada artefacto.
- Reinstalación idempotente y upgrades explícitos, aditivos y verificables.
- Compatibilidad de upgrade verificable desde locks históricos `v0.2.0` y
  `v0.3.0`, junto con verificación del commit, identidad histórica,
  inventario, manifest y contenido de artefactos.
- Protección contra modificaciones locales, conflictos no gestionados,
  symlinks, rutas inseguras y eliminaciones implícitas.

## [0.3.0] - Publicada

El tag `v0.3.0` existe y permanece inmutable.

### Instrucciones y skills

- Reglas consolidadas para conformidad OpenAPI con HTTP real,
  compatibilidad backward/forward, DDD, Liquibase XML, preservación de
  datos y evidencia de validación.
- Dos skills y sus tres referencias reforzadas para planificación,
  compatibilidad de contratos y versionado estructural.

### Distribución de ocho archivos

- Distribución de tres instrucciones Java y dos skills con sus tres
  referencias, para un total de ocho archivos gestionados.
- Instalación limpia, dry-run y repetición idempotente.
- Lock con manifest, commit de origen y hashes SHA-256 calculados desde
  archivos reales.

### Upgrade explícito desde v0.2.0

- Las actualizaciones requieren `--upgrade` y una instalación v0.2.0
  verificable; no hay upgrades silenciosos.
- El instalador rechaza conflictos con archivos del consumidor y no
  sobrescribe cambios locales en archivos gestionados.
- La recuperación ante fallos manejables conserva respaldos hasta que la
  publicación de archivos y lock concluye correctamente.

### Pruebas unitarias

- 14 pruebas automatizadas del instalador ejecutadas y aprobadas durante
  R2.3.
- Instalación limpia end-to-end, upgrade desde v0.2.0, idempotencia y
  protección de modificaciones locales verificados contra la línea base
  `1254d1067be22ad1be7b11fbfce4e04a03be76a7`.

### Limitaciones y validación funcional futura

La validación funcional de OpenAPI, DDD y Liquibase XML fue realizada durante M1 sobre el laboratorio Java, con 40 pruebas automatizadas exitosas, incluidas pruebas de contrato HTTP y migración incremental sobre PostgreSQL con datos preexistentes.

La versión 0.3.0 también superó las pruebas de instalación, actualización desde v0.2.0, idempotencia e integridad de artefactos distribuidos.

Permanece pendiente una validación funcional independiente que demuestre el comportamiento de GitHub Copilot utilizando las skills actualizadas y distribuidas por v0.3.0 en un consumidor nuevo.

El framework todavía no incorpora quality gates generales automatizados y no ofrece atomicidad global de instalación ante interrupciones abruptas.

## [0.2.0]

### Añadido

- Instrucción Java distribuible mediante instalación central versionada.
- Skills e instrucciones de OpenAPI/DDD y Liquibase XML disponibles en
  el repositorio central.

### Limitaciones

- El instalador distribuía únicamente la instrucción Java.
- No existía un upgrade automático para instalaciones anteriores.