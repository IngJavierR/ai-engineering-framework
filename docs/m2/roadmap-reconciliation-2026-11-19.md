# Reconciliación del roadmap y cierre de M2

## Alcance de la revisión

Se inspeccionaron el framework en `bfefae6` y el laboratorio
`angular-customer-profile-consumer` en `63d72e5`. Ambos worktrees estaban
limpios al inicio de la revisión. El framework está catorce commits por delante
de `origin/main`; no se realizaron operaciones remotas.

## Estado del roadmap

El estado de cada milestone se encuentra resumido en la sección
`Roadmap y estado de implementación` del README. La conclusión relevante es:

- MVP y M1 contienen gobierno y artefactos reutilizables, pero sus criterios de
  salida no se volvieron a demostrar contra laboratorios presentes en este
  workspace.
- M2 dispone del framework de contratos y validación, y de un consumidor
  Angular real con Angular `21.2.26`, TypeScript `5.9.3` y Vitest `4.1.12`.
- M3, M3.1 y M3.3 no tienen implementación demostrable. M4 y M5 contienen
  capacidades parciales, no sus criterios de salida completos.

## M2 — Requerimientos + HTML + pruebas

Estado: **BLOCKED**.

El laboratorio conserva una especificación, mockup HTML, YAML de casos
unitarios y una decisión funcional declarada. Los insumos especifican el campo
accesible `Nombre visible`, normalización con `trim`, validación local entre 2
y 50 caracteres, y el error `required` para valores formados solo por
espacios.

No se implementó la funcionalidad ni se cambió el laboratorio porque no existe
una ruta autorizada y verificable para hacerlo:

1. El único manifiesto Angular del framework sigue siendo
   `illustrative-not-ready-for-execution`; su consumidor, baseline y versiones
   no están verificados.
2. No hay un manifiesto ejecutable equivalente vinculado al laboratorio real.
3. No hay PREPARE exitoso, recibo ni ancla externa independiente coherente.
4. La decisión del laboratorio documenta una aprobación funcional declarada,
   pero limita de forma expresa el alcance a documentación y evidencia; no
   autoriza implementación.
5. La integración SSH firmada es experimental y no se usa como condición
   artificial de cierre de M2. Tampoco existe evidencia firmada que pudiera
   aportar una autorización adicional.

Modificar el manifiesto ilustrativo, fabricar un ancla o ampliar unilateralmente
la autorización invalidaría los controles existentes. Por ello, los comandos
del consumidor (`build`, pruebas unitarias, Playwright y VERIFY) quedan
**NOT_RUN** y no se reclama evidencia de navegador.

## Validación ejecutada

En el framework se ejecutó:

```text
.venv/bin/python -m unittest discover -s tests -v
```

Resultado: `119` pruebas ejecutadas, `OK`, en aproximadamente 29 segundos.
La suite cubre el instalador y los validadores M2, incluido el verificador de
autorización SSH. No valida una implementación Angular ni sustituye las
pruebas funcionales requeridas por el criterio de salida de M2.

## Continuidad requerida

Para reanudar M2 se necesita una autorización de implementación y un manifiesto
`ready-for-execution` versionado que describa el laboratorio real, sus hashes,
baseline, alcance permitido y evidencia de decisión. Después debe completarse
PREPARE, almacenarse un ancla externa independiente y coherente, implementar
solo dentro del alcance verificado y ejecutar build, pruebas unitarias,
Playwright y VERIFY con evidencia real. La ejecución de Playwright es una
condición pendiente del criterio de salida, no una comprobación realizada en
este cierre bloqueado.
