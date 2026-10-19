
# GitHub Copilot Instructions

You are contributing to the AI Engineering Framework.

## Mandatory Context

Follow the engineering principles defined
in AGENTS.md.

## Repository Purpose

This repository defines reusable engineering
practices for GitHub Copilot.

It is not a business application.

## Development Guidelines

- Make minimal, focused changes.
- Follow the existing repository structure.
- Avoid duplicated instructions.
- Never assume that a future capability
  has already been implemented.
- Do not introduce dependencies without
  explaining their purpose.
- Maintain documentation consistency.

## Change Management

Before implementing any change:

1. Understand the requested scope.
2. Identify affected files.
3. Describe the intended changes.
4. Implement only authorized changes.
5. Report what was changed.
6. State which validations were executed.

## Important

The framework will support multiple clients,
projects, and technology stacks.

Avoid assumptions that would prevent
future extensibility.

## API and Database Governance

When working on Java APIs:

- Follow the applicable OpenAPI and DDD standards.
- Preserve approved API contracts.
- Perform compatibility analysis for existing APIs.

For ANY database structural change:

- Liquibase XML is mandatory.
- Do not execute uncontrolled DDL.
- Do not enable automatic schema generation.
- Preserve executed changesets.
- Validate structural changes before completion.

These rules apply even when database changes
are triggered indirectly by Java application work.
