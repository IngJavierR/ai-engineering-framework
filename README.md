
# AI Engineering Framework

Framework para estandarizar el desarrollo asistido por GitHub Copilot.
Instálalo en tu proyecto y obtén skills, instrucciones y un flujo
PREPARE/VERIFY verificable para backend y frontend.

**Versión actual:** `0.8.0-rc.1`

---

## 0. Prerrequisitos

```bash
python3 --version          # 3.11 o superior
node --version && npm --version
java -version              # JDK 17 o superior (solo si usas Gatling o Java)
mvn -version               # Maven (solo si usas Gatling o Java)
docker compose version     # Docker Desktop encendido (solo si usas PostgreSQL local)
git --version
git config --global init.defaultBranch main   # las pruebas del framework asumen "main"
```

En VS Code: **GitHub Copilot Chat en modo Agent**.

---

## 1. Estructura de trabajo recomendada

```text
{base}/
├── ai-engineering-framework/   # este repositorio (clonado aquí)
├── .venv-fw/                   # Python para los validadores del framework
├── mi-proyecto/                # tu proyecto (repo Git)
├── features/                   # insumos de negocio por feature (fuera del proyecto)
├── evidence/                   # snapshots y receipts de PREPARE
└── custody/                    # anchor externo
```

---

## 2. Clonar el framework y preparar el entorno

```bash
cd {base}
git clone https://github.com/IngJavierR/ai-engineering-framework.git
FW=ai-engineering-framework

# En macOS Homebrew, Python no permite pip global (PEP 668): usa un venv propio
python3 -m venv .venv-fw
source .venv-fw/bin/activate
pip install --upgrade pip
python3 -m pip install -r $FW/tools/requirements-frontend-contracts.txt pytest

# Opcional: verifica que el framework está sano en tu máquina
(cd $FW && bash tools/release_gate.sh)   # esperado: RELEASE_GATE_PASS
```

En cada nueva terminal repite desde `{base}/`:

```bash
source .venv-fw/bin/activate && FW=ai-engineering-framework
```

---

## 3. Instalar el framework en tu proyecto

El proyecto destino debe ser un repositorio Git con working tree limpio.

Elige el perfil según tu stack. Puedes combinar perfiles con `--profile` repetido:

| Perfil | Stack | Skills que instala |
| --- | --- | --- |
| `python-fastapi` | FastAPI + PostgreSQL | DDD backend, OpenAPI, Liquibase, Gatling, seguridad |
| `angular` | Angular | Diseño/implementación Angular, Cypress, seguridad |
| `react` | React | Diseño/implementación React, Cypress, seguridad |
| `java-spring` | Java + Spring Boot | DDD backend, Java/Spring, OpenAPI, Liquibase, Gatling, seguridad |
| `backend` | Cualquier backend REST | DDD backend (neutral), OpenAPI, Liquibase, Gatling, seguridad |

```bash
# Proyecto Angular + FastAPI (monorepo)
python3 $FW/tools/install.py --target mi-proyecto \
  --profile angular --profile python-fastapi --dry-run   # previsualiza sin escribir

python3 $FW/tools/install.py --target mi-proyecto \
  --profile angular --profile python-fastapi

git -C mi-proyecto add -A
git -C mi-proyecto commit -m "chore: instalar ai-engineering-framework"
```

Confirma la instalación: aparece `.ai-framework.lock.json` y la carpeta `.github/`
con las skills e instrucciones del framework en tu proyecto.

---

## 4. Feature backend (contrato primero)

Ejecuta todo desde `{base}/`, con `.venv-fw` activado.

### 4.1 Crear los insumos

```bash
python3 $FW/tools/new_feature.py \
  --stack python-fastapi \
  --feature-id FEAT-ORDERS-001 \
  --consumer mi-proyecto \
  --contract-dir backend/contract \
  --out features/orders-api
```

### 4.2 Editar los insumos de negocio

Edita a mano solo estas dos cosas:

- `mi-proyecto/backend/contract/openapi.yaml`: contrato aprobado con un
  `operationId` único por operación.
- `mi-proyecto/backend/contract/test-cases.yaml`: al menos un caso 2xx por
  operación; si hay body o parámetros obligatorios, también un caso negativo 4xx.

### 4.3 Versionar, refrescar y prevalidar

```bash
git -C mi-proyecto add backend/contract
git -C mi-proyecto commit -m "docs: add approved API contract"

python3 $FW/tools/refresh_manifest.py \
  --manifest features/orders-api/backend.input.yaml

python3 $FW/tools/validate_backend_contracts.py \
  --input features/orders-api/backend.input.yaml --phase preflight   # esperado: VALID
```

