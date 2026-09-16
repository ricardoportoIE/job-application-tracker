# ADR-0002: JWT bearer authentication

- Status: Accepted
- Date: 2026-08-31

## Context

The API must support a separately deployed browser client without server-side session storage.

## Decision

Issue short-lived HS256 JWT access tokens after email/password authentication. Require `sub`, `iat`, and `exp`, restrict the accepted algorithm, hash passwords with Argon2, and resolve the user on every authenticated request.

## Consequences

The API remains stateless and simple to scale. Tokens cannot currently be revoked individually; logout removes the browser session token. Refresh tokens, rotation, and revocation remain future work if persistent sessions are required.
