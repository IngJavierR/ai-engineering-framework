# SPEC-CUSTOMER-PROFILE-001 — Edición de perfil de cliente

## Objetivo

Permitir que una persona usuaria edite y valide localmente el nombre visible de un perfil de cliente.

## Alcance

La feature comprende el formulario y la validación local del nombre visible. No comprende autenticación, autorización, navegación entre rutas, persistencia remota, solicitudes HTTP ni pruebas funcionales automatizadas.

## Requisitos confirmados

### REQ-CUSTOMER-PROFILE-001-01 — Presentación del campo

El formulario debe mostrar un campo de texto etiquetado como **Nombre visible**.

**Criterio verificable:** una prueba unitaria de componente, ejecutada en un entorno DOM simulado compatible con el consumidor, encuentra un control con nombre accesible «Nombre visible».

### REQ-CUSTOMER-PROFILE-001-02 — Validación de nombre visible

El nombre visible es obligatorio y debe contener entre 2 y 50 caracteres después de aplicar las decisiones autorizadas de normalización.

**Criterios verificables:**

- Un valor normalizado de 2 a 50 caracteres es válido.
- Un valor que queda vacío después de normalizar espacios externos es inválido con el error `required`.
- La unidad de validación no realiza solicitudes HTTP ni accede a servicios externos.

## Ambigüedad

### AMB-CUSTOMER-PROFILE-001-01 — Espacios externos

La especificación no determina si los espacios iniciales y finales forman parte del nombre ni de su longitud. El mockup no resuelve esta ambigüedad y no puede utilizarse para inventar esa regla.

## Decisión requerida para ejemplos

Los manifiestos ilustrativos declaran `DEC-CUSTOMER-PROFILE-001-01`: eliminar espacios iniciales y finales antes de validar. La decisión está marcada como **no verificada** porque este repositorio no contiene un commit, una pull request aprobada ni otra evidencia independiente que la autorice.

Por tanto, los manifiestos son plantillas ilustrativas y no están listos para ejecución.

## Límite de pruebas M2

Las pruebas M2 son unitarias de frontend. Pueden usar DOM simulado, Angular TestBed o React Testing Library cuando sean compatibles con el proyecto consumidor. Se excluyen navegador real, navegación E2E, Cypress, HTTP externo, pruebas funcionales automatizadas y pruebas de seguridad.
