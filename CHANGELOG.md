# Changelog

Los cambios se registran por versión candidata o publicada. Una entrada
marcada como candidata no implica que exista un tag, release ni artefacto
publicado.

## [0.3.0] - Candidata no publicada, pendiente de release

No existe todavía un tag, release ni artefacto publicado para esta
versión candidata.

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

### Validación pendiente para R3

- Esta candidata no se ha validado end-to-end en un consumidor.
- No existen quality gates automatizados generales del framework.
- No hay atomicidad global ante `SIGKILL`, apagados o fallos del sistema
  de archivos durante una instalación o upgrade.

## [0.2.0]

### Añadido

- Instrucción Java distribuible mediante instalación central versionada.
- Skills e instrucciones de OpenAPI/DDD y Liquibase XML disponibles en
  el repositorio central.

### Limitaciones

- El instalador distribuía únicamente la instrucción Java.
- No existía un upgrade automático para instalaciones anteriores.