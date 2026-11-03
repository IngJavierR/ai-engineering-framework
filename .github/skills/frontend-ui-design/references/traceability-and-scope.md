# Traceability and Scope Planning

## Purpose

Define the planning evidence required before a stack-specific frontend skill may
implement an M2 feature. This reference does not create a new schema, persistent
contract, validator, or scope exception.

## Traceability Chain

Every unit-testable requirement must have a complete planned chain:

```text
REQ-* -> CMP-* -> UT-* -> planned technical test -> planned evidence
```

- `REQ-*` comes from confirmed requirements in `frontend-ui-input/v1`.
- `CMP-*` comes from declared conceptual components and must include the
  requirement.
- `UT-*` comes from `frontend-unit-tests/v1` and must reference both the
  requirement and a related conceptual component.
- The planned technical test follows the detected conventions of the intended
  Angular or React consumer.
- Planned evidence prepares the fields required by the consumer-specific
  `frontend-ui-output/v1.traceability.entries` record.

A shared YAML case can map to different technical test identifiers in Angular
and React. Each consumer keeps its own traceability entries, technical test
names, result evidence, and execution status.

## Required Matrix

The planning report must include at least:

| Requirement | Conceptual component | YAML case | Target type / name | Planned technical unit | Planned technical test | Output correspondence |
| --- | --- | --- | --- | --- | --- | --- |

Use the target in the YAML case to constrain the technical plan. For example,
`component`, `validator`, `utility`, `hook`, `service`, `state`, and `adapter`
may require different test strategies. `other` requires the contract's explicit
justification.

Do not use line coverage, a snapshot, generated source, or a component name as
a substitute for a missing requirement-to-case link.

## Traceability Blocking Conditions

Return `BLOCKED` when any of these conditions applies:

- A unit-testable `REQ-*` has no declared `CMP-*`.
- A `REQ-*`/`CMP-*` relation has no applicable `UT-*` case.
- A `UT-*` references unrelated requirements or components.
- A required precondition references an unverified authorized decision.
- A test needs async control not supported or not deterministically planable by
  the detected consumer configuration.
- A planned technical test cannot comply with the case isolation requirements.
- A required technical destination is prohibited or cannot be established from
  consumer conventions.

Use existing structural and semantic validators for contract errors. Do not edit
or silently reinterpret contracts to make a matrix complete.

## Planned Files and Scope

List planned paths only; this skill must not create, modify, delete, rename, or
change the type of consumer files.

For every planned destination, record:

| Planned path | Purpose | Change kind | Allowed-path match | Protected-path result | Deletion / authorization assessment |
| --- | --- | --- | --- | --- | --- |

Apply the manifest rules exactly:

1. `protectedPaths` has absolute precedence over `allowedPaths`.
2. A path must be inside an explicit allowed file or directory entry.
3. Paths must be regular and safe; no absolute paths, globs, traversal,
   duplicate separators, symlink traversal, submodules, or type changes may
   bypass scope.
4. A rename requires both origin and destination to be allowed and unprotected.
5. A deletion requires an allowed, unprotected target, `deletionPolicy.allowed:
   true`, and applicable verifiable authorization.
6. A scope exception requires a new versioned manifest and verified authorized
   decision; it cannot be improvised by this skill.

If any planned destination is outside scope or protected, do not select an
alternative by assumption. Report `BLOCKED` and the exact scope conflict.

## PREPARE and VERIFY Boundaries

PREPARE must succeed before executable planning. It validates current inputs and
captures an initial Git snapshot through the existing workflow. The planning
report must preserve the identity that PREPARE established: manifest, referenced
input hashes, consumer identity, base commit, and snapshot.

A coherent externally supplied anchor is required together with the PREPARE
receipt. It proves value correspondence only; it does not authenticate the
custodian, prove authorship, or prove that no reverted intermediate changes
occurred.

VERIFY is for the post-change workflow and must be invoked by a later execution
phase. A `PASS` means only that observable Git scope conforms. It neither runs
nor validates builds, typechecks, or unit tests. Those checks remain `NOT_RUN`
in this planning skill and require real command and result evidence in
`frontend-ui-output/v1` after implementation.

## Planning Status

Use `READY_FOR_IMPLEMENTATION` only when the complete matrix, conversion
inventory, scope table, consumer conventions, and governance preconditions are
present and unblocked. Otherwise use `BLOCKED` and enumerate every unresolved
reason.
