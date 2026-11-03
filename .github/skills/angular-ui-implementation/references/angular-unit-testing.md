# Angular Unit Testing

## Purpose

Translate `frontend-unit-tests/v1` cases into deterministic Angular technical
tests using only the verified runner and utilities already configured by the
consumer.

## Traceability Requirement

Each applicable technical test must preserve:

```text
REQ-* -> CMP-* -> UT-* -> Angular technical test -> result -> evidence
```

Name or otherwise stably identify the technical test with its `UT-*` case and
record that identifier in the Angular `frontend-ui-output/v1` traceability
entry. A line-coverage value, snapshot, generated code, or suite name cannot
replace this link.

### Conceptual Example Only

The following is a planning example, not a test result or evidence claim:

| Requirement | Conceptual component | YAML case | Planned Angular unit | Planned technical test identifier |
| --- | --- | --- | --- | --- |
| `REQ-PROFILE-001-01` | `CMP-PROFILE-001-01` | `UT-PROFILE-001-01` | Form component | `UT-PROFILE-001-01 renders accessible display-name textbox` |
| `REQ-PROFILE-001-02` | `CMP-PROFILE-001-02` | `UT-PROFILE-001-02` | Pure name validator | `UT-PROFILE-001-02 accepts normalized valid name` |

This example neither authorizes a feature nor implies that any command ran.
Real identifiers, files, and results come only from the approved plan and
executed consumer validation.

## Test Strategy by `target.type`

| Contract target | Preferred strategy | TestBed use |
| --- | --- | --- |
| `component` | Render in the configured DOM simulation; assert required roles, accessible names, visible behavior, and isolated outputs. | Use when templates, DI, Angular rendering, or framework providers are required. |
| `validator` | Invoke a pure validator directly using declared input and assert normalized value and validation result. | Do not use unless the verified unit is Angular-coupled. |
| `utility` | Invoke directly with the contract input and expected output. | Normally unnecessary. |
| `service` | Use the consumer's existing DI and test-double pattern; replace external dependencies locally. | Use when DI is required. |
| `state` | Follow the established local signals/state testing approach and assert observable confirmed behavior. | Only when Angular integration is needed. |
| `adapter` | Exercise the local adapter boundary with stubs, spies, or fakes. | Use only for required Angular integration. |
| `other` | Use the contract justification and existing consumer convention. | Only when necessary and justified. |

A `hook` target is framework-neutral contract vocabulary. Angular implementations
must map it to an actually planned Angular unit; block when no approved,
traceable Angular equivalent exists rather than inventing one.

## Runner and DOM Rules

Use the installed and configured runner verified during discovery, such as
Jasmine/Karma, Jest, Vitest, or another consumer-provided runner. Do not assume
that a named tool is installed, and do not add packages, modify workspace files,
or switch runners.

Component tests may use DOM simulation and the runner's existing querying
utilities. Prefer roles and accessible names for requirements that declare
accessible controls. Do not require a real browser, E2E navigation, Cypress, or
Playwright.

Do not make external HTTP calls. For external boundaries, use the declared
mocking approach and existing local stubs, spies, fakes, module mocks, timers,
or service doubles. A case with `mocks: []` does not authorize real I/O.

## Case Translation Checklist

For every `UT-*`, preserve and implement:

1. `requirementIds` and `componentIds` in the traceability record.
2. `target.type`, `target.conceptualUnitId`, and `target.name`.
3. `classification`, including positive, negative, boundary, and regression
   intent.
4. Every precondition, including only verified `DEC-*` references.
5. Declared mocks and input.
6. Action type and operation.
7. Expected observable result.
8. Isolation: DOM simulation policy and prohibitions on external HTTP, real
   browser, and E2E navigation.
9. Async mechanism, timer control, completion condition, and cleanup.

If any item cannot be represented deterministically using verified local tools,
block the case and the dependent feature rather than weakening the contract.

## Async Controls

For `async.isAsync: false`, do not introduce uncontrolled waits.

For asynchronous cases, use only a mechanism that matches the contract and
existing runner support:

| Contract control | Required Angular test behavior |
| --- | --- |
| `promise` | Await a controlled promise and assert the declared completion condition. |
| `observable` | Use the existing consumer scheduler or subscription pattern; complete and clean up deterministically. |
| `callback` | Invoke the callback through a controlled local double and assert completion. |
| `timer`, `debounce`, `interval` | Use configured fake timers or framework test scheduler when declared; flush, advance, and clean up deterministically. |
| `await-controlled-promise` | Hold and resolve the local promise explicitly. |
| `fake-timers` | Use only the runner's verified fake-timer facility. |
| `framework-test-scheduler` | Use only an already configured compatible scheduler. |
| `manual` | Use only when the contract supplies its required justification and completion condition. |

Never use arbitrary sleeps, real network timing, ordering dependencies, or a
real browser to satisfy async behavior.

## Execution and Evidence

Run only existing authorized unit-test, build, or typecheck commands. Capture
real runner, command, exit code, result-file paths, scope, and limitations in
`frontend-ui-output/v1`.

After changes, run VERIFY with the corresponding receipt and independent anchor.
A `PASS` confirms observable Git scope only; it does not validate the test
command, prove authorship, or prove absence of reverted intermediate changes.
Use `NOT_RUN` for checks not executed and do not declare `VALIDATED` until all
applicable acceptance criteria have sufficient real evidence.