### 4.4 PREPARE

```bash
git -C mi-proyecto switch -c feat/orders-001

python3 $FW/tools/validate_backend_workflow.py prepare \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository mi-proyecto --workspace-root . \
  --evidence-directory evidence                                       # esperado: PASS WF-PREPARE-000

RECEIPT=$(ls -t evidence/*.receipt.json | head -1)
python3 $FW/tools/make_anchor.py --receipt "$RECEIPT" \
  --output custody/anchor.json
```

### 4.5 Implementar con Copilot (modo Agent)

Abre `mi-proyecto` en VS Code y envía este prompt:

> Usa las skills `openapi-to-ddd`, `fastapi-development`, `liquibase-versioning` y
> `gatling-performance` con el manifiesto `../features/orders-api/backend.input.yaml`.
> Implementa en `backend/` el contrato aprobado de `backend/contract/openapi.yaml` sin
> modificarlo.
>
> - Crea el esquema PostgreSQL con changesets Liquibase XML incluidos desde
>   `backend/db/changelog/db.changelog-master.xml`, con rollback. No uses `create_all`
>   ni Alembic.
> - Implementa con pytest cada `TC-*` de `backend/contract/test-cases.yaml` más
>   conformidad con schemathesis contra el contrato.
> - Crea `performance/gatling/` (Maven + Java DSL) con perfiles smoke, baseline y
>   stress; la URL desde `TARGET_BASE_URL`, solo destinos loopback.
>
> Trabaja solo dentro de `scope.allowedPaths` y reporta la evidencia como
> GENERATED/COMPILED/TESTED/VALIDATED/NOT_RUN.

### 4.6 Verificar localmente y correr VERIFY

```bash
# Aplica changesets Liquibase
docker compose --profile tools build liquibase
docker compose --profile tools run --rm liquibase validate
docker compose --profile tools run --rm liquibase update

# Pruebas
(cd mi-proyecto/backend && .venv/bin/pytest -q)

# Gatling
(cd mi-proyecto/backend && .venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000) &
(cd mi-proyecto/performance/gatling && \
  TARGET_BASE_URL=http://127.0.0.1:8000 mvn gatling:test)
kill %1

git -C mi-proyecto add -A
git -C mi-proyecto commit -m "feat: FEAT-ORDERS-001"

python3 $FW/tools/validate_backend_contracts.py \
  --input features/orders-api/backend.input.yaml --phase verify       # esperado: VALID

python3 $FW/tools/validate_backend_workflow.py verify \
  --manifest features/orders-api/backend.input.yaml \
  --consumer-repository mi-proyecto --workspace-root . \
  --evidence-directory evidence --receipt "$RECEIPT" \
  --external-anchor custody/anchor.json                               # esperado: PASS WF-VERIFY-000

git -C mi-proyecto switch main
git -C mi-proyecto merge --ff-only feat/orders-001
```

---

## 5. Feature frontend (Angular/React)

Empieza solo después de hacer merge de la feature backend. El anchor nuevo
reemplaza al anterior en `custody/`.

### 5.1 Crear los insumos

```bash
python3 $FW/tools/new_feature.py \
  --feature-id FEAT-PROFILE-001 \
  --stack angular \
  --consumer mi-proyecto \
  --frontend-root frontend \
  --out features/profile
```

### 5.2 Editar los insumos de negocio

En `features/profile/`:

- `specification.md`: descripción funcional de la feature.
- `mockup.html`: HTML autocontenido del diseño.
- `unit-tests.yaml`: casos unitarios por componente.
- `angular.input.yaml`: ajusta `templateStatus: ready-for-execution` y pega
  los fragmentos `requirements`, `conceptualComponents`, `mockups` y `unitTests.caseIds`
  generados por las skills M2.

No toques `scope`. El scaffold ya protege `package*.json`, `backend`,
`performance` y `db`, y declara los cachés.

### 5.3 Refrescar, validar y PREPARE

```bash
python3 $FW/tools/refresh_manifest.py \
  --manifest features/profile/angular.input.yaml

python3 $FW/tools/validate_frontend_contracts.py \
  --input features/profile/angular.input.yaml \
  --unit-tests features/profile/unit-tests.yaml                       # esperado: VALID

python3 $FW/tools/validate_frontend_semantics.py \
  --input features/profile/angular.input.yaml \
  --workspace-root "$PWD"                                             # esperado: sin errores

git -C mi-proyecto switch -c feat/profile-001

python3 $FW/tools/validate_frontend_workflow.py prepare \
  --manifest features/profile/angular.input.yaml \
  --consumer-repository mi-proyecto --workspace-root . \
  --evidence-directory evidence                                       # esperado: PASS WF-PREPARE-000

RECEIPT=$(ls -t evidence/*.receipt.json | head -1)
python3 $FW/tools/make_anchor.py --receipt "$RECEIPT" \
  --output custody/anchor.json
```

