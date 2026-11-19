# Contratos M2 para frontend unitario

## Propósito y alcance

M2 define contratos para transformar una especificación funcional, un mockup HTML autocontenido y casos YAML de pruebas unitarias en implementaciones verificables para consumidores Angular y React. M2 se limita a pruebas unitarias de frontend.

M2 permite DOM simulado, Angular TestBed y React Testing Library cuando sean compatibles con el consumidor. M2 no incluye navegador real, navegación E2E, Cypress, HTTP externo, automatización funcional, SAST, DAST ni pruebas de seguridad. Cypress pertenece a M3.1 y las pruebas de seguridad pertenecen a M3.2.

Los contratos son:

1. `frontend-ui-input/v1` para fuentes, alcance y contexto de consumidor.
2. `frontend-unit-tests/v1` para casos unitarios independientes del stack.
3. `frontend-ui-output/v1` para cambios, trazabilidad y evidencia real.
4. `authorization-trust/v1` para la política auxiliar externa de principals,
   claves públicas SSH, alcance y fingerprints revocados.

Los ejemplos de [customer-profile](../examples/customer-profile/) son plantillas ilustrativas. Sus hashes de los archivos de entrada locales se calcularon desde bytes reales; los commits, versiones de consumidores y autorizaciones que requerirían repositorios externos se marcan como `not-verified`. Por ello no son manifiestos listos para ejecución.

## Convenciones comunes

- `schemaVersion` y `featureId` son obligatorios.
- Los IDs son únicos y estables dentro de una feature: `REQ-*`, `SCR-*`, `CMP-*`, `UT-*`, `AMB-*`, `INF-*` y `DEC-*`.
- Las rutas usan `/` y se resuelven de forma determinista: `functionalSpecification.path`, `mockups[].path`, `assets[].path`, `unitTests.path` y `files[].path` son relativas al directorio que contiene el manifiesto `frontend-ui-input/v1`; `consumer.repositoryRoot` también es relativa a ese mismo directorio y resuelve la raíz del repositorio consumidor. Las rutas internas del consumidor (`consumer.detection.*Path`, `baseline.snapshotPath`, `scope.allowedPaths` y `scope.protectedPaths`) son relativas a `consumer.repositoryRoot`.
- El validador normaliza y resuelve cada ruta antes de usarla. Se rechazan rutas absolutas, segmentos `.` o `..`, separadores duplicados, glob, regex, URI y rutas que atraviesen symlinks.
- Los hashes se expresan como `sha256:<64-hex>` y se calculan desde bytes reales. No se declaran como verificados si no pueden calcularse.
- El mockup HTML aporta estructura visual y semántica; no autoriza reglas de negocio.
- Un requisito puede ser `confirmed`; una falta de información es `ambiguity`; una interpretación es `inference`; una excepción o interpretación implementable requiere `authorizedDecision` verificable.

## 1. `frontend-ui-input/v1`

### Propósito

El manifiesto de entrada vincula la feature con una especificación funcional, mockups, assets opcionales, contrato OpenAPI aprobado cuando exista, casos YAML unitarios, consumidor concreto, baseline Git y alcance autorizado.

### Campos normativos

| Campo | Regla |
| --- | --- |
| `schemaVersion` | Debe ser exactamente `frontend-ui-input/v1`. |
| `featureId` | ID estable de la feature. |
| `templateStatus` | `ready-for-execution` solo cuando todos los hechos externos sean verificables; los ejemplos usan `illustrative-not-ready-for-execution`. |
| `consumer` | Declara `stack: angular` o `stack: react`, rutas de manifest/lockfile, versiones detectadas y estado de verificación. |
| `baseline` | Declara commit, estado inicial requerido y ruta del snapshot pre-ejecución. |
| `scope` | Contiene `allowedPaths`, `protectedPaths` y política explícita de eliminación. |
| `functionalSpecification`, `mockups`, `unitTests` | Referencias relativas con hash real de cada archivo local. |
| `requirements` | Separa confirmados, ambigüedades, inferencias y decisiones autorizadas. |
| `conceptualComponents` | Modelos conceptuales independientes del framework. |

Un contrato OpenAPI se declara como referencia inmutable cuando existe. M2 no lo modifica.

### Estado de versiones de consumidor

Una versión Angular o React es verificable solo cuando un validador puede inspeccionar el `package.json`, lockfile y resolución aplicable del consumidor real. Un rango semver no demuestra por sí solo una versión instalada. Si no existe consumidor real, los valores deben ser `not-verified`, con una razón explícita.

### Autorizaciones verificables

Una fecha y un nombre de aprobador dentro del YAML no son evidencia suficiente. Una `authorizedDecision` puede implementarse únicamente si el validador independiente verifica una de estas evidencias:

- pull request aprobada, con repositorio, número, review aprobada, commit y referencia explícita al `DEC-*`;
- commit firmado y aceptado por la política del repositorio, con referencia explícita al `DEC-*`;
- registro corporativo inmutable accesible al validador, con estado aprobado, alcance y referencia al `DEC-*`;
- tag o release aprobado, resoluble a un commit y relacionado con el `DEC-*`.

