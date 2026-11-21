# Quickstart de Copilot para features frontend M2

## Requisitos

Instala el perfil del consumidor y las dependencias de los validadores:

```bash
python3 tools/install.py --target ../mi-frontend --profile angular --dry-run
python3 -m pip install -r tools/requirements-frontend-contracts.txt
```

El consumidor debe ser un repositorio Git con working tree limpio. Las
dependencias de validación se instalan en el entorno Python elegido por el
equipo; no las instala automáticamente `install.py`.

## Estructura recomendada

```text
workspace/
├── mi-frontend/            # consumidor Git limpio
├── features/<feature>/     # specification, mockup, YAML y manifest
├── evidence/               # snapshot y receipt, fuera del consumidor
└── custody/anchor.json     # anchor fuera de evidence y del consumidor
```

## Flujo verificable

1. Crear insumos ilustrativos:

   ```bash
   python3 tools/new_feature.py \
     --feature-id FEAT-PROFILE-001 \
     --stack angular \
     --consumer ../../mi-frontend \
     --out features/profile
   ```

2. Completar requisitos, mockup, casos unitarios, alcance y decisiones humanas.
   El scaffold queda como `illustrative-not-ready-for-execution`; no autoriza
   implementación.
3. Refrescar hashes, versiones resueltas y baseline después de editar insumos:

   ```bash
   python3 tools/refresh_manifest.py \
     --manifest features/profile/angular.input.yaml
   ```

4. Corregir errores estructurales/semánticos hasta que ambos validadores pasen.
5. Ejecutar PREPARE con evidencia fuera del consumidor:

   ```bash
   python3 tools/validate_frontend_workflow.py prepare \
     --manifest features/profile/angular.input.yaml \
     --consumer-repository mi-frontend \
     --workspace-root . \
     --evidence-directory evidence
   ```

6. Crear el anchor en custodia independiente:

   ```bash
   python3 tools/make_anchor.py \
     --receipt evidence/<execution-id>.receipt.json \
     --output custody/anchor.json
   ```

   El anchor prueba correspondencia de valores, no autoridad de custodia ni
   autoría. El invocador es responsable de conservarlo por un canal aprobado.
7. Planear e implementar con Copilot, y finalmente ejecutar VERIFY con receipt
   y anchor.

## Prompts recomendados

**Planear**

> Usa la skill `frontend-ui-design` con
> `features/<feature>/angular.input.yaml`, el receipt
> `evidence/<id>.receipt.json` y el anchor `custody/anchor.json`. Entrega la
> matriz REQ→CMP→UT y el estado final.

**Implementar**

> Usa la skill `angular-ui-implementation` para implementar el plan aprobado
> dentro de `allowedPaths`, con pruebas unitarias. Ejecuta solo comandos
> existentes del proyecto y registra la evidencia en `frontend-ui-output/v1`.

Para React, sustituye `angular` por `react` y usa las skills equivalentes.

## Interpretación de VERIFY

`VERIFY` con `status: PASS` y `workflowStatus: BLOCKED` significa que el alcance
Git observable es conforme, pero la evidencia de frontend sigue en `NOT_RUN`.
No certifica autoría, pruebas, build, typecheck ni validación formal completa.

## Decisiones autorizadas

`authorizedDecisions` sigue siendo fail-closed. Hasta que exista evidencia
criptográfica/política real soportada, elimina la ambigüedad del requisito o
mantén la feature bloqueada; no inventes aprobaciones, firmas ni custodia.
