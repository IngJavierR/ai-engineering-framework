# Mockup-to-Component Conversion

## Purpose

Convert a verified self-contained HTML mockup into a framework-neutral plan for
native Angular or React components, without treating HTML as a business
specification or importing its execution environment.

## Permitted Translation

Use the mockup as visual and semantic reference only. Plan to preserve the
following when they are consistent with confirmed requirements and consumer
conventions:

| Mockup element | Planning treatment |
| --- | --- |
| Semantic elements such as `main`, headings, `form`, `label`, `input`, and `button` | Map to native template or JSX structure with equivalent applicable semantics. |
| Visible text and control names | Preserve when required or when they do not conflict with the specification. |
| Label-to-control association, accessible names, `aria-*`, `name`, `type`, and `autocomplete` | Preserve or adapt natively when applicable, keeping controls accessible to the required unit-test intent. |
| Local presentation styles | Translate the visual intent through the consumer's existing style convention only. |
| Declared, hashed assets | Plan their use only from their declared source and allowed destination. |

The plan must identify which mockup elements map to which conceptual components
and which requirements or unit-test cases observe them.

## Prohibited Translation

Do not copy, execute, or infer behavior from:

- `<script>` elements;
- inline event handlers such as `onclick`;
- remote imports, CDN links, trackers, analytics, or external URLs;
- generated bundler metadata;
- undeclared assets or dependencies;
- visual affordances that lack a confirmed functional rule.

A visual submit, save, cancel, navigation, dialog, API, loading, or persistence
cue does not authorize the corresponding behavior. Plan only the behavior
confirmed by the specification and represented by applicable `UT-*` cases.

## Styles and Dependencies

Inspect the consumer to determine its established style mechanism. The plan may
reuse that mechanism only inside the allowed scope. It must not introduce a UI
library, CSS framework, icon package, reset, CDN resource, build configuration,
or package change automatically.

If the mockup requires a visual outcome that cannot be planned with an existing
consumer convention inside scope, report the gap. Do not solve it by changing a
protected configuration file or adding a dependency.

## Native Component Boundaries

Use conceptual components declared in the manifest as the starting boundary.
Do not split or merge them solely because of HTML nesting. A technical component,
validator, utility, hook, or other unit may be planned when it supports a
confirmed requirement and the unit-test contract identifies a compatible target.

For each planned unit, record:

- conceptual component ID;
- mockup elements represented;
- confirmed requirements served;
- related YAML unit-test cases;
- planned technical destination;
- consumer convention on which the plan relies.

## Accessibility and Unit-Testability

Preserve semantic structure and accessible labels needed by confirmed
requirements. Where the unit-test contract expects a role or accessible name,
plan a native element or supported equivalent that enables a DOM-simulated unit
test. This is not a complete accessibility certification and does not expand M2
into browser, E2E, performance, or security testing.

## Conversion Inventory

Include a conversion inventory in the planning report with these columns:

| Mockup source | Conceptual component | Planned native representation | Requirement / case linkage | Notes |
| --- | --- | --- | --- | --- |

Mark a source element as `not-planned` when it would require unconfirmed
behavior, a new dependency, or an out-of-scope destination. Such an entry must
state the blocking reason or limitation.
