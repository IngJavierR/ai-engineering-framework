
# AI Engineering Framework

Framework centralizado y versionado para estandarizar
el desarrollo de software asistido por GitHub Copilot.

## Objetivo

Establecer prácticas de ingeniería reutilizables,
verificables y adaptables a distintos proyectos
y clientes.

## Estado

Versión: 0.2.0
Estado: Experimental

## Componentes

- AGENTS.md: contrato general de los agentes.
- .github/copilot-instructions.md:
  instrucciones para GitHub Copilot.
- framework.yaml: metadatos y versión.

## Alcance inicial

El framework comenzará con soporte para Java.

## Capacidades futuras

Las capacidades de agentes especializados,
skills, políticas de cliente y validaciones
automáticas se incorporarán progresivamente.

## Desarrollo

Cada etapa debe validarse antes de avanzar
a la siguiente.


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

## Instrucciones de ingeniería

### Java

Archivo:
`.github/instructions/java.instructions.md`

Alcance:
Archivos Java que coincidan con `**/*.java`.

Incluye:
- Buenas prácticas de diseño.
- Separación de responsabilidades.
- Reglas arquitectónicas.
- DDD cuando corresponda.
- Manejo de errores.
- Seguridad.
- Pruebas.
- Migraciones con Liquibase.
- Gestión de cambios.

Estas instrucciones son declarativas.
Todavía no existen validadores automáticos
que garanticen su cumplimiento.


## Distribución experimental

El framework puede instalar instrucciones Java
en repositorios Git independientes.

### Instalación

Desde el repositorio central:

```bash
python3 tools/install.py \
  --target ../java-framework-lab \
  --dry-run

python3 tools/install.py \
  --target ../java-framework-lab
```

### Alcance actual

- Distribución de instrucciones Java.
- Registro de versión y commit de origen.
- Prevención de sobrescrituras accidentales.
- Ejecución idempotente para una misma versión.

### Limitaciones

- No distribuye todavía agentes ni políticas.
- No actualiza automáticamente instalaciones anteriores.
- No fusiona cambios locales.
- No reemplaza validaciones de CI.

## M1 — OpenAPI + DDD + Liquibase XML

### Objetivo

Incorporar capacidades para construir y ampliar
APIs Java a partir de contratos OpenAPI, utilizando
Domain-Driven Design y manteniendo compatibilidad
con las funcionalidades existentes.

### Gobierno de base de datos

Todo cambio estructural de base de datos debe
estar versionado mediante Liquibase XML.

Esta regla incluye:
- Tablas y columnas.
- Índices y restricciones.
- Llaves primarias y foráneas.
- Vistas, secuencias, funciones y triggers.
- Cualquier otro objeto estructural.

No está permitido modificar la estructura de BD
mediante mecanismos externos a Liquibase.

Las operaciones normales sobre datos de negocio
no están sujetas a esta regla.

### Instrucciones disponibles

- `.github/instructions/openapi-ddd.instructions.md`
- `.github/instructions/liquibase.instructions.md`

### Estado

- Gobierno OpenAPI + DDD: definido.
- Gobierno Liquibase XML: definido.
- Skills especializadas: pendientes.
- Pruebas automatizadas de contrato: pendientes.
- Validación sobre PostgreSQL temporal: pendiente.

## M1 — Skill liquibase-versioning

Ubicación:
`.github/skills/liquibase-versioning/SKILL.md`

Primera skill especializada del framework.

### Responsabilidades

- Clasificar cambios estructurales de BD.
- Analizar impacto y compatibilidad.
- Generar changesets Liquibase XML.
- Preservar cambios previamente aplicados.
- Evaluar preconditions y rollback.
- Definir validaciones necesarias.

### Estado

- Definición de skill: implementada.
- Validación de comportamiento en Copilot:
  ejecutada durante M1.
- Distribución a proyectos consumidores: pendiente.
- Ejecución real sobre PostgreSQL: pendiente.
- Validación automatizada de cambiosets: pendiente.

Las reglas globales de Liquibase XML permanecen
definidas en las instrucciones del framework.

## M1 — Skill openapi-to-ddd

Ubicación:
`.github/skills/openapi-to-ddd/SKILL.md`

### Objetivo

Interpretar contratos OpenAPI y construir o
evolucionar APIs Java Spring Boot utilizando
Domain-Driven Design.

### Capacidades

- Analizar contratos OpenAPI.
- Distinguir proyectos nuevos y existentes.
- Identificar componentes y límites de dominio.
- Proponer arquitectura DDD con puertos y adaptadores.
- Analizar impacto sobre funcionalidades existentes.
- Identificar cambios estructurales de BD.
- Aplicar el gobierno Liquibase XML.
- Definir pruebas de contrato y regresión.
- Evaluar compatibilidad hacia atrás.

### Estado

- Skill definida y disponible en el repositorio.
- Pruebas de interpretación realizadas durante M1.
- Generación y compilación de API: pendiente.
- Validación real del contrato: pendiente.
- Pruebas sobre PostgreSQL: pendiente.
- Distribución a consumidores: pendiente.
