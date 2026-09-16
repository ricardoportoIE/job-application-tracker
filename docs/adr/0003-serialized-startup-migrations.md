# ADR-0003: Serialized startup migrations

- Status: Accepted
- Date: 2026-09-16

## Context

A fresh Compose or RDS database must be usable without a manual step, while rolling deployments may start more than one task.

## Decision

Run Alembic before Uvicorn in the container entrypoint. Hold a PostgreSQL transaction advisory lock while provisioning the application role, migrating, verifying the expected heads, and granting privileges. Readiness also checks the Alembic head.

## Consequences

Fresh environments become self-initialising and concurrent startups serialize safely. A migration failure prevents the task from becoming healthy. Long or backward-incompatible migrations still require an explicit expand-and-contract deployment strategy.
