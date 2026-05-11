# Architecture

## Overview

`TuiDo365` is a Linux terminal client for Microsoft To Do built on Microsoft Graph. The system is intentionally structured so that both the CLI and the TUI share the same application and infrastructure layers.

The architecture optimizes for:

- maintainability
- testability
- AI-assisted implementation
- Linux-friendly operation
- clear separation of concerns

## Architectural style

The project uses a layered architecture with lightweight domain modeling.

### Layers

1. **Presentation layer**
   - CLI commands implemented with Typer
   - TUI screens and widgets implemented with Textual

2. **Application layer**
   - use cases
   - orchestration services
   - validation and formatting logic that is not UI-specific

3. **Domain layer**
   - task and list models
   - enums and business rules
   - domain-specific errors

4. **Infrastructure layer**
   - Microsoft Graph client
   - MSAL authentication adapter
   - local SQLite cache
   - filesystem config and token storage
   - logging

## Dependency direction

Dependencies must flow inward.

- presentation depends on application
- application depends on domain and abstractions
- infrastructure implements abstractions for application use
- domain depends on nothing external beyond the standard library and minimal model helpers

The UI layer must never call Graph directly.

## High-level module map

```text
src/mtd/
  cli/        # Typer entrypoints and command bindings
  tui/        # Textual app, screens, widgets, state adapters
  app/        # use cases, app services, output formatting
  domain/     # models, enums, rules, exceptions
  infra/      # auth, graph, cache, config, logging
```

## Primary execution flows

### Login flow

1. user runs `tuido login`
2. CLI calls application auth use case
3. auth use case delegates to the MSAL adapter
4. device-code flow is started
5. token is acquired and persisted to token cache
6. application returns a sanitized success result

### Read tasks flow

1. user runs `tuido tasks --list "Tasks"`
2. CLI resolves list input and calls application task service
3. task service uses Graph To Do repository
4. infrastructure client fetches task lists/tasks from Microsoft Graph
5. Graph DTOs are mapped into domain models
6. presentation layer renders a table or JSON payload

### TUI interaction flow

1. TUI screen dispatches an intent such as refresh, add task, or complete task
2. state store invokes an application use case
3. application layer performs the operation through the same service abstractions used by the CLI
4. state store updates the UI model
5. widgets re-render from state

## Domain model boundaries

The domain layer should contain simple project-owned models rather than passing Graph response payloads throughout the app.

### TaskList

Fields should include:

- `id`
- `display_name`
- `wellknown_list_name`
- `is_owner`
- `is_shared`

### Task

Fields should include:

- `id`
- `list_id`
- `title`
- `status`
- `importance`
- `body`
- `due_at`
- `start_at`
- `reminder_at`
- `completed_at`
- `last_modified_at`
- `etag`
- optional categories metadata

## Application services

The application layer should provide focused services and use cases.

### Candidate services

- `AuthService`
- `ListService`
- `TaskService`
- `SyncService`

### Candidate use cases

- login
- logout
- list_lists
- list_tasks
- add_task
- update_task
- complete_task
- delete_task
- refresh_cache

Use cases should be thin and predictable so they are easy to test and easy for AI agents to extend without damaging adjacent modules.

## Infrastructure components

### Auth adapter

Wrap MSAL behind a narrow project-owned interface.

Responsibilities:

- start device-code flow
- acquire and refresh tokens
- persist token cache securely
- expose user-facing auth errors in normalized form

### Graph client

Provide a small, typed wrapper around the Graph To Do endpoints.

Responsibilities:

- inject bearer tokens
- handle retryable errors
- parse Graph responses
- map Graph data to project-owned DTOs
- expose task/list operations via repository-style methods

### Cache store

SQLite is the first persistence choice.

Responsibilities:

- cache task lists and tasks
- store freshness metadata
- support offline reads later
- prepare for delta-token storage in future sync work

### Config and paths

Use XDG-friendly Linux paths.

Responsibilities:

- resolve config location
- resolve state/cache/log locations
- create directories as needed
- enforce file permissions where practical

## Error handling

Normalize errors at the application boundary.

Categories:

- auth failures
- permission failures
- network failures
- throttling / retry-after
- not found
- invalid user input
- immutable built-in list operations
- cache/database errors

Presentation layers should never render raw Graph or MSAL stack traces to end users.

## Observability

The system should use structured logging early.

Minimum requirements:

- debug logs for HTTP and sync internals only when enabled
- token redaction
- request correlation IDs when possible
- concise user-facing error messages

## Security posture

- never store passwords
- do not log tokens or authorization headers
- use delegated permissions only as needed
- keep token cache and config under user-owned Linux paths
- prefer least-privilege scopes

## Offline design direction

Offline mode is not required in the first vertical slice, but the architecture should allow it cleanly.

Future design:

- network-first reads by default
- `--offline` mode for cached reads
- store cache age and sync status
- support delta-based sync later to avoid repeated full fetches

## Testing strategy

### Unit tests

- domain rules
- use cases
- date parsing
- output formatting
- built-in list operation guards

### Integration tests

- Graph client with mocked HTTP
- auth adapter with test doubles
- sqlite cache repositories

### Manual tests

- device-code login on Linux desktop
- device-code login over SSH
- list tasks
- add/update/complete/delete task
- error handling for built-in lists

## Future extensibility

Areas intentionally left open:

- browser-based auth fallback
- richer search and filtering
- notifications
- packaging as a standalone binary
- AUR packaging
- delta sync
- categories and advanced metadata editing

## Rules for contributors and AI agents

- Keep Graph response shapes out of UI modules.
- Prefer adding a use case over embedding logic in commands/widgets.
- Add tests with each feature.
- Avoid introducing dependencies that collapse boundaries.
- Preserve Linux-first pathing and ergonomics.
