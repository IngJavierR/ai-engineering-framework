# M4 — Evidencia de distribución y políticas

## Consumidores demostrados

| Consumidor | Política de ejemplo | Capacidades explícitas | Capacidades ausentes |
| --- | --- | --- | --- |
| `ai-engineering-java-lab` | `example-client-a-java` | `gatling-performance`, `security-validation` | Angular UI, Cypress |
| `angular-customer-profile-consumer` | `example-client-b-angular` | `angular-ui-implementation`, `cypress-functional-testing`, `security-validation` | Gatling |

Ambos locks registran framework `0.4.0` y el mismo commit de fuente
`883d77a60a9eb0cb1083b34fd77b9d428a5e6475`. Las políticas se almacenan dentro
de cada consumidor y no hay configuración mutable compartida.

## Operaciones verificadas

- Java: adopción explícita de artefactos sin lock mediante
  `--replace-framework-artifacts`, seguida de reinstalación idempotente.
- Angular: actualización controlada desde el lock histórico a las capacidades
  autorizadas, seguida de reinstalación idempotente.
- Conflicto: pruebas de bootstrap verifican que artefactos no administrados y
  políticas existentes divergentes se bloquean sin flags explícitos.
- Propuesta: cada consumidor contiene `proposal.json` y `PR_UPDATE.md` con una
  rama propuesta y `requiresHumanReview: true`; no se hizo push ni PR remoto.

## Validación local

`tests.test_bootstrap` cubre bootstrap, dry-run, adopción explícita,
idempotencia, política aislada, conflicto y propuesta sin acceso remoto. La
suite completa del framework se ejecuta como evidencia de cierre.

**M4 LOCAL DEMONSTRATION: COMPLETED.** La creación remota de Pull Request y la
publicación de releases permanecen fuera de esta validación local.
