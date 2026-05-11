# ADR 0004: CLI and TUI must share one application core

## Status

Accepted

## Context

The project will expose both a command-line interface and an interactive terminal UI. Duplicating business logic across both surfaces would slow delivery and create drift.

## Decision

The CLI and TUI will both consume the same application services and use cases. Neither interface may call Microsoft Graph directly.

## Consequences

### Positive

- reduced duplication
- consistent behavior across both interfaces
- easier testing
- safer AI-assisted contributions because logic lives in one place

### Negative

- requires more upfront structure than a throwaway prototype
- forces discipline around abstractions early

## Alternatives considered

### Separate code paths for CLI and TUI

Pros:

- may feel faster in a very early prototype

Cons:

- duplicated logic
- inconsistent error handling
- higher long-term maintenance cost

## Notes

This decision is central to the repository design. New features should first be added to the application layer, then surfaced in the CLI and/or TUI.
