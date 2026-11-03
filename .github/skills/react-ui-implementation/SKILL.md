---
name: react-ui-implementation
description: >
  Implement and validate React frontend features from an approved
  frontend-ui-design plan, frontend-ui-input/v1, frontend-unit-tests/v1,
  and a self-contained HTML mockup. Use for React consumer discovery,
  scope-governed JSX or TSX component generation, React unit-test
  implementation, PREPARE/VERIFY workflow integration, and
  frontend-ui-output/v1 evidence.
---

# React UI Implementation

## Mission

Implement an approved M2 frontend plan in a verified React consumer using its
existing conventions and tools. Preserve scope, traceability, and real evidence.

This skill supports:
- NEW_REACT_FEATURE
- EXISTING_REACT_FEATURE
- REACT_COMPONENT_IMPLEMENTATION
- REACT_UNIT_TEST_IMPLEMENTATION

This skill depends on `frontend-ui-design`. It must not replace the shared
planning workflow, M2 validators, Git scope guard, or PREPARE/VERIFY invoker.

## Mandatory Governance

Follow repository, consumer, and applicable client instructions.

Read references:
- [React discovery](./references/react-discovery.md)
- [React components](./references/react-components.md)
- [React unit testing](./references/react-unit-testing.md)

Before modifying a consumer, require:
- A `frontend-ui-design` result with `READY_FOR_IMPLEMENTATION`.
- A React `frontend-ui-input/v1` manifest for the same feature and consumer.
- The matching `frontend-unit-tests/v1` source, functional specification, and
  referenced mockup inputs.
- Successful M2 structural and semantic validation.
- Successful PREPARE and a receipt plus independent external anchor coherent
  with the manifest, input hashes, consumer identity, baseline, and snapshot.

Receipt/anchor value correspondence does not authenticate the custodian, prove
provenance, establish authorship, or prove that no intermediate changes were
reverted. Do not treat it as such.

Reject `illustrative-not-ready-for-execution` manifests. Reject a non-React
consumer, a plan for another identity, unverified required authorization, or a
missing blocking decision. Do not infer missing facts.

## Workflow

### 1. Confirm Plan and Identity

Verify that the shared plan:
- Is `READY_FOR_IMPLEMENTATION` and names `consumer.stack: react`.
- Corresponds to the exact feature, manifest, consumer, inputs, and baseline.
- Preserves the complete `REQ-* -> CMP-* -> UT-*` planning matrix.
- Lists destinations that remain allowed and unprotected.
- Records detected consumer conventions and pending checks.

If plan, manifest, PREPARE receipt, or external anchor diverges, report
`BLOCKED` before changing the consumer.

### 2. Discover the React Consumer

Inspect the real consumer read-only. Verify its resolved React and TypeScript
versions, component architecture, props, hooks, state, styling, assets, test
configuration, DOM simulation, and command scripts.

Determine from evidence which component, composition, state, hook, style, and
test patterns apply in the relevant area. Reuse only what the consumer already
provides. React Testing Library may be used only when it is installed and
configured in that consumer.

Do not assume React APIs, test runners, utilities, JSX transforms, or framework
versions from a package range. Do not add or configure dependencies. If a
mandatory capability cannot be satisfied using verified existing tooling and
permitted files, report `BLOCKED`.

### 3. Implement Only Authorized Behavior

Implement only `CONFIRMED` requirements and verified authorized decisions from
the shared plan. Maintain consumer conventions and create or modify only files
within `allowedPaths` that are not protected.

Translate mockup structure into native JSX or TSX and established styles.
Preserve applicable semantic elements, labels, accessible control names, field
attributes, and declared assets. Do not copy scripts, inline handlers, CDN
references, trackers, remote imports, or undeclared dependencies.

Do not infer or create APIs, navigation, persistence, authentication,
authorization, remote HTTP, or other side effects. A visual control is not a
business behavior unless confirmed and traced.

Read [React components](./references/react-components.md).

### 4. Implement Unit Tests

Translate every applicable `UT-*` into a technical React test while retaining:

```text
REQ-* -> CMP-* -> UT-* -> React technical test -> result -> evidence
```

Reuse the verified existing runner, configuration, DOM environment, and test
utilities. Use React Testing Library only if the consumer already installs and
configures it. Test pure validators and utilities directly when their contract
target allows it; test hooks with the existing local test pattern.

Use observable component behavior, roles, and accessible names for component
cases. Honor each case's preconditions, mocks, action, expected result,
isolation, and async controls. Do not use a snapshot or line coverage as a
substitute for a declared case.

Read [React unit testing](./references/react-unit-testing.md).

### 5. Execute Authorized Validation

Execute only existing, authorized consumer commands for build, typecheck, and
unit tests when they are applicable to the implemented scope. Do not install
packages, change configuration, or create commands merely to obtain a result.

Record each real command, exit code, runner, result artifact, scope, and
limitation in `frontend-ui-output/v1`. Use `NOT_RUN` when a relevant command
was not executed. Do not declare `COMPILED`, `TESTED`, or `VALIDATED` without
its required evidence.

### 6. Verify Scope and Report Evidence

After consumer changes, invoke VERIFY with the matching receipt, independent
external anchor, and external evidence location. Treat a failed or blocked scope
result as `BLOCKED`; do not convert it to `PASS`.

VERIFY `PASS` establishes observable Git scope conformity only. It does not
prove authorship, rule out reverted intermediate changes, execute frontend
commands, or establish final validation. Record consumer-specific changes,
traceability entries, command evidence, and limitations in
`frontend-ui-output/v1`.

## Scope Rules

`protectedPaths` takes absolute precedence over `allowedPaths`. Respect
`deletionPolicy` and only applicable verified authorizations. Never bypass scope
with globs, traversal, symlinks, submodules, type changes, or unauthorized
renames or deletions.

Do not modify consumer files merely because this skill is invoked. A separate
authorized execution using a ready plan is required.

## Required Report

Provide:
1. Plan, manifest, consumer, PREPARE, and anchor identity assessment.
2. Detected React versions, structure, conventions, DOM environment, and runner.
3. Implemented files and scope assessment.
4. `REQ-* -> CMP-* -> UT-* -> technical test` matrix.
5. Commands actually executed and their evidence.
6. VERIFY result and scope evidence.
7. `frontend-ui-output/v1` traceability and validation records.
8. Checks reported as `NOT_RUN` and remaining limitations.
9. Final status.

## Restrictions

Never:
- Modify protected paths, configuration, `package.json`, lockfiles, or routes
  unless the manifest explicitly allows them and they are unprotected.
- Add dependencies, UI libraries, test tools, runners, or configuration by default.
- Implement behavior from visual affordance alone.
- Use real HTTP, real browsers, E2E navigation, Cypress, Playwright, performance,
  or security testing.
- Claim `VALIDATED` because source was generated or VERIFY returned `PASS`.
- Claim authorship or absence of reverted intermediate changes.

## Status

Use one of:
- `READY_FOR_VALIDATION`
- `VALIDATED`
- `BLOCKED`

Use `VALIDATED` only when all applicable acceptance criteria, scope checks, and
real command evidence are sufficient. Use `READY_FOR_VALIDATION` when changes
are within scope but applicable validation remains pending. Use `BLOCKED` for
any failed precondition, scope violation, divergent identity, or missing required
capability.
