# React Consumer Discovery

## Purpose

Establish the verified React capabilities and local conventions required to
execute an approved `frontend-ui-design` plan. Discovery is read-only and must
precede any consumer change.

## Identity and Governance Preconditions

Confirm all of the following before implementation:

| Precondition | Required evidence | Block when |
| --- | --- | --- |
| Shared plan | `frontend-ui-design` result is `READY_FOR_IMPLEMENTATION`. | The plan is missing, blocked, incomplete, or names another stack. |
| Manifest identity | Same feature, input manifest, React consumer, inputs, scope, and baseline as the plan. | Feature, hash, consumer, baseline, or scope diverges. |
| Executable manifest | `templateStatus` is `ready-for-execution`; required facts and decisions are verified. | Manifest is illustrative or contains unverified blocking facts. |
| Structural and semantic checks | Existing M2 validators succeeded for the exact input identity. | Any validation is failed, blocked, unavailable, or belongs to another input. |
| PREPARE | Successful PREPARE for the exact manifest and consumer. | PREPARE is absent, failed, blocked, or belongs to another identity. |
| Receipt and anchor | Values correspond to the same execution ID, manifest hash, inputs, consumer, base commit, and snapshot hash. | Receipt or anchor is absent, malformed, divergent, or not independently supplied. |

Receipt and anchor correspondence proves only value correspondence. It does not
authenticate a custodian, prove provenance or authorship, or prove that no
intermediate changes were later reverted.

## Required Read-Only Inspection

Inspect only the real authorized consumer and record observed facts:

1. **Package and lock resolution**
   - Locate the manifest and lockfile declared by `consumer.detection`.
   - Record resolved React, TypeScript, runner, and test-utility versions only
     when they can be verified from the actual consumer.
   - Do not infer installed versions from semver ranges alone.

2. **Build and TypeScript configuration**
   - Identify the existing build, JSX/TSX transform, TypeScript, lint, DOM, and
     test configuration files only for inspection.
   - Determine source roots, module resolution, path aliases, file extensions,
     naming rules, and existing command scripts.
   - Do not modify configuration merely to make an implementation possible.

3. **Component architecture and composition**
   - Record local component organization, props conventions, composition,
     children patterns, error/display patterns, and co-location rules.
   - Identify existing use of function components, memoization, refs, context,
     and other React APIs only where they are actually used in the feature area.
   - Preserve observed patterns; do not introduce a new architectural style.

4. **Hooks and state**
   - Identify the feature area's existing hook conventions and state mechanism:
     local state, reducer, context, external store, or another verified pattern.
   - Determine local rules for custom hooks, state ownership, derived values,
     validation, normalization, and cleanup.
   - Do not add state-management libraries, providers, or global abstractions.

5. **Styles and assets**
   - Identify the established style format and scoping approach, such as local
     CSS, modules, CSS-in-JS, or another existing mechanism.
   - Identify permitted asset handling and local design primitives, if any.
   - Reuse only conventions and dependencies already present and within scope.

6. **Routes and external boundaries**
   - Identify routes only to preserve boundaries and determine whether they are
     protected. Do not add navigation, route changes, HTTP calls, persistence,
     authentication, or side effects unless explicitly confirmed, authorized,
     and in scope.

7. **Unit-test tooling and DOM environment**
   - Identify the installed and configured runner and utilities from real files
     and nearby tests: Jest, Vitest, React Testing Library, or another consumer
     tool.
   - Verify the simulated DOM environment, reporting, fake timers, async
     helpers, mocks, and command scripts actually configured for the consumer.
   - Do not install, swap, or configure a runner or utility.

## Capability Decision

A capability is usable only if its package, configuration, DOM environment, and
applicable consumer convention can be verified. Record each requirement as
available, not-applicable, or blocked.

| Required capability | Satisfying evidence | Block condition |
| --- | --- | --- |
| React component implementation | Existing compatible component pattern and allowed destinations. | Required files would be protected or architecture is indeterminate. |
| Props, hooks, or state behavior | Existing approach can represent confirmed rules. | The plan requires behavior unsupported by verified local patterns. |
| Component unit test | Existing runner and simulated DOM can render and query required component behavior. | No compatible configured runner or DOM facility exists. |
| React Testing Library | Installed and configured React Testing Library where the plan selects it. | The plan requires it but it is unavailable or only a dependency/configuration change would enable it. |
| Hook, validator, or utility test | Existing test pattern can invoke the planned unit directly. | Required test capability is unavailable or not deterministic. |
| Async case | Existing utilities can honor declared mechanism, timer control, completion, and cleanup. | Determinism cannot be preserved. |

If a capability is unavailable, do not solve it by editing `package.json`, a
lockfile, build/test configuration, routing, or another protected path. Report
`BLOCKED` and the missing capability.

## Discovery Record

The implementation report must include:

- verified React, TypeScript, runner, and test-utility versions;
- component, props, hooks, state, styles, and asset conventions to be reused;
- verified DOM simulation and async/mock facilities;
- allowed planned destinations and protected exclusions;
- selected existing commands, if any, for build, typecheck, and unit tests;
- unavailable capability and block reason, or `NOT_RUN` execution checks.

Discovery does not execute build, typecheck, or tests and does not itself create
runtime evidence.