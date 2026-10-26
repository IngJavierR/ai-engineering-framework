
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

## Directional Analysis

Assess each direction separately:

| Direction | Question |
| --- | --- |
| Backward request compatibility | Can existing requests be accepted by the proposed API? |
| Forward request compatibility | Can proposed requests be accepted by the currently deployed API when rollout needs it? |
| Backward response compatibility | Can existing consumers interpret proposed responses? |
| Forward response compatibility | Can proposed consumers interpret responses from the currently deployed API when rollout needs it? |

Evaluate strict consumers explicitly. Adding an optional response
property can still fail a consumer that rejects unknown properties.

Optional, omitted and null values are distinct. Record separately:
- whether a property is required by OpenAPI
- whether it may be omitted from JSON
- whether JSON null is allowed
- whether the persistence representation permits null

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

When applicable, include negative validation cases for:
- missing required properties
- invalid property types
- invalid formats
- minimum and maximum lengths or other declared bounds
- declared constraints
- additionalProperties behavior

Validate runtime HTTP requests and responses against the contract.
Parsing YAML, resolving references, or checking generated DTOs alone
does not establish HTTP contract conformance.

## Validator Coverage

Document the validator, version, supported OpenAPI constructs and
unsupported constructs used by the contract. A validator with partial
coverage may provide TESTED evidence for its supported scope, but it
does not establish complete OpenAPI conformance.

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
