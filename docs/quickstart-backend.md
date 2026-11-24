# Quickstart backend contract-first

Instala el perfil de backend apropiado antes de crear una feature:

```bash
python3 tools/install.py --target consumer --profile python-fastapi
```

Crea el insumo verificable y reemplaza los valores ilustrativos por los
aprobados por el consumidor:

```bash
python3 tools/new_feature.py --stack python-fastapi --feature-id FEAT-ORDERS-001 \
  --consumer consumer --contract-dir backend/contract --out features/orders-api
git -C consumer add backend/contract
git -C consumer commit -m "docs: add approved orders API contract"
python3 tools/refresh_manifest.py --manifest features/orders-api/backend.input.yaml
```

`--contract-dir` es la opción recomendada: deja el contrato aprobado junto al
código y lo protege durante VERIFY. Debe confirmarse antes de `refresh`, porque
este comando rechaza árboles consumidores sucios con `RM-GIT-001`.

El manifiesto requiere OpenAPI aprobado, casos de prueba, Liquibase y perfiles
Gatling. Antes de implementar, ejecuta la prevalidación; permite que Copilot
cree el changelog nuevo dentro del alcance autorizado:

```bash
python3 tools/validate_backend_contracts.py --input features/orders-api/backend.input.yaml --phase preflight
```

Después de crear el changelog y el código, exige la verificación completa:

```bash
python3 tools/validate_backend_contracts.py --input features/orders-api/backend.input.yaml --phase verify
```

El resultado `VALID` de `verify` permite implementar dentro del alcance autorizado. Un
resultado `INVALID` requiere corrección y `BLOCKED` requiere una decisión de
política, por ejemplo si el esquema ya usa otra herramienta de migración.

Para hacer cumplir el alcance declarado durante la implementación, usa el
workflow con evidencia fuera del repositorio consumidor. `PREPARE` captura un
snapshot limpio y `VERIFY` exige un ancla externa y la fase `verify` completa:

```bash
git -C consumer switch -c feat/orders-001
python3 tools/validate_backend_workflow.py prepare \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository consumer --workspace-root . \
  --evidence-directory evidence
python3 tools/make_anchor.py --receipt evidence/<execution>.receipt.json \
  --output custody/<execution>.anchor.json
python3 tools/validate_backend_workflow.py verify \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository consumer --workspace-root . \
  --evidence-directory evidence --receipt evidence/<execution>.receipt.json \
  --external-anchor custody/<execution>.anchor.json
```

`scope.ignoredWorkPaths` puede declarar únicamente artefactos ya ignorados por
Git, como `.venv`, `__pycache__` o `performance/gatling/target`; su contenido
no se monitoriza. `status: PASS` con `workflowStatus: BLOCKED` significa que el
alcance es conforme, pero la evidencia de pruebas, build, Liquibase y Gatling
sigue pendiente.

Los patrones ignorados se fijan en PREPARE y no se pueden cambiar después. El
scaffold detecta los stacks presentes en el monorepo para incluir caches de
Node, Python, Java y Gatling cuando correspondan.
