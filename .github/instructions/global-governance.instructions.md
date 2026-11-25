---
description: Cross-stack engineering governance for framework consumers.
---

# Global Engineering Governance

- Preserve approved contracts, scope boundaries, and local consumer conventions.
- Validate untrusted input at trust boundaries and do not log secrets or
  sensitive data.
- Keep dependency changes explicit, minimal, and reproducible.
- Do not silently weaken quality, security, migration, or authorization
  controls; document limitations and evidence actually executed.
- Structure backend code with Domain-Driven Design and hexagonal boundaries
  in every stack; follow the `backend-ddd-architecture` skill and the
  installed stack skill.
- Represent database structural changes as Liquibase XML changesets; never use
  ORM automatic DDL to create or modify managed schemas.
- Use client policies only to add rules or select compatible capabilities.
  Mandatory framework controls remain in effect.
