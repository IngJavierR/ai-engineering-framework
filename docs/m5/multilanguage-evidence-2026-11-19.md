# M5 — Evidencia multilenguaje

## Arquitectura

`universal-governance` contiene reglas transversales de alcance, evidencia,
seguridad y dependencias. `java-base` se conserva para compatibilidad de locks
históricos y solo se recibe a través del perfil `java-spring`. Los perfiles
Angular, React y FastAPI resuelven desde la base transversal sin artefactos
Java.

## Matriz demostrada

| Perfil | Gobierno | Especialización | Artefactos Java | Resultado |
| --- | --- | --- | --- | --- |
| Java Spring | Universal + Java | OpenAPI/DDD/Liquibase heredados, Gatling, seguridad | Sí | `mvn -q -DskipTests compile` PASS |
| Angular | Universal | Angular UI, Cypress, seguridad | No después de migración | typecheck y build PASS |
| React fixture | Universal | React UI, Cypress, seguridad | No | TypeScript build y Vitest PASS |
| FastAPI fixture | Universal | FastAPI, seguridad | No | pytest/OpenAPI/Pydantic PASS |

## Migración Angular

El consumidor Angular partía de un lock heredado que incluía `java-base`.
`bootstrap.py --profile angular --migrate-stack` verificó el lock existente,
retiró solo instrucciones/skills Java administradas y registró
`universal-governance` como base del lock. No se modificó código funcional,
dependencias npm ni configuración Angular.

## Fixtures técnicos

- React: componente funcional TypeScript `Status` y una prueba Vitest.
- FastAPI: `POST /echo` con Pydantic, validación 422, error 403 y
  disponibilidad de `/openapi.json`.

Los fixtures viven bajo `tests/fixtures/`, se instalan en directorios temporales
Git y no son aplicaciones de negocio ni repositorios permanentes.

## Limitaciones

FastAPI emitió un warning de deprecación en `TestClient` de la combinación
actual FastAPI/Starlette; las pruebas pasaron. Los perfiles no seleccionan
herramientas de migración de base de datos para Python: cada consumidor debe
usar su gobierno de migraciones aprobado.
