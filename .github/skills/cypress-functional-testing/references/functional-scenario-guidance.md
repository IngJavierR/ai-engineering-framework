# Cypress Functional Scenario Guidance

Use a compact traceability matrix:

| Requirement | Existing case | Cypress scenario | Result evidence |
| --- | --- | --- | --- |

Keep an existing Playwright, Selenium, or component-test suite intact. Cypress
adds independent functional evidence and should not duplicate each assertion
unless the requirement needs a browser-level confirmation.

For input validation, verify the observable sequence: locate an accessible
control, enter a value, perform the real interaction such as blur or submit,
then assert the value, validity state, linked message, and text. Include both
inclusive boundaries and their adjacent invalid values when requirements define
them.

In `cypress.config.*`, define a local `baseUrl`, `video`, and screenshot policy.
Ignore generated `cypress/screenshots`, `cypress/videos`, `cypress/downloads`,
and reporter directories unless a project explicitly requires retained evidence.
