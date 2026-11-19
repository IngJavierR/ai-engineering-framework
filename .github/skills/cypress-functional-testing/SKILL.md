---
name: cypress-functional-testing
description: Design, execute, and document deterministic Cypress functional tests for authorized local or non-production web applications.
---

# Cypress Functional Testing

## Mission

Translate verified functional requirements and declared test cases into
reproducible Cypress scenarios for an authorized local or non-production web
application. This skill is stack-neutral and does not replace unit, component,
or other browser-testing frameworks.

## Scenario design

- Trace every scenario to `REQ-*` and, where available, `UT-*` identifiers.
- Prefer accessible interactions: labels, roles, names, and native controls.
  Use `data-*` selectors only when accessibility cannot identify a stable
  element; do not add implementation-only selectors by default.
- Cover positive, negative, boundary, normalization, visible feedback, and
  declared primary interactions without inventing APIs, persistence, or
  navigation.
- Keep tests independent: reset local state before each scenario and generate
  unique data whenever stateful local behavior is unavoidable.

## Deterministic local execution

- Target only an authorized local or non-production base URL.
- Start and stop the application through local project commands; do not use a
  production or third-party URL.
- Use Cypress headless with an installed compatible browser.
- Do not rely on arbitrary waits, external HTTP, shared credentials, or test
  ordering.

## Evidence and artifacts

- Configure screenshots on failure and videos when useful for diagnosis.
- Keep generated screenshots, videos, downloads, and reports out of version
  control by default.
- Record the exact command, browser, scenario count, pass/fail count,
  application target, and report locations in stable project documentation.
- A local result proves only the tested local behavior. It does not constitute
  formal governance certification, a production release decision, or a
  performance/security claim.
