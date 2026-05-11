# CLAUDE.md

This file gives AI coding agents and human contributors a practical execution plan for building `TuiDo365`.

## Project summary

`TuiDo365` is a Linux-first terminal Microsoft To Do client built on Microsoft Graph, with:

- a Typer CLI
- a Textual TUI
- a shared application core
- delegated Microsoft identity authentication using MSAL

## Build philosophy

Favor a thin vertical-slice workflow over broad unfinished scaffolding.

Start with a minimal but real path from:

- user command
- to auth
- to Graph call
- to mapped domain model
- to terminal output

## Priority order

### Milestone 1

- ~~project scaffolding~~ ✅
- ~~config/path utilities~~ ✅
- ~~logging setup~~ ✅
- ~~domain models (TaskList, Task, enums)~~ ✅
- ~~domain error hierarchy~~ ✅
- ~~basic tests~~ ✅ (150 passing)
- auth adapter using device-code flow
- `tuido login`
- `tuido lists`
- `tuido tasks --list <name>`

### Milestone 2

- `tuido add`
- `tuido update`
- `tuido done`
- `tuido delete`
- list create/rename/delete with built-in list guardrails
- JSON output mode

### Milestone 3

- TUI skeleton
- list sidebar
- task table
- task detail view
- refresh/search shortcuts

### Milestone 4

- sqlite cache
- offline reads
- sync freshness indicators
- packaging polish
- user docs and demo assets

## Mandatory constraints

- CLI and TUI must share application services
- no direct Graph usage from presentation code
- no live network dependence in CI tests
- do not add browser auth before device code flow works
- do not implement Planner features in this repo

## Suggested initial code skeleton

```text
src/mtd/
  main.py
  domain/
  app/
  infra/
  cli/
  tui/
```

## Recommended first classes/modules

1. `config.paths`
2. `config.settings`
3. `infra.logging.setup`
4. `infra.auth.token_cache`
5. `infra.auth.msal_client`
6. `infra.graph.client`
7. `infra.graph.todo_api`
8. `domain.models`
9. `app.services.auth_service`
10. `app.services.list_service`
11. `app.services.task_service`
12. `cli.app`
13. `cli.auth_commands`
14. `cli.list_commands`
15. `cli.task_commands`

## Implementation rules

### Auth

- wrap MSAL in a project-owned adapter
- return normalized auth results/errors
- store token cache under Linux user state paths
- support future fallback auth methods without changing CLI command contracts

### Graph integration

- centralize Graph base URL handling
- centralize bearer token injection
- centralize retry/throttling handling
- map Graph payloads into internal models before returning upstream

### Domain models

Keep them simple and explicit.

Avoid leaking Graph-specific nested shapes above infrastructure unless they are intentionally represented in the domain.

### CLI

- commands should parse input and delegate immediately
- commands should not own business logic
- add `--json` wherever scripting value is high

### TUI

- keep widgets presentation-only
- move mutations through application services
- use an app/state layer instead of embedding fetch/update logic in widgets

## Quality gates

Before calling a milestone complete:

- `ruff check .` passes
- `ruff format --check .` passes
- `mypy src` passes
- `pytest` passes

## Good task shapes for AI agents

- “Implement Linux XDG path helpers and tests”
- “Create Graph To Do repository interface and DTO mapper”
- “Add list-lists use case and wire Typer command”
- “Implement built-in list mutation guard and tests”

## Bad task shapes for AI agents

- “Build the whole app”
- “Add all sync features”
- “Refactor everything for cleanliness”

## Acceptance criteria for the first usable release

A user on Linux can:

1. install the package
2. run `tuido login`
3. authenticate successfully with device-code flow
4. list task lists
5. view tasks in a chosen list
6. add and complete a task
7. receive understandable errors when auth or permissions fail

## Documentation discipline

Update docs when:

- architecture changes
- a new dependency is added
- auth behavior changes
- config schema changes
- CLI contracts change

## Final note

Optimize for correctness, small increments, and preserving boundaries. A modest but reliable shared core is more valuable than a flashy TUI built on unstable foundations.
