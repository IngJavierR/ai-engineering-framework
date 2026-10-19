
---
applyTo: "**/db/**,**/database/**,**/liquibase/**,**/*changelog*.xml,**/persistence/**"
---

# Database Structural Change Governance

## Purpose

Enforce version control of all database
structural changes using Liquibase XML.

This policy applies to new and existing projects.

## Mandatory Rules

1. ALL database structural changes MUST be
   represented by Liquibase XML changesets.

2. Never execute structural changes outside
   the approved Liquibase lifecycle.

3. Never use Hibernate or JPA automatic DDL
   to create or modify managed schemas.

4. Never modify, delete or reuse a changeset
   that has already been executed.

5. Every new structural change requires
   a new uniquely identified changeset.

6. Do not silently introduce destructive
   or backward-incompatible changes.

7. Every changeset must be included in the
   project's root database changelog.

## Structural Changes Covered

The policy includes:

- Schemas and tables
- Columns and data types
- Primary and foreign keys
- Unique and check constraints
- Indexes
- Sequences
- Views and materialized views
- Functions and stored procedures
- Triggers
- Database-specific types
- Partition definitions
- Structural object permissions
- Other database schema objects

## Required Format

- Use Liquibase XML changelogs.
- Prefer native Liquibase XML change types.
- Embedded SQL is allowed only inside XML
  changesets when required for unsupported
  database-specific operations.
- Each changeset needs a unique ID and author.
- Follow project-specific naming conventions.
- Keep changesets small and independently
  understandable.

## Backward Compatibility

For existing systems:

- Prefer additive changes.
- Preserve existing schema consumers.
- Evaluate compatibility before removing
  or renaming objects.
- Use expand-and-contract when necessary.
- Require explicit approval for destructive
  changes.

## Rollback

- Assess rollback feasibility for every change.
- Define an explicit rollback when appropriate.
- If rollback is unsafe or impossible, document
  the limitation and recovery strategy.
- Never invent a destructive rollback merely
  to satisfy a checklist.

## Data Operations

Normal application DML is outside the scope
of this structural-change policy.

Do not introduce data migrations or seed data
unless explicitly requested and approved.

## Validation

When executable tooling is available:

1. Validate the XML changelog.
2. Check for duplicate changeset identities.
3. Verify previously executed changesets
   remain unchanged.
4. Apply the changelog to a temporary database.
5. Verify the resulting database structure.
6. Check repeat execution behavior.
7. Report compatibility and rollback risks.

Never report PASS for checks not executed.

## Completion Report

Include:

- Structural objects affected
- New changelog files
- Changeset identifiers
- Compatibility assessment
- Validation results
- Rollback or recovery strategy
