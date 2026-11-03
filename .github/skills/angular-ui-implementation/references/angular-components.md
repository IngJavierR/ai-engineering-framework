# Angular Component Implementation

## Purpose

Implement only the Angular technical units approved by `frontend-ui-design`,
within the manifest scope and according to observed consumer conventions.

## Authorization Matrix

| Action | Allowed only when | Block when |
| --- | --- | --- |
| Create or modify Angular source, template, style, asset, or spec file | The destination is within `allowedPaths`, not in `protectedPaths`, regular, and listed in the approved plan. | Destination is protected, outside scope, unsafe, or absent from the plan. |
| Apply a confirmed rule | It is explicitly traced to `REQ-*` and applicable `CMP-*` / `UT-*`. | It is inferred, ambiguous, or untraced. |
| Apply a decision | It is a verified `DEC-*` that applies to the requirement. | Evidence is absent, revoked, or outside the decision's scope. |
| Delete or rename | The manifest permits it, all paths are allowed and unprotected, and required authorization is verified. | `deletionPolicy` rejects it or any path is protected/out of scope. |
| Reuse a library or tool | It is already installed, configured, compatible, and used consistently by the consumer. | It would introduce a package, CDN, configuration change, or new UI library. |

`protectedPaths` always overrides `allowedPaths`. Do not use globs, traversal,
symlinks, submodules, type changes, or indirect file changes to evade the
manifest scope.

## Angular Structure

Follow the pattern discovered in the consumer:

- For standalone areas, preserve existing standalone imports, providers, and
  composition style.
- For NgModule areas, preserve declarations, imports, exports, and module
  boundaries; do not convert the area to standalone components without explicit
  authorization and scope.
- Preserve established use of signals, inputs, outputs, injection, change
  detection, state, and error-display patterns.
- Preserve existing naming, file layout, TypeScript strictness, and style
  conventions.

Do not create abstractions, global services, route changes, or shared framework
infrastructure unless the approved plan requires them and scope permits them.

## Mockup Translation

Translate only the approved mockup inventory into native Angular template and
style constructs:

- preserve applicable semantic structure, headings, forms, labels, field names,
  accessible names, and declared assets;
- use native property, attribute, and event binding only for confirmed behavior;
- preserve label-to-control association and accessible semantics needed by
  requirements and `UT-*` expectations;
- express visual styling with the established local style mechanism;
- retain an element as visual-only or omit it when it has no confirmed behavior.

Never copy or activate mockup scripts, inline handlers, trackers, CDN links,
remote imports, or generated markup. A visible save, cancel, route, loading,
or API affordance does not authorize persistence, navigation, HTTP, auth, or
other side effects.

## Forms and Validation

Use the existing form approach only when it can express confirmed requirements:

- retain reactive-form, template-driven, signals-based, or local patterns
  actually used by the consumer;
- keep normalization and validation behavior limited to confirmed rules and
  verified authorized decisions;
- make pure validation logic directly testable when the plan and consumer
  conventions support it;
- preserve existing local error representation and display patterns.

Do not introduce API integration, remote validators, persistence, or service
calls from a form unless explicitly confirmed and allowed. An HTML `form` or
button does not itself imply submission behavior.

## Implementation Record

For every technical unit, record for `frontend-ui-output/v1`:

- created or modified regular-file path and resulting content hash;
- change classification and scope result;
- conceptual component IDs, requirement IDs, and YAML case IDs served;
- associated technical test identifiers;
- any unimplemented visual element and its confirmed limitation.

Mark build, typecheck, tests, coverage, and final validation as `NOT_RUN` until
real authorized commands produce evidence.