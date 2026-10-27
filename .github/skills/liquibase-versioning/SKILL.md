---
name: liquibase-versioning
description: >
  Design and generate versioned Liquibase XML changesets
  for any database structural change, including tables,
  columns, constraints, indexes, schemas, sequences,
  views, triggers, functions and other schema objects.
  Use for new projects and existing databases.
  Preserve applied changesets, assess compatibility,
  document rollback and plan validation.
---

# Liquibase Structural Versioning

## Mission

Manage ALL database structural changes through
versioned Liquibase XML changelogs.

This skill supports:
- New database schemas.
- Existing database schema evolution.
- Structural changes requested directly.
- Structural changes required indirectly by
  application or API development.

This skill does not manage ordinary business DML
unless explicitly requested.

## Mandatory Governance

Before performing a task, follow:
- Repository-wide instructions.
- Applicable liquibase.instructions.md policy.
- Project-specific database conventions.
- Active client policies, when available.

Never bypass mandatory policies.

## Workflow

### 1. Identify Change Type

Classify the request as:
- CREATE_STRUCTURE
- ALTER_STRUCTURE
- DROP_STRUCTURE
- NO_STRUCTURAL_CHANGE
- UNCERTAIN

Determine:
- Database engine and supported version.
- Existing or new project.
- Affected database objects.
- Required compatibility guarantees.

Do not assume that the database is empty.

### 2. Inspect Existing State

When working on an existing project:

- Locate the root Liquibase changelog.
- Inspect changelog include ordering.
- Identify naming and directory conventions.
- Review existing changesets.
- Identify constraints and dependencies.
- Determine whether execution history is available.
- Establish a verifiable baseline for applied changeset content when
  immutability must be checked.

Never assume that an existing changeset is safe
to modify because its deployment state is unknown.

Never invent hashes. Use content or hashes calculated from a real
baseline, such as the approved source revision or deployment artifact.

### 3. Analyze Impact

Evaluate:
- Existing application consumers.
- Schema backward compatibility.
- Locking and operational risks.
- Data preservation.
- Referential integrity.
- Potential destructive operations.
- Rollback feasibility.

For rules enforced by indexes or constraints, identify whether their
correctness depends on concurrent operations and plan concurrency
tests when it does.

Prefer additive changes for existing systems.

For destructive changes, require explicit approval.

### 4. Design Changesets

Generate new Liquibase XML changesets.

Requirements:
- Unique ID, author and changelog path.
- Preserve existing changesets.
- Prefer native Liquibase XML change types.
- Use database-specific SQL only inside
  XML changesets when necessary.
- Keep changesets focused.
- Follow existing naming conventions.
- Include new files in the root changelog.
- Avoid runAlways or runOnChange unless
  explicitly justified and approved.

Use references/xml-conventions.md for examples
and additional structural conventions.

### 5. Preconditions

Use meaningful preconditions when the database
state or deployment assumptions require them.

Do not automatically use MARK_RAN or CONTINUE
to hide unexpected schema differences.

Unexpected precondition failures must normally
stop execution for investigation.

### 6. Rollback and Recovery

Assess reversibility.

For reversible changes:
- Define an appropriate rollback where needed.
- Avoid destructive rollback of pre-existing data.

For irreversible or high-risk changes:
- Document recovery requirements.
- Require appropriate approval.

Never promise that rollback is safe without
validation.

Explicitly document that dropping a column or structural object can
remove data written after deployment. Prefer forward recovery when a
rollback would discard data that must be retained.

### 7. Validation Plan

When tooling is available, validate:

- XML structure and Liquibase changelog syntax.
- Duplicate changeset identities.
- Root changelog inclusion.
- Applied changeset integrity against the established baseline.
- Application on a temporary PostgreSQL database with the previous
  schema and representative existing records for evolutionary changes.
- Expected resulting schema.
- Repeat execution behavior.
- Data preservation and one DATABASECHANGELOG entry per changeset.
- Index and constraint behavior against the real database engine.
- Concurrent operations when a changed rule depends on concurrency,
  including uniqueness where applicable.
- Rollback when safe and applicable.

When Docker or Testcontainers is selected for validation, record the
runtime and compatibility checks. Neither tool is required unless the
project selects it.

Report NOT_RUN for every check not executed.

### 8. Deliverables

Provide:
1. Change classification.
2. Impact analysis.
3. XML changesets.
4. Root changelog changes.
5. Compatibility analysis.
6. Rollback or recovery strategy.
7. Validation results.
8. Remaining risks.

For validation results, use these evidence states:
- GENERATED: XML or related artifacts were produced.
- COMPILED: applicable compilation succeeded with evidence.
- TESTED: checks ran with verifiable results and known scope.
- VALIDATED: declared acceptance criteria have sufficient evidence.

Generated artifacts, static review, or partial checks alone do not
justify VALIDATED. Report NOT_RUN for applicable pending checks.

## Safety

Never:
- Execute uncontrolled schema DDL.
- Modify applied changesets.
- Drop structural objects without approval.
- Invent database metadata.
- Claim tests passed without running them.
- Replace existing changesets to simplify work.
- Generate production deployment commands
  without identifying their operational risks.

## Completion Status

Use:
- READY_FOR_VALIDATION
- VALIDATED
- BLOCKED

Use VALIDATED only when all mandatory executable
checks were performed successfully.

Use READY_FOR_VALIDATION for generated changes
whose required runtime checks remain pending.
