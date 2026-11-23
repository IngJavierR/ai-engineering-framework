# Backend Test Cases

Declare backend test cases in `test-cases.yaml` using `backend-test-cases/v1`.
Each case identifies an OpenAPI `operationId`, HTTP method and path, a level
(`unit`, `integration`, or `contract`), classifications, request data, and the
expected status and response schema.

Provide a successful 2xx or 3xx case for every operation. Add negative cases
for every operation with a request body or required parameter. Cover declared
constraints such as required properties, type, format, length, bounds, enums,
and `additionalProperties` where applicable. Include authorized security and
regression cases without inventing identity behavior.

Test levels describe evidence, not implementation shortcuts: unit tests cover
isolated behavior, integration tests cover service dependencies, and contract
tests validate real HTTP requests and responses against the approved contract.
Report the execution result for every `TC-*` identifier.
