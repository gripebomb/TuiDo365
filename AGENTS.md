# AGENTS.md

This repository is intended for AI-assisted development. Follow these rules when planning or implementing changes.

## Primary mission

Build a Linux-first terminal client for Microsoft To Do that uses Microsoft Graph and supports both CLI and TUI workflows from one shared application core.

## Source of truth

When implementation details are unclear, prefer these sources in order:

1. repository ADRs
2. `docs/architecture.md`
3. current code patterns in `src/`
4. official Microsoft Graph and Microsoft identity documentation

Do not invent Graph fields or auth behaviors when the official docs should be checked.

## Hard boundaries

- Do not call Microsoft Graph directly from `cli/` or `tui/`.
- Do not pass raw Graph response payloads throughout the app.
- Do not put business rules into widget or command files.
- Do not store secrets in the repo, tests, fixtures, or logs.
- Do not add large framework dependencies without documenting the reason.

## Required architecture rules

- UI layers depend on application services/use cases only.
- Application layer depends on domain models and interfaces.
- Infrastructure implements external integrations.
- Domain layer stays small and project-owned.

## Preferred implementation pattern

For a new feature:

1. update or add domain models if needed
2. add or update an application use case/service
3. add infrastructure support if external data is required
4. expose the feature through CLI and/or TUI
5. add tests
6. update docs if behavior changed materially

## File ownership guidance

- `src/mtd/domain/` — business types, rules, project errors
- `src/mtd/app/` — orchestration, use cases, formatting helpers
- `src/mtd/infra/` — Graph, auth, cache, config, logging
- `src/mtd/cli/` — Typer commands only
- `src/mtd/tui/` — Textual presentation only
- `tests/` — unit and integration coverage

## Coding standards

- target Python 3.12+
- prefer typed functions
- prefer small functions over large classes when possible
- use dataclasses or Pydantic models where appropriate
- keep side effects isolated in infrastructure modules
- keep command handlers thin

## Testing expectations

Every meaningful feature should include tests.

Minimum expectations:

- unit tests for business rules and use cases
- mocked integration tests for Graph-facing code
- no reliance on live Microsoft tenants in CI

## Logging rules

- never log bearer tokens
- never log authorization headers
- sanitize user-provided secrets
- keep user-facing messages concise and actionable

## Commit/PR shaping

Prefer small, reviewable increments.

Good examples:

- “Add token cache abstraction and tests”
- “Implement list-lists use case and CLI command”
- “Add task table widget backed by shared TaskService”

Avoid giant mixed changes that alter architecture, UI, auth, and packaging at the same time.

## When blocked

If a feature depends on uncertain Microsoft Graph behavior:

- stop guessing
- verify against official docs
- encode the confirmed behavior in tests or comments

## Definition of done

A task is complete when:

- architecture boundaries are preserved
- tests pass
- lint and type checks pass
- docs are updated when needed
- no secrets are introduced
