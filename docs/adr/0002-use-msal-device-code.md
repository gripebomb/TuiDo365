# ADR 0002: Use MSAL with device-code flow first

## Status

Accepted

## Context

The application targets Linux terminal environments, including desktops and SSH sessions. Authentication must work without assuming a native browser flow is always available or convenient.

## Decision

Use MSAL for Python and implement device-code flow as the first authentication path.

## Consequences

### Positive

- fits terminal and SSH workflows well
- straightforward user experience for CLI apps
- supported by Microsoft identity flows for native/public client scenarios

### Negative

- some tenants may restrict or block device-code flow
- the user has to complete a second-device or browser verification step

## Alternatives considered

### Browser-based interactive auth first

Pros:

- familiar for many users
- can be friendlier on desktop Linux

Cons:

- less suitable for headless sessions
- more moving parts for a first milestone

### Application permissions only

Pros:

- no user login flow at runtime

Cons:

- insufficient for core task write operations
- wrong fit for a personal terminal task client

## Notes

A browser-based fallback can be added later if tenant policy frequently blocks device-code sign-in.
