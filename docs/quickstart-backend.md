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
Gatling. Antes de implementar, ejecuta:

```bash
python3 tools/validate_backend_contracts.py --input backend.input.yaml
```

El resultado `VALID` permite implementar dentro del alcance autorizado. Un
resultado `INVALID` requiere corrección y `BLOCKED` requiere una decisión de
política, por ejemplo si el esquema ya usa otra herramienta de migración.
