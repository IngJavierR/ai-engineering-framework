# Frontend Input Interpretation

## Purpose

Define how `frontend-ui-design` interprets M2 frontend inputs without creating
new business behavior or replacing existing validators.

## Required Sources

Executable planning requires all of the following:

- A `frontend-ui-input/v1` manifest.
- Its referenced `frontend-unit-tests/v1` document.
- The referenced functional specification.
- At least one referenced self-contained HTML mockup.
- The real consumer repository and its declared configuration.
- Successful M2 validation and PREPARE evidence, with a coherent receipt and
  externally supplied independent anchor.

The manifest identifies the consumer, input hashes, scope, conceptual
components, and authorization state. The semantic validator remains responsible
for checking real paths, hashes, consumer facts, authorizations, and related
contract semantics.

## Source Authority

| Source | Authoritative use | Not authorized to define |
| --- | --- | --- |
| Functional specification | Business rules, acceptance criteria, and feature boundaries. | Unstated implementation details or external behavior. |
| `frontend-ui-input/v1` | Scope, input identity, consumer, conceptual components, decisions, and references. | New requirements or unverified approvals. |
| `frontend-unit-tests/v1` | Mandatory unit-test intent, isolation, expected outcomes, and async controls. | Framework-specific test APIs or unlisted business rules. |
| HTML mockup | Visual structure, visible text, semantics, labels, controls, and declared presentation assets. | Business rules, persistence, API calls, navigation, authorization, or side effects. |
| Consumer repository | Existing verified conventions, configured tools, and permitted technical patterns. | A reason to change protected paths or add dependencies. |

When sources conflict, do not reconcile them by invention. Report the conflict
as an ambiguity and block the affected requirement until an authorized decision
with verifiable evidence applies.

## Planning Eligibility

Before returning `READY_FOR_IMPLEMENTATION`, establish that:

1. The manifest uses `templateStatus: ready-for-execution`.
2. Structural and semantic validation have succeeded for the exact inputs.
3. Consumer identity, stack, versions, baseline, and required authorization
   evidence are verified.
4. PREPARE succeeded for the exact manifest and consumer.
5. The receipt and external anchor correspond to the same execution identity,
   manifest hash, input hashes, consumer identity, base commit, and snapshot
   hash.
6. No blocking ambiguity or untraceable unit-testable requirement remains.

Receipt/anchor correspondence binds values only. It does not establish the
custodian's authenticity, prove change authorship, or replace independent
verification. The existing workflow invoker defines and checks those records;
this skill consumes their outcome and does not reimplement it.

## Rule Classification

Use the following classifications in the plan.

### CONFIRMED

A confirmed rule is explicitly supported by the functional specification and
represented consistently by the manifest. It may be planned only within its
stated boundary.

### INFERENCE

An inference records a limited interpretation, typically from presentation. It
is not an implementation permission unless `implementationAllowed` is true in
the manifest and no other condition blocks it. An inference cannot create a
new side effect, dependency, API call, navigation flow, persistence behavior,
or security behavior.

### AMBIGUITY

An ambiguity is missing, conflicting, or incomplete information. If it blocks a
requirement identified by `blocksRequirementIds`, the plan is `BLOCKED` until a
matching authorized decision has independently verifiable evidence.

### AUTHORIZED DECISION

An authorized decision applies only to its listed ambiguity and requirement IDs.
Use it only when its evidence is independently verified through the existing
semantic controls. A name, date, or YAML assertion alone is insufficient.

## Consumer Discovery

Inspect the actual consumer read-only and record only observed facts:

- declared stack and resolved versions;
- component and file-layout conventions;
- TypeScript configuration and naming patterns;
- existing styling approach;
- local test runner, script, configured utilities, result format, and nearby
  test patterns.

Do not infer Angular forms, standalone components, NgModules, React state
libraries, CSS tooling, Jest, Vitest, Karma, Jasmine, or Testing Library from a
framework name. If the planned unit-test intent needs a convention or tool that
cannot be found and safely reused, block executable planning rather than add a
dependency.

## Required Planning Output

Report the consumer type, verified source status, classified rules, detected
conventions, and all required pending runtime checks as `NOT_RUN`. This skill
plans technical work only; it does not create code, invoke consumer commands,
or claim runtime evidence.
