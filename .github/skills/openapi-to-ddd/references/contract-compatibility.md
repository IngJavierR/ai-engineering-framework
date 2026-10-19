
# OpenAPI Contract Compatibility

## Purpose

Preserve existing API consumers when implementing
new operations or evolving existing contracts.

## Required Inputs

- Baseline OpenAPI contract
- Proposed OpenAPI contract
- Available consumer requirements
- API versioning policies

If the baseline is missing, report compatibility
as NOT_VERIFIED.

## Potential Breaking Changes

Review changes involving:
- Removed paths or HTTP methods
- Renamed parameters
- Required request parameters
- Newly required request properties
- Removed response properties
- Changed property types or formats
- Changed response status codes
- Changed authentication requirements
- Changed error response contracts
- Changed media types
- Narrowed validation constraints

Compatibility depends on the direction
of communication and consumer expectations.

## Potentially Compatible Changes

Examples:
- Adding a new endpoint.
- Adding an optional request property.
- Adding a new optional capability.

Important:
A new response property is not automatically
compatible with every consumer. Strict clients
may reject unknown fields.

Do not classify changes solely from this list.

## Compatibility Dimensions

Analyze:
1. Schema compatibility
2. HTTP contract compatibility
3. Behavioral compatibility
4. Consumer compatibility
5. Database compatibility

A successful OpenAPI diff does not prove
behavioral or consumer compatibility.

## Existing Projects

Before implementing:
- Preserve the baseline contract.
- Identify affected endpoints and consumers.
- Evaluate old requests against the new API.
- Evaluate new responses against old expectations.
- Preserve supported error semantics.
- Report undocumented behavior as a risk.

## Required Test Matrix

For each affected operation:
- Existing valid request
- Existing invalid request
- Required parameter validation
- Optional parameter behavior
- Response schema conformance
- Status code verification
- Authorization behavior
- Relevant boundary conditions

For changed operations, include baseline
regression scenarios.

## Status

Use:
- COMPATIBLE_WITH_EVIDENCE
- POTENTIALLY_COMPATIBLE
- BREAKING_CHANGE
- NOT_VERIFIED

Only use COMPATIBLE_WITH_EVIDENCE when supported
by executed checks appropriate to the change.

## Reporting

Document:
- Baseline version
- Proposed version
- Affected operations
- Compatibility findings
- Tests executed
- Tests not executed
- Known risks
