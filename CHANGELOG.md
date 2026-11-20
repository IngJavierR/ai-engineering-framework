# Changelog

Los cambios se registran por versión preparada para publicación o
publicada. Una entrada sin fecha no implica que exista un tag, release
ni artefacto publicado.

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