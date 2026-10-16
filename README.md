
# AI Engineering Framework

Framework centralizado y versionado para estandarizar
el desarrollo de software asistido por GitHub Copilot.

## Objetivo

Establecer prácticas de ingeniería reutilizables,
verificables y adaptables a distintos proyectos
y clientes.

## Estado

Versión: 0.1.0
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
