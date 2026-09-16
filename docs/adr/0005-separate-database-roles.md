# ADR-0005: Separate database roles

- Status: Accepted
- Date: 2026-09-16

## Context

The API previously ran with the RDS master credential, giving a compromised application unnecessary administrative power.

## Decision

Store a dedicated application credential in Secrets Manager. The startup migration process temporarily receives the RDS administrative credential, creates or rotates the application role, migrates, grants DML access, and removes the administrative variables before replacing itself with Uvicorn.

## Consequences

The long-running API process has no administrative database credential and cannot create roles or alter infrastructure. Startup remains trusted and privileged; a future deployment pipeline may move migrations into a dedicated one-off ECS task for even stronger separation.