### 5.4 Planear e implementar con Copilot (modo Agent)

**Planear primero:**

> Usa la skill `frontend-ui-design` con `../features/profile/angular.input.yaml`,
> el receipt `../evidence/<id>.receipt.json` y el anchor `../custody/anchor.json`.
> Entrega la matriz REQ→CMP→UT y el estado final.

**Implementar solo si el plan resultó `READY_FOR_IMPLEMENTATION`:**

> Usa la skill `angular-ui-implementation` para implementar el plan aprobado
> dentro de `allowedPaths`, con pruebas unitarias. Ejecuta solo comandos existentes
> del proyecto y registra la evidencia en `frontend-ui-output/v1`.

### 5.5 Probar, confirmar y correr VERIFY

```bash
(cd mi-proyecto/frontend && npx ng test --watch=false)

git -C mi-proyecto add -A
git -C mi-proyecto commit -m "feat: FEAT-PROFILE-001"

python3 $FW/tools/validate_frontend_workflow.py verify \
  --manifest features/profile/angular.input.yaml \
  --consumer-repository mi-proyecto --workspace-root . \
  --evidence-directory evidence --receipt "$RECEIPT" \
  --external-anchor custody/anchor.json                               # esperado: PASS WF-VERIFY-000

git -C mi-proyecto switch main
git -C mi-proyecto merge --ff-only feat/profile-001
```

---

## 6. Interpretación de resultados

| Resultado | Significado |
| --- | --- |
| `PASS WF-VERIFY-000` con `workflowStatus: BLOCKED` | El alcance es conforme. La evidencia de pruebas, build, Liquibase y Gatling la certificas tú con los comandos de los pasos 4.6 / 5.5 |
| `FAIL SCOPE-008/009` | Copilot tocó algo fuera del alcance declarado. Revierte o ajusta el alcance en una feature nueva |
| `BLOCKED BE-HASH-001` | El contrato aprobado fue modificado después de PREPARE |
| `BLOCKED GIT-003` | Se cambió de rama después de PREPARE. El mensaje indica la rama esperada y la actual |
| `BLOCKED GIT-005` | Apareció un archivo ignorado no declarado (por ejemplo un archivo de secretos nuevo). El mensaje indica cuál |
| `FAIL RM-GIT-001` | El working tree del consumidor tiene cambios pendientes. Haz commit antes de `refresh_manifest` |

---

## 7. Upgrade y reinstalación

Si ya tienes el framework instalado y quieres añadir o actualizar capacidades:

```bash
# Añadir React a un proyecto que ya tiene Angular
python3 $FW/tools/install.py --target mi-proyecto --profile react --upgrade --dry-run
python3 $FW/tools/install.py --target mi-proyecto --profile react --upgrade

# Migrar desde un lock heredado (java-base a stack explícito)
python3 $FW/tools/install.py --target mi-proyecto \
  --profile python-fastapi --upgrade --migrate-stack
```

Los upgrades son aditivos; nunca eliminan capacidades implícitamente.

---

## 8. Bootstrap corporativo (proyectos múltiples)

Para aplicar el framework a varios proyectos con una política centralizada:

```bash
python3 $FW/tools/bootstrap.py \
  --target ../mi-proyecto \
  --version 0.8.0-rc.1 \
  --client-policy docs/m4/examples/client-a-java-policy.json \
  --dry-run
```

Consulta [docs/quickstart-backend.md](docs/quickstart-backend.md) y
[docs/quickstart-copilot.md](docs/quickstart-copilot.md) para flujos detallados.

---

## Estado y limitaciones

Estado actual: **READY_WITH_LIMITATIONS** — apto para piloto interno controlado con
fuente local fijada, locks y revisión humana. Consulta
[docs/release-readiness.md](docs/release-readiness.md) para la matriz completa de madurez.

Limitaciones conocidas:

- `release_gate.sh` requiere `ssh-keygen` (disponible en macOS, puede fallar en entornos CI
  reducidos).
- No existe atomicidad global de instalación ante interrupciones abruptas del sistema de archivos.
- Quality gates automatizados remotos no están implementados (`automatedQualityGates: false`).

Consulta el [CHANGELOG](CHANGELOG.md) para el historial de cambios por versión.
