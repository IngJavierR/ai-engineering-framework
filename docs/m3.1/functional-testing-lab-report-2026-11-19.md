# M3.1 — Functional Testing

## Resultado de laboratorio

El laboratorio Angular `angular-customer-profile-consumer` ejecutó Cypress
`16.3.0` con Electron `150` headless contra `http://127.0.0.1:4200`.

| Escenarios | Pass | Fail |
| ---: | ---: | ---: |
| 4 | 4 | 0 |

La batería verifica el formulario accesible, validación obligatoria, espacios,
normalización, límites 2/50, límites inválidos 1/51, mensajes, atributos ARIA
y la interacción `Guardar`. Está trazada a los `REQ-*` y `UT-*` existentes.

Las capturas de fallo y videos están configurados y se ignoran por defecto. La
evidencia detallada y matriz pertenecen al consumidor:
[customer-profile-cypress-report.md](../../../labs/angular-customer-profile-consumer/docs/m3.1/customer-profile-cypress-report.md).

## Capacidad reutilizable

La skill `cypress-functional-testing` contiene reglas independientes del stack
para selectores accesibles, aislamiento, determinismo, limpieza y evidencia.
Se instala con:

```bash
python3 tools/install.py --target ../consumer-project \
  --capability cypress-functional-testing
```

**M3.1 DEVELOPMENT / LAB: COMPLETED.** La certificación formal de gobierno no
se ejecutó ni se representa como aprobada.
