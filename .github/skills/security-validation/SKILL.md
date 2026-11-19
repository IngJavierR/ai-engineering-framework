---
name: security-validation
description: Produce evidence-based application security reviews, neutral findings JSON, and manual validation guidance for authorized local projects.
---

# Security Validation

## Mission

Assess an application's real security scope using code, configuration,
dependency, and safe local dynamic evidence. Produce Markdown and neutral JSON
findings suitable for later independent review. This skill is language- and
architecture-neutral.

## Review workflow

1. Verify repository identity, commit, worktree, stack, and authorized scope.
2. Inventory attack surfaces, inputs, data flows, trust boundaries, external
   services, authentication, authorization, and excluded components.
3. Analyze code and configuration for OWASP Top 10 and applicable CWE classes.
4. Run installed or officially supported dependency/static tools locally. Never
   upload source or use automatic dependency remediation during review.
5. Perform only safe checks against an authorized local target. Do not exploit,
   deny service, extract sensitive data, or scan production or third parties.
6. Correlate tool output with code/configuration evidence and deduplicate it.
7. Classify every item as confirmed vulnerability, probable finding, configuration
   risk, hardening recommendation, not applicable, or not evaluated.

## Finding conventions

Each finding needs a stable ID, severity, confidence, CWE/OWASP mapping when
applicable, evidence location, technical explanation, impact, safe manual
validation, remediation, priority, and limitations. Do not report a tool alert
as confirmed without supporting evidence.

Use severity `critical`, `high`, `medium`, `low`, or `informational` and
confidence `high`, `medium`, or `low`. Keep actual secrets and personally
identifying data out of reports.

## Neutral JSON contract

Use the `security-findings/v1` structure:

```json
{
  "schemaVersion": "security-findings/v1",
  "repository": {"name": "", "commit": "", "stack": []},
  "scope": {"included": [], "excluded": []},
  "tools": [{"name": "", "version": null, "command": "", "result": ""}],
  "findings": [{
    "id": "SEC-001",
    "classification": "configuration-risk",
    "severity": "medium",
    "confidence": "high",
    "cwe": [],
    "owasp": [],
    "evidence": [{"path": "", "location": "", "detail": ""}],
    "summary": "",
    "impact": "",
    "manualValidation": [],
    "remediation": "",
    "priority": ""
  }],
  "limitations": []
}
```

## Evidence boundaries

A completed local review is not a production penetration test, security
certification, authorization decision, or claim that all vulnerabilities are
absent. Record untested areas explicitly.
