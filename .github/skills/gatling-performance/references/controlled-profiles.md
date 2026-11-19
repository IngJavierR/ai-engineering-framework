# Controlled Gatling Profiles

Keep profile values in environment variables or Maven properties. Default to a
loopback URL and reject other targets in the simulation itself.

Recommended local defaults are deliberately modest:

- smoke: one user and one request;
- baseline: four concurrent users over ten seconds;
- stress: twelve concurrent users over fifteen seconds.

Set thresholds as acceptance criteria for the current disposable environment,
not service-level objectives. Capture Gatling's response-time percentiles,
request count, error count, and requests per second from its report.

Use only idempotent GET endpoints where possible. When a create endpoint is
necessary to seed a test, generate a unique value and do not include it in the
throughput assertions for the evaluated read path.
