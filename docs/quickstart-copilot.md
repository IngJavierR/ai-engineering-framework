# Quickstart de Copilot para features frontend M2

## Preparación

```bash
cd workspace   # contiene ai-engineering-framework/, app/, features/, evidence/, custody/
FW=ai-engineering-framework
python3 -m pip install -r $FW/tools/requirements-frontend-contracts.txt
```

Instala el perfil del consumidor:

```bash
python3 $FW/tools/install.py --target app --profile angular --dry-run
```

El consumidor debe ser un repositorio Git con working tree limpio.

## Estructura recomendada

```text
workspace/
├── ai-engineering-framework/   # framework
├── app/                        # consumidor Git limpio
├── features/<feature>/         # specification, mockup, YAML y manifest
├── evidence/                   # snapshot y receipt, fuera del consumidor
└── custody/anchor.json         # anchor fuera de evidence y del consumidor
```

## Flujo verificable

1. Crear insumos ilustrativos:

   ```bash
   python3 $FW/tools/new_feature.py \
     --feature-id FEAT-PROFILE-001 \
     --stack angular \
     --consumer app \
     --frontend-root frontend \
     --out features/profile
   ```

2. Completar requisitos, mockup, casos unitarios, alcance y decisiones humanas.
   El scaffold queda como `illustrative-not-ready-for-execution`; no autoriza
   implementación. Confirma los cambios del consumidor si usaste `--contract-dir`:
   ```bash
   git -C app add -A
   git -C app commit -m "content: prepare feature business inputs"
   ```

3. Refrescar hashes, versiones resueltas y baseline después de editar insumos:

   ```bash
   python3 $FW/tools/refresh_manifest.py \
     --manifest features/profile/angular.input.yaml
   ```

4. Corregir errores estructurales/semánticos hasta que ambos validadores pasen.

5. Crear una rama de feature antes de PREPARE. Los patrones `ignoredWorkPaths`
   quedan anclados en este punto y no pueden ampliarse para ocultar cambios:

   ```bash
   git -C app switch -c feat/profile-001
   python3 $FW/tools/validate_frontend_workflow.py prepare \
     --manifest features/profile/angular.input.yaml \
     --consumer-repository app \
     --workspace-root . \
     --evidence-directory evidence
   ```

6. Crear el anchor en custodia independiente:

   ```bash
   RECEIPT=$(ls -t evidence/*.receipt.json | head -1)
   python3 $FW/tools/make_anchor.py \
     --receipt "$RECEIPT" \
     --output custody/anchor.json
   ```

7. Planear e implementar con Copilot, y finalmente ejecutar VERIFY:

   ```bash
   python3 $FW/tools/validate_frontend_workflow.py verify \
     --manifest features/profile/angular.input.yaml \
     --consumer-repository app \
     --workspace-root . \
     --evidence-directory evidence --receipt "$RECEIPT" \
     --external-anchor custody/anchor.json
   ```

## Interpretación de VERIFY

`VERIFY` con `status: PASS` y `workflowStatus: BLOCKED` significa que el alcance
Git observable es conforme, pero la evidencia de pruebas sigue en `NOT_RUN`.
No certifica autoría, pruebas, build, typecheck ni validación formal completa.
En un monorepo, `--frontend-root frontend` hace que las rutas del manifiesto se
resuelvan dentro de ese directorio y protege los directorios hermanos.
Los patrones `ignoredWorkPaths` quedan anclados en PREPARE; no se pueden ampliar
después para ocultar cambios de VERIFY.

## Decisiones autorizadas

`authorizedDecisions` sigue siendo fail-closed. Hasta que exista evidencia
criptográfica/política real soportada, elimina la ambigüedad del requisito o
mantén la feature bloqueada; no inventes aprobaciones, firmas ni custodia.
