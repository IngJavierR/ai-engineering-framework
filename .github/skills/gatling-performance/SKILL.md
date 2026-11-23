---
name: gatling-performance
description: Design, execute, and document controlled Gatling performance tests against authorized local or non-production HTTP targets.
---

# Gatling Performance

## Mission

Create reproducible Gatling performance evidence for an authorized HTTP target
and record its architectural impact. This skill supports smoke, baseline, and
controlled stress profiles.

## Safety and target control

- Use only a local or explicitly authorized non-production base URL.
- Require the base URL through configuration; never hardcode a production
  destination.
- A standard Gatling Maven `pom.xml`, including XML namespaces, is valid. Read
  the target base URL from `TARGET_BASE_URL` in simulation configuration.
- Do not use third-party services, customer data, destructive endpoints, or
  unbounded arrival rates.
- Make test data unique and keep the target environment disposable.
- Stop if the resolved target is not a loopback address or an explicitly
  authorized environment.

## Profiles

Document each profile's users, ramp, duration, assertions, target URL, and
environment limitations:

| Profile | Purpose | Required behavior |
| --- | --- | --- |
| smoke | Verify connectivity and request correctness. | One or few requests; fail on HTTP or assertion errors. |
| baseline | Establish a repeatable local reference. | Bounded concurrent load and explicit latency/error thresholds. |
| stress | Find a controlled local saturation signal. | Short, capped load; never use as a production capacity claim. |

## Execution evidence

Run Gatling with an existing build integration. Preserve its generated report
outside version control, then record the exact command, profile, report path,
requests, failures, latency percentile, throughput, and thresholds in a stable
Markdown report.

Do not mark a profile as passed if it was not executed. A local result is not a
production capacity certification.

## Architecture 4+1 and ADR

For the evaluated system, update Markdown documentation containing Mermaid
diagrams for:

1. logical view;
2. process view;
3. development view;
4. physical/deployment view; and
5. scenario view.

Create an ADR for material choices such as load profiles, target isolation, or
threshold semantics. State consequences, rejected alternatives, and validation
limits. Mermaid syntax must be simple and renderable by standard GitHub
Markdown.
