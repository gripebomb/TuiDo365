# ADR 0003: Use SQLite for local cache and state

## Status

Accepted

## Context

The application benefits from a local cache for faster startup, offline reads, and future incremental sync state. The persistence layer should be simple, reliable, and friendly to Linux desktop and terminal use.

## Decision

Use SQLite for local cache and lightweight application state.

## Consequences

### Positive

- zero separate service dependency
- stable and well understood
- good fit for local desktop/CLI applications
- easy to inspect and test

### Negative

- schema migration discipline is needed over time
- not ideal for multi-process high-write concurrency, though that is not a major concern here

## Alternatives considered

### JSON files

Pros:

- very easy to start

Cons:

- weak query capabilities
- awkward incremental updates
- poor fit for sync metadata and future delta state

### DuckDB

Pros:

- powerful local analytics capabilities

Cons:

- more capability than needed for the first use case
- less conventional for simple local app-state storage

## Notes

SQLite should initially store cached lists, cached tasks, freshness metadata, and future sync tokens.
