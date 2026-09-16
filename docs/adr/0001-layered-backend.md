# ADR-0001: Layered backend architecture

- Status: Accepted
- Date: 2026-08-30

## Context

HTTP concerns, validation, business rules, persistence, and cross-cutting operational behaviour need to evolve independently and remain testable.

## Decision

Organise the backend into routes, schemas, services, models, core, middleware, and database modules. Routes translate HTTP to domain calls; services enforce ownership and transactions; models describe persistence.

## Consequences

The separation improves testability and discoverability. Some CRUD paths contain additional mapping code, but business rules do not leak into route handlers or ORM models.
