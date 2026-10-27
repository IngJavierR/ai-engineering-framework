# Changelog

Los cambios se registran por versión preparada para publicación o
publicada. Una entrada sin fecha no implica que exista un tag, release
ni artefacto publicado.

## [0.3.0] - Preparada para publicación

No existe todavía un tag, release ni artefacto publicado para esta
versión.

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