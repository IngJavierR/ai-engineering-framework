# Security Reporting Guidance

Markdown reports should identify repository, commit, stack, scope, exclusions,
methodology, tool versions, attack-surface inventory, findings, safe manual
validation, remediation, severity summary, reproducible commands, and coverage
limits.

Separate full dependency-tree findings from production-runtime findings. For
frontend tooling, an advisory in a development-only CLI chain may be a
configuration or supply-chain risk rather than a runtime browser vulnerability.

Use safe local dynamic validation to verify controls such as input rejection,
generic error behavior, and explicitly exposed health endpoints. Do not invoke
destructive operations, enumerate sensitive resources, or attempt access
control bypasses.
