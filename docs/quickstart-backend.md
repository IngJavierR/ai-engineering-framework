# Quickstart backend contract-first

## Preparación

```bash
cd workspace   # contiene ai-engineering-framework/, app/, features/, evidence/, custody/
FW=ai-engineering-framework
python3 -m pip install -r $FW/tools/requirements-frontend-contracts.txt
```

Instala el perfil de backend apropiado en el consumidor:

```bash
python3 $FW/tools/install.py --target app --profile python-fastapi
```

## Crear el insumo

Crea los insumos verificables. `--contract-dir backend/contract` deja el contrato
aprobado dentro del consumidor y lo protege durante VERIFY. Debe confirmarse antes
de `refresh`, porque este comando rechaza árboles consumidores sucios con `RM-GIT-001`:

```bash
python3 $FW/tools/new_feature.py --stack python-fastapi --feature-id FEAT-ORDERS-001 \
  --consumer app --contract-dir backend/contract --out features/orders-api
git -C app add backend/contract
git -C app commit -m "docs: add approved orders API contract"
python3 $FW/tools/refresh_manifest.py --manifest features/orders-api/backend.input.yaml
```

El manifiesto requiere OpenAPI aprobado, casos de prueba, Liquibase y perfiles
Gatling. Antes de implementar, ejecuta la prevalidación; permite que Copilot
cree el changelog nuevo dentro del alcance autorizado:

```bash
python3 $FW/tools/validate_backend_contracts.py \
  --input features/orders-api/backend.input.yaml --phase preflight
```

## Implementar con alcance verificado

Crea una rama de feature antes de PREPARE. Los patrones `ignoredWorkPaths` se
fijan en este punto y no pueden ampliarse después:

```bash
git -C app switch -c feat/orders-001
python3 $FW/tools/validate_backend_workflow.py prepare \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository app --workspace-root . \
  --evidence-directory evidence
RECEIPT=$(ls -t evidence/*.receipt.json | head -1)
python3 $FW/tools/make_anchor.py --receipt "$RECEIPT" \
  --output custody/anchor.json
```

Después de crear el changelog, el código y la simulación Gatling, ejecuta la
verificación completa antes de VERIFY:

```bash
python3 $FW/tools/validate_backend_contracts.py \
  --input features/orders-api/backend.input.yaml --phase verify
python3 $FW/tools/validate_backend_workflow.py verify \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository app --workspace-root . \
  --evidence-directory evidence --receipt "$RECEIPT" \
  --external-anchor custody/anchor.json
```

`status: PASS` con `workflowStatus: BLOCKED` significa que el alcance es conforme,
pero la evidencia de pruebas, build, Liquibase y Gatling sigue pendiente.

El scaffold detecta los stacks presentes en el monorepo (Node, Python, Java, Gatling)
y declara automáticamente sus artefactos de trabajo como ignorados. Los patrones quedan
anclados en PREPARE y no se pueden cambiar después para ocultar cambios de VERIFY.
