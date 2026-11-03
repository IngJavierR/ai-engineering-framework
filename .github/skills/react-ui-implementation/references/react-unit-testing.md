# React Unit Testing

## Purpose

Translate `frontend-unit-tests/v1` cases into deterministic React technical
tests using only the verified runner, simulated DOM, and utilities already
configured by the consumer.

## Traceability Requirement

Each applicable technical test must preserve:

```text
REQ-* -> CMP-* -> UT-* -> React technical test -> result -> evidence
```

Name or otherwise stably identify the technical test with its `UT-*` case and
record that identifier in the React `frontend-ui-output/v1` traceability entry.
A line-coverage value, snapshot, generated code, or suite name cannot replace
this link.

### Conceptual Example Only

The following is a planning example, not a test result or evidence claim:

| Requirement | Conceptual component | YAML case | Planned React unit | Planned technical test identifier |
| --- | --- | --- | --- | --- |
| `REQ-PROFILE-001-01` | `CMP-PROFILE-001-01` | `UT-PROFILE-001-01` | Profile form component | `UT-PROFILE-001-01 renders accessible display-name textbox` |
| `REQ-PROFILE-001-02` | `CMP-PROFILE-001-02` | `UT-PROFILE-001-02` | Pure name validator | `UT-PROFILE-001-02 accepts normalized valid name` |

This example neither authorizes a feature nor implies that any command ran.
Real identifiers, files, and results come only from the approved plan and
executed consumer validation.

## Test Strategy by `target.type`

| Contract target | Preferred strategy | React-specific constraint |
| --- | --- | --- |
| `component` | Render in the configured simulated DOM; assert roles, accessible names, observable output, and isolated interaction. | Use React Testing Library only when installed and configured; otherwise use the existing local component-test pattern. |
| `hook` | Exercise the hook through the consumer's existing hook-test pattern or an approved minimal test component. | Do not add a hook-test utility; block if no traceable local pattern exists. |
| `validator` | Invoke a pure validator directly with contract input and assert normalized value and validation result. | Do not render a component unless the verified unit is component-coupled. |
| `utility` | Invoke directly with declared input and expected output. | Normally does not require a DOM. |
| `service` | Follow existing local injection or module-boundary pattern; replace external dependencies locally. | Do not introduce a service container or real I/O. |
| `state` | Follow the established state/store test pattern and assert observable confirmed behavior. | Do not introduce a new global store or provider. |
| `adapter` | Exercise the local adapter boundary with stubs, spies, or fakes. | Do not cross an external network boundary. |
| `other` | Use the contract justification and existing consumer convention. | Block when no approved mapping exists. |

## Runner and DOM Rules

Use the installed and configured runner verified during discovery, such as Jest,
Vitest, or another consumer-provided runner. Do not assume a named tool is
installed, and do not add packages, modify configuration, or switch runners.

Use React Testing Library only when it is already installed and configured.
When available, component tests should query by role and accessible name for
requirements that declare accessible controls. Otherwise use the verified local
utility to assert observable behavior without coupling tests to internal
implementation details.

Do not require a real browser, E2E navigation, Cypress, or Playwright. Do not
make external HTTP calls. For external boundaries, use declared mocks and
existing local stubs, spies, fakes, module mocks, timers, or service doubles. A
case with `mocks: []` does not authorize real I/O.

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

| Contract control | Required React test behavior |
| --- | --- |
| `promise` | Await a controlled promise and assert the declared completion condition. |
| `observable` | Use the existing consumer subscription or scheduler pattern; complete and clean up deterministically. |
| `callback` | Invoke the callback through a controlled local double and assert completion. |
| `timer`, `debounce`, `interval` | Use verified fake timers or scheduler support when declared; advance/flush and clean up deterministically. |
| `await-controlled-promise` | Hold and resolve the local promise explicitly. |
| `fake-timers` | Use only the verified runner fake-timer facility. |
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
Propagate `FAIL` or `BLOCKED` without converting it to `PASS`. Use `NOT_RUN` for
checks not executed and do not declare `VALIDATED` until all applicable
acceptance criteria have sufficient real evidence.