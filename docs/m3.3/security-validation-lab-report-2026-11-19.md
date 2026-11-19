# M3.3 — Security Validation

## Resumen ejecutivo

Se revisaron por separado dos laboratorios locales: Angular Customer Profile y
Customers API Java. La evidencia no representa una aplicación integrada, un
pentest, ni una certificación formal. Se documentaron tres hallazgos de nivel
medio: uno en dependencias de desarrollo Angular y dos riesgos de configuración
Java que requieren atención antes de una publicación no local.

## Cobertura

| Aplicación | Commit | Stack | Resultado |
| --- | --- | --- | --- |
| Angular Customer Profile | `735e962` | Angular 21.2.26, TypeScript | 1 hallazgo medio; 0 advisories en dependencias de producción. |
| Customers API | `ec56826` | Java 21, Spring Boot, PostgreSQL, Liquibase | 2 riesgos medios de configuración. |

Los informes y salidas JSON de cada consumidor son la fuente de detalle:

- [Angular Markdown](../../../labs/angular-customer-profile-consumer/docs/m3.3/security-review.md)
  y [JSON](../../../labs/angular-customer-profile-consumer/docs/m3.3/security-findings.json).
- [Java Markdown](../../../ai-engineering-java-lab/docs/m3.3/security-review.md)
  y [JSON](../../../ai-engineering-java-lab/docs/m3.3/security-findings.json).

## Resultados por severidad

| Crítica | Alta | Media | Baja | Informativa |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 3 | 0 | 0 |

## Capacidad y contrato

La skill [security-validation](../../.github/skills/security-validation/SKILL.md)
define una revisión reutilizable por alcance, amenazas, evidencia y hallazgos.
El contrato neutral [security-findings/v1](security-findings.v1.schema.json)
permite que un reportador independiente consuma las salidas sin acoplarse al
stack del laboratorio.

## Límites

No hubo SAST ni scanner de advisories Java instalado localmente. No se evaluaron
producción, terceros, TLS/proxy, proveedores de identidad ni gestores de
secretos. Las comprobaciones dinámicas se limitaron a rutas inocuas del
laboratorio Java local. Las recomendaciones se mantienen separadas de cambios
funcionales y no se aplicaron remediaciones automáticamente.

**M3.3 DEVELOPMENT / LAB: COMPLETED.** La certificación formal de seguridad no
se ejecutó ni se representa como aprobada.
