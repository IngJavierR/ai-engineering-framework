---
name: frontend-ui-design
description: >
  Analyze and plan Angular or React frontend work from a functional
  specification, self-contained HTML mockup, frontend-ui-input/v1 and
  frontend-unit-tests/v1 contracts. Use for frontend requirement
  interpretation, safe mockup-to-component planning, REQ-to-CMP-to-UT
  traceability, PREPARE/VERIFY governance, consumer convention discovery,
  and fail-closed scope planning before implementation.
---

# Frontend UI Design

## Mission

Plan an Angular or React frontend feature from verified M2 inputs without
implementing consumer code, running consumer commands, or modifying contracts.

This skill supports:
- NEW_FRONTEND_FEATURE
- EXISTING_FRONTEND_FEATURE
- ANGULAR_FRONTEND_PLAN
- REACT_FRONTEND_PLAN
- MOCKUP_TO_COMPONENT_PLAN

The functional specification defines business rules. A mockup defines visual
and semantic reference only; it does not authorize business behavior.

## Mandatory Governance

Follow repository, consumer, and applicable client instructions.

Read references:
- [input interpretation](./references/input-interpretation.md)
- [mockup conversion](./references/mockup-conversion.md)
- [traceability and scope](./references/traceability-and-scope.md)

Use the existing M2 structural validator, semantic validator, Git scope guard,
and PREPARE/VERIFY invoker as independent controls. This skill does not replace,
duplicate, or bypass them.

Do not proceed with executable planning unless PREPARE completed successfully,
the receipt and independent external anchor correspond, and all manifest facts
required for execution are verified. Correspondence with an external anchor
does not authenticate its custodian or prove provenance.

## Workflow

### 1. Discover Inputs

Identify:
- `frontend-ui-input/v1` manifest and `frontend-unit-tests/v1` document.
- Referenced functional specification and self-contained HTML mockup.
- Consumer repository, declared stack, manifest, lockfile, and resolved versions.
- Consumer component, style, TypeScript, and unit-test conventions.
- Existing M2 validation results, PREPARE receipt, and independent external anchor.
- `allowedPaths`, `protectedPaths`, `deletionPolicy`, and authorized decisions.

Reject `illustrative-not-ready-for-execution` manifests for executable planning.
Do not invent missing consumer metadata, hashes, versions, approvals, or rules.

### 2. Establish Planning Eligibility

Confirm through the existing controls that:
- Input contracts are structurally valid.
- Referenced files, hashes, paths, consumer facts, and authorizations are
  semantically valid.
- PREPARE completed successfully against the intended consumer and input identity.
- The receipt and external anchor are coherent with the same manifest, inputs,
  consumer, baseline, and initial snapshot.

If an ambiguity blocks a requirement, an authorized decision lacks verifiable
evidence, the consumer cannot be verified, or PREPARE evidence is incomplete,
report `BLOCKED`. Do not treat an illustrative example, receipt, or anchor as a
substitute for independently verified facts.

### 3. Interpret Functional Sources

Classify each statement as:
- **CONFIRMED**: a business rule supported by the functional specification and
  represented in the manifest.
- **INFERENCE**: a presentation-oriented interpretation that remains
  non-implementable unless the manifest permits it.
- **AMBIGUITY**: missing or conflicting information that requires a verified
  authorized decision when it blocks a requirement.
- **AUTHORIZED DECISION**: a manifest decision with independently verifiable
  evidence that applies to the stated requirements only.

Use the specification for business rules, the unit-test YAML for mandatory
unit-test intent, the manifest for scope and authorization, and the mockup for
visual and semantic reference. Do not infer persistence, APIs, navigation,
authentication, side effects, or dependencies.

### 4. Analyze the Consumer

Inspect the real consumer without modifying it. Identify its existing:
- Angular or React structure and component conventions.
- TypeScript and style conventions.
- Local unit-test runner, configured test utilities, scripts, and result format.
- Nearby component and test patterns that can be followed.

Do not assume framework versions, standalone components, NgModules, form APIs,
state libraries, test runners, Testing Library, or styling systems. Record an
unknown required convention as a limitation or `BLOCKED` when it prevents a
safe plan.

### 5. Build the Traceability Plan

For every unit-testable requirement, map:

```text
REQ-* -> CMP-* -> UT-* -> planned technical test -> planned evidence
```

Identify conceptual components from the manifest. Plan technical component,
validator, utility, hook, service, state, adapter, or other units only as
allowed by the unit-test target and consumer conventions. Prepare the separate
consumer-specific entries required by `frontend-ui-output/v1`; do not create a
new schema or persistent contract.

A unit-testable requirement without a sufficient conceptual component or YAML
case is `BLOCKED`. A YAML case without a related requirement or component is
also `BLOCKED` and must be handled by the existing validators rather than
silently repaired.

### 6. Plan Mockup Conversion

Convert only verified visual and semantic reference into native components.
Preserve applicable HTML semantics, accessible labels, fields, control names,
and declared assets. Translate styles through the consumer's existing styling
conventions.

Never copy or activate scripts, inline handlers, trackers, CDN references,
remote imports, or undeclared dependencies. Do not convert visual interactions
into unconfirmed business behavior and do not add UI libraries automatically.

Read [mockup conversion](./references/mockup-conversion.md).

### 7. Plan Scope-Constrained Files

List planned technical source, style, asset, and test destinations without
creating or modifying them. Every destination must be allowed, unprotected,
regular, and compatible with consumer conventions.

`protectedPaths` takes absolute precedence over `allowedPaths`. Respect
`deletionPolicy` and applicable verified authorization. Never use globs,
traversal, symlinks, submodules, path-type changes, or renames to bypass scope.

Read [traceability and scope](./references/traceability-and-scope.md).

### 8. Report the Plan

Produce:
1. Consumer type and detected conventions.
2. Verified sources and their validation status.
3. `REQ-* -> CMP-* -> UT-*` matrix.
4. Mockup conversion inventory.
5. Confirmed rules, inferences, ambiguities, and authorized decisions.
6. Planned files and scope assessment.
7. Detected runner and unit-test conventions.
8. Correspondences prepared for `frontend-ui-output/v1`.
9. Pending checks as `NOT_RUN`.
10. Final status.

## Validation Boundaries

This skill must not:
- Modify consumer code, tests, configuration, dependencies, contracts, or examples.
- Run build, typecheck, unit tests, browser tests, or any consumer command.
- Declare `GENERATED`, `COMPILED`, `TESTED`, or `VALIDATED` without real evidence.
- Declare `VALIDATED` automatically after PREPARE or VERIFY.
- Introduce Cypress, Playwright, E2E, performance, or security activities.

VERIFY `PASS` establishes only observable Git scope conformity. It does not
prove change authorship or absence of intermediate changes that were reverted.
It also does not execute or validate frontend build, typecheck, or unit tests.

## Status

Use one of:
- `READY_FOR_IMPLEMENTATION`
- `BLOCKED`

Use `READY_FOR_IMPLEMENTATION` only when executable planning is complete and
all required preconditions are verified. Otherwise report `BLOCKED` with each
reason. All execution validations remain `NOT_RUN` in this planning skill.