La evidencia debe existir, no estar revocada y autorizar el cambio exacto. Si no se puede consultar o verificar, el manifiesto permanece `BLOCKED`. No existe bypass.

## 1.1 `authorization-trust/v1`

### Propósito y límites

`authorization-trust/v1` es una política auxiliar que declara, para un
consumidor esperado, los principals, claves públicas SSH, features, decisiones
y requisitos que cada principal puede autorizar. También declara fingerprints
SSH revocados. Es un documento de custodia externa: no forma parte de
`frontend-ui-input/v1`, no puede incluirse como entrada inventariada de una
feature y el manifest no puede elegir libremente sus aprobadores.

El contrato valida únicamente su forma: rutas absolutas con segmentos
normalizados, IDs, unicidad, ausencia de comodines y formato declarado de clave pública SSH. No
certifica la validez criptográfica de `publicKey`, la identidad del custodio,
la firma de un commit, el alcance efectivo, la ubicación externa de la policy,
la canonicalización efectiva de la ruta, la resolución de symlinks
ni una revocación verificable. No admite claves privadas, secretos, nombres,
emails o fechas como mecanismos de autorización por sí solos.

La canonicalización efectiva, la resolución de symlinks y la frontera de
confianza, junto con la verificación de ubicación externa, clave y principal
confiables, firma, alcance y revocación, se incorporarán en incrementos
posteriores. Por tanto,
`authorization-trust/v1` no altera `SEM-AUTH-001` ni permite todavía declarar
una decisión autorizada para PREPARE.

## 2. `frontend-unit-tests/v1`

### Propósito

El contrato define intención de pruebas unitarias sin imponer APIs Angular o React. Cada caso tiene `id`, `title`, `requirementIds`, `componentIds`, `priority`, `target`, `preconditions`, `mocks`, `input`, `action`, `expected`, `classification`, `async` e `isolation`.

Los valores habituales de `target.type` son `component`, `hook`, `service`, `utility`, `validator`, `state` y `adapter`. `other` requiere una justificación explícita.

### Reglas unitarias

- Las pruebas son deterministas, aisladas y no dependen del orden.
- Las dependencias externas se sustituyen por mocks, stubs, spies o fakes locales.
- Se permite renderizar componentes en DOM simulado.
- Angular puede usar TestBed cuando la unidad requiera configuración Angular.
- React puede usar Testing Library cuando sea compatible con el proyecto.
- Se excluyen HTTP externo, navegador real, navegación E2E, Cypress y automatización funcional.
- Las pruebas asíncronas declaran mecanismo, estrategia de temporizadores o scheduler, condición de finalización y limpieza.
- La cobertura de líneas no sustituye el vínculo requisito→caso→prueba técnica.

## 3. `frontend-ui-output/v1`

### Propósito

El contrato de salida registra datos observados después de una ejecución: snapshots, cambios atribuibles, matriz de trazabilidad, comandos, resultados y artefactos. No puede declarar éxito sin evidencia.

### Estados de evidencia

| Estado | Significado |
| --- | --- |
| `GENERATED` | Se generaron artefactos; no implica compilación ni ejecución. |
| `COMPILED` | Build o typecheck terminó correctamente con comando, código de salida y evidencia reales. |
| `TESTED` | Pruebas unitarias ejecutadas con comando, resultado verificable y alcance conocido. |
| `VALIDATED` | Los criterios aplicables tienen evidencia suficiente; no se infiere de coverage o tests aislados. |
| `NOT_RUN` | Comprobación aplicable no ejecutada. |

### Estados de workflow

| Estado | Significado |
| --- | --- |
| `READY_FOR_IMPLEMENTATION` | Entradas, autorización verificable y alcance están preparados; todavía no hay implementación. |
| `READY_FOR_VALIDATION` | Hay cambios dentro de alcance y faltan una o más validaciones. |
| `BLOCKED` | Hay ambigüedad sin autorización, autorización no verificable, alcance no íntegro, cambios concurrentes o cualquier cambio fuera de alcance. |

Los estados de evidencia y workflow son independientes. Un cambio de alcance no autorizado siempre exige `BLOCKED`.

## Protección de alcance

### Rutas permitidas y protegidas

`allowedPaths` indica los únicos archivos o directorios que pueden cambiar. `protectedPaths` indica archivos o directorios que nunca pueden cambiar para ese manifiesto.

El solapamiento es válido para proteger un archivo específico dentro de una carpeta autorizada. La precedencia es absoluta:

```text
protectedPaths > allowedPaths
```

Por ejemplo, si se permite `src/features/customer-profile` pero se protege `src/features/customer-profile/validator.ts`, crear un componente hermano puede permitirse; modificar, eliminar o renombrar el validador se rechaza.

### Semántica por cambio

| Cambio | Requisito para permitirlo |
| --- | --- |
| Nuevo | Destino permitido, no protegido, archivo regular y sin symlink en ancestros. |
| Modificado | Ruta permitida, no protegida y tipo preservado. |
| Eliminado | Ruta permitida, no protegida y `deletionPolicy.allowed: true` con autorización verificable. |
| Renombrado | Origen y destino permitidos, no protegidos y tipo preservado. |
| Cambio de tipo | Rechazado por defecto. |
| Symlink o submódulo | Rechazado por defecto. |
| Conflicto Git | Rechazado siempre. |

