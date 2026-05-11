# ADR 0001: Use Python with Typer and Textual

## Status

Accepted

## Context

The project needs to deliver a Linux-first terminal application with both a traditional CLI and an interactive TUI. It should be easy to package, easy to test, and practical for AI-assisted incremental development.

## Decision

Use Python as the primary language.

Use:

- Typer for the CLI
- Textual for the TUI
- httpx for HTTP
- pytest for tests

## Consequences

### Positive

- fast iteration speed
- strong Linux compatibility
- excellent developer ergonomics
- mature terminal ecosystem
- low barrier for contributors and AI agents

### Negative

- runtime distribution is less self-contained than a compiled language by default
- performance is good enough for this use case but not maximal

## Alternatives considered

### Go

Pros:

- easy static binary distribution
- strong CLI ecosystem

Cons:

- weaker TUI ecosystem fit for the desired app style
- slower iteration for AI-heavy prototyping

### Rust

Pros:

- strong performance and safety
- excellent binary distribution story

Cons:

- higher implementation complexity for the first release
- slower ramp for mixed human/AI contributors

## Notes

If packaging becomes a major pain point later, the project can still ship bundled binaries using PyInstaller or Nuitka without rewriting the application.
