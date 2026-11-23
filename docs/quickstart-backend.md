# Quickstart backend contract-first

Instala el perfil de backend apropiado antes de crear una feature:

```bash
python3 tools/install.py --target ../consumer --profile python-fastapi
```

Crea el insumo verificable y reemplaza los valores ilustrativos por los
aprobados por el consumidor:

```bash
python3 tools/new_feature.py --stack python-fastapi --feature-id FEAT-ORDERS-001 \
  --consumer ../consumer --out ../consumer/feature-input
python3 tools/refresh_manifest.py --manifest ../consumer/feature-input/backend.input.yaml
```

El manifiesto requiere OpenAPI aprobado, casos de prueba, Liquibase y perfiles
Gatling. Antes de implementar, ejecuta la prevalidación; permite que Copilot
cree el changelog nuevo dentro del alcance autorizado:

```bash
python3 tools/validate_backend_contracts.py --input backend.input.yaml --phase preflight
```

Después de crear el changelog y el código, exige la verificación completa:

```bash
python3 tools/validate_backend_contracts.py --input backend.input.yaml --phase verify
```

El resultado `VALID` de `verify` permite implementar dentro del alcance autorizado. Un
resultado `INVALID` requiere corrección y `BLOCKED` requiere una decisión de
política, por ejemplo si el esquema ya usa otra herramienta de migración.

Para hacer cumplir el alcance declarado durante la implementación, usa el
workflow con evidencia fuera del repositorio consumidor. `PREPARE` captura un
snapshot limpio y `VERIFY` exige un ancla externa y la fase `verify` completa:

```bash
python3 tools/validate_backend_workflow.py prepare \
  --manifest ../consumer/feature-input/backend.input.yaml \
  --consumer-repository ../consumer --workspace-root .. \
  --evidence-directory ../evidence
python3 tools/make_anchor.py --receipt ../evidence/<execution>.receipt.json \
  --output ../custody/<execution>.anchor.json
python3 tools/validate_backend_workflow.py verify \
  --manifest ../consumer/feature-input/backend.input.yaml \
  --consumer-repository ../consumer --workspace-root .. \
  --evidence-directory ../evidence --receipt ../evidence/<execution>.receipt.json \
  --external-anchor ../custody/<execution>.anchor.json
```