No se admiten wildcards, glob ni expresiones regulares en el alcance. Una excepción requiere un manifiesto nuevo, versionado y una `authorizedDecision` verificable; no existe bypass.

## Snapshots Git y atribución

Un validador ejecutable e independiente de Copilot debe capturar un snapshot pre-ejecución y otro post-ejecución. El snapshot contiene al menos:

- `HEAD` y árbol Git del baseline;
- cambios staged respecto a `HEAD`;
- cambios unstaged respecto al índice;
- archivos no rastreados no ignorados, con tipo y hash si son archivos regulares;
- renames, eliminaciones y cambios de tipo;
- resolución de rutas gobernadas para detectar symlinks;
- instante de captura y manifiesto de hashes de archivos rastreados cuando aplique.

El conjunto atribuible se calcula comparando el snapshot final con el snapshot inicial aprobado:

```text
attributableChanges = finalRepositoryState - approvedInitialRepositoryState
```

El validador distingue `preExistingChanges`, `attributableChanges`, `concurrentChanges` y `scopeViolations`.

### Repositorios con cambios preexistentes

La política predeterminada requiere árbol limpio: sin staged, unstaged, no rastreados relevantes, conflictos ni cambios de tipo. Si el repositorio no inicia limpio, es `BLOCKED`.

Solo puede continuar si existe un snapshot inicial verificable y aprobado externamente que enumere y hashee los cambios preexistentes, mantenga `HEAD` e índice, no intersecte rutas permitidas, protegidas ni de evidencia, y pueda validarse contra una fuente independiente. Si no se puede demostrar esa separación, permanece `BLOCKED`.

### Cambios concurrentes

Si `HEAD`, índice, hashes, rutas, renames, eliminaciones o tipos cambian fuera de los cambios atribuibles esperados entre snapshots, el validador declara cambio concurrente y devuelve `BLOCKED`. Un cambio concurrente hace imposible demostrar la integridad del alcance.

## Reglas de trazabilidad

Cada requisito unit-testable debe enlazarse con:

```text
requisito → componente conceptual → caso YAML → prueba técnica del consumidor → resultado → evidencia
```

La presentación del campo también requiere un caso YAML: en el ejemplo es `UT-CUSTOMER-PROFILE-001-01`. Angular y React mantienen matrices separadas porque sus unidades y pruebas técnicas son distintas, aunque consuman los mismos requisitos y casos YAML.

Un requisito sin caso debe reportarse. Una prueba técnica sin requisito debe reportarse. Si una validación no fue ejecutada, su resultado debe ser `NOT_RUN`; nunca se infiere éxito.

## Validación estructural y semántica

Se recomienda JSON Schema Draft 2020-12 para validar estructura YAML interpretada como JSON: campos obligatorios, tipos, enums, patrones de ID, hashes, arrays y forma de evidencias.

Un validador semántico independiente valida hechos reales: hashes de archivos, rutas/symlinks, Git, snapshots, cambios concurrentes, referencias, autorizaciones externas, alcance efectivo y consistencia de estados. JSON Schema no sustituye esta segunda capa.

## Errores esperados

| Código | Condición |
| --- | --- |
| `INPUT-003` | Ruta absoluta, traversal o patrón ambiguo. |
| `INPUT-007` | Hash de entrada no coincide con bytes reales. |
| `INPUT-011` | Versión de stack no verificable en un manifiesto marcado listo para ejecución. |
| `INPUT-014` | Autorización sin evidencia externa verificable. |
| `UNIT-004` | Caso sin requisito o componente relacionado. |
| `UNIT-011` | HTTP externo en prueba unitaria. |
| `UNIT-012` | Navegador real, navegación E2E o Cypress en M2. |
| `UNIT-013` | Prueba asíncrona sin control determinista. |
| `SCOPE-008` | Cambio fuera de `allowedPaths`. |
| `SCOPE-009` | Cambio dentro de `protectedPaths`. |
| `SCOPE-010` | Rename con origen o destino no autorizado. |
| `SCOPE-011` | Cambio de tipo, symlink o submódulo no autorizado. |
| `OUTPUT-008` | `TESTED` sin comando, resultado y evidencia. |
| `OUTPUT-011` | Violación de alcance sin workflow `BLOCKED`. |
| `OUTPUT-012` | `VALIDATED` con validaciones obligatorias pendientes. |

## Cobertura

La cobertura se mide solo cuando el runner del consumidor la soporta. Cada consumidor define y versiona sus métricas, alcance, exclusiones, umbrales y política de no regresión. No existen porcentajes universales. La cobertura no demuestra por sí misma satisfacción de requisitos ni permite declarar `VALIDATED`.

## Validación pendiente

Esta documentación no crea JSON Schemas, validador, consumidores, dependencias ni pruebas. Es material de diseño y ejemplos para auditoría humana antes de M2.1B.
