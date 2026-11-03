# Angular Consumer Discovery

## Purpose

Establish the verified Angular capabilities and local conventions required to
execute an approved `frontend-ui-design` plan. Discovery is read-only and must
precede any consumer change.

## Identity and Governance Preconditions

Confirm all of the following before implementation:

| Precondition | Required evidence | Block when |
| --- | --- | --- |
| Shared plan | `frontend-ui-design` result is `READY_FOR_IMPLEMENTATION`. | The plan is missing, blocked, incomplete, or names another stack. |
| Manifest identity | Same feature, input manifest, Angular consumer, inputs, scope, and baseline as the plan. | Feature, hash, consumer, baseline, or scope diverges. |
| Executable manifest | `templateStatus` is `ready-for-execution`; required facts and decisions are verified. | Manifest is illustrative or contains unverified blocking facts. |
| PREPARE | Successful PREPARE for the exact manifest and consumer. | PREPARE is absent, failed, blocked, or belongs to another identity. |
| Receipt and anchor | Values correspond to the same execution ID, manifest hash, inputs, consumer, base commit, and snapshot hash. | Receipt or anchor is absent, malformed, divergent, or not independently supplied. |

Receipt and anchor correspondence proves only value correspondence. It does not
authenticate a custodian, prove provenance or authorship, or prove that no
intermediate changes were later reverted.

## Required Read-Only Inspection

Inspect only the real authorized consumer and record observed facts:

1. **Package and lock resolution**
   - Locate the manifest and lockfile declared by `consumer.detection`.
   - Record resolved Angular, TypeScript, and test-tool versions only when they
     can be verified from the actual consumer.
   - Do not infer installed versions from semver ranges alone.

2. **Angular workspace and application configuration**
   - Identify workspace, builder, TypeScript, template, style, and test
     configuration files only for inspection.
   - Determine project and source roots, component naming, file layout, and
     existing path conventions.
   - Do not modify configuration merely to make an implementation possible.

3. **Component architecture**
   - Establish from nearby code whether the applicable area uses standalone
     components or NgModules.
   - Record existing imports, providers, injection style, signals, inputs,
     outputs, change detection, and composition patterns where relevant.
   - Preserve observed patterns; do not introduce a new architectural style.

4. **Forms and validation**
   - Determine whether the feature area uses reactive forms, template-driven
     forms, signals-backed state, or another established local approach.
   - Identify existing validators, error models, normalization patterns, and
     accessible form conventions.
   - Do not add a form library or change global providers.

5. **Styles and assets**
   - Identify the existing component/global style format and encapsulation
     conventions.
   - Identify permitted asset handling and local design primitives, if any.
   - Reuse only conventions and dependencies already present and within scope.

6. **Routes and external boundaries**
   - Identify routes only to preserve boundaries and determine whether they are
     protected. Do not add navigation, route changes, HTTP calls, persistence,
     authentication, or side effects unless explicitly confirmed, authorized,
     and in scope.

7. **Unit-test tooling**
   - Identify the installed and configured runner and utilities from real files
     and nearby tests: Jasmine/Karma, Jest, Vitest, or another consumer tool.
   - Identify DOM simulation, reporting, async helpers, and command scripts.
   - Do not install, swap, or configure a runner or utility.

## Capability Decision

A capability is usable only if its package, configuration, and applicable
consumer convention can be verified. Record each requirement as available,
not-applicable, or blocked.

| Required capability | Satisfying evidence | Block condition |
| --- | --- | --- |
| Angular component implementation | Existing compatible component pattern and allowed destinations. | Required files would be protected or architecture is indeterminate. |
| Form / state behavior | Existing approach can represent confirmed rules. | The plan requires behavior unsupported by verified local patterns. |
| Component unit test | Existing runner can render required DOM-simulated component behavior. | No compatible configured runner or rendering facility exists. |
| Pure validator / utility test | Existing TypeScript test path can invoke the unit directly. | Required test tool is unavailable or only an out-of-scope reconfiguration would enable it. |
| Async case | Existing utilities can honor declared mechanism, timer control, completion, and cleanup. | Determinism cannot be preserved. |

If a capability is unavailable, do not solve it by editing `package.json`, a
lockfile, workspace configuration, routing, or another protected path. Report
`BLOCKED` and the missing capability.

## Discovery Record

The implementation report must include:

- verified Angular, TypeScript, and test-tool versions;
- standalone or NgModule determination and evidence source;
- component, forms, styles, and test conventions to be reused;
- allowed planned destinations and protected exclusions;
- selected existing commands, if any, for build, typecheck, and unit tests;
- unavailable capability and block reason, or `NOT_RUN` execution checks.

Discovery does not execute build, typecheck, or tests and does not itself create
runtime evidence.