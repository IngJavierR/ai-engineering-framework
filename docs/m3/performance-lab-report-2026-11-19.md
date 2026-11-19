# M3 — Performance + Arquitectura 4+1

## Modalidad y objetivo

Evidencia **Development / Lab** ejecutada contra `ai-engineering-java-lab` en
`5df90f9`, con Spring Boot local `127.0.0.1:8080` y PostgreSQL 16.4 iniciado
por Docker Compose. No se dirigió tráfico a producción ni a terceros.

## Perfiles Gatling ejecutados

| Perfil | Carga | Requests | Errores | p95 | Throughput | Umbral |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| smoke | 1 usuario inmediato | 2 | 0 | 10 ms | 2 req/s | p95 <= 2 s; fallos <= 1 % |
| baseline | 4 usuarios / rampa 10 s | 8 | 0 | 16 ms | 1 req/s | p95 <= 3 s; fallos <= 1 % |
| stress | 12 usuarios / rampa 15 s | 24 | 0 | 15 ms | 1.714 req/s | p95 <= 5 s; fallos <= 1 % |

Los tres comandos `mvn -Pperformance gatling:test` terminaron con `BUILD
SUCCESS`. Gatling generó informes `index.html` bajo `target/gatling/`; dichos
artefactos están correctamente ignorados por Git y no se versionan.

La secuencia evaluada crea un cliente con email único y después lo recupera por
ID. Por tanto, el throughput describe el flujo completo POST+GET, no solamente
la lectura. Los resultados son límites de un equipo local desechable, no un SLO
ni una declaración de capacidad productiva.

## Arquitectura y decisiones

- Vistas lógica, de procesos, desarrollo, física y de escenarios: consultar
  [4+1 en el laboratorio Java](../../../ai-engineering-java-lab/docs/architecture/4plus1.md).
- ADR de perfiles y aislamiento local: consultar
  [ADR 0001](../../../ai-engineering-java-lab/docs/adr/0001-gatling-local-performance-profiles.md).
- La capacidad reutilizable está en
  `.github/skills/gatling-performance/` y se distribuye mediante el inventario
  `gatling-performance`.

## Estado

**M3 DEVELOPMENT / LAB: COMPLETED.**

No existe una certificación formal de gobierno o rendimiento productivo para
esta ejecución; la evidencia solo cubre el laboratorio local autorizado.
