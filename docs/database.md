# Database Model

```mermaid
erDiagram
    USERS ||--o{ COMPANIES : owns
    USERS ||--o{ APPLICATIONS : owns
    COMPANIES ||--o{ APPLICATIONS : receives
    APPLICATIONS ||--o{ APPLICATION_EVENTS : records

    USERS {
        uuid id PK
        varchar email UK
        varchar password_hash
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }

    COMPANIES {
        uuid id PK
        uuid user_id FK
        varchar name
        varchar website
        varchar industry
        varchar location
        timestamptz created_at
        timestamptz updated_at
    }

    APPLICATIONS {
        uuid id PK
        uuid user_id FK
        uuid company_id FK
        varchar position
        varchar status
        varchar source
        varchar work_model
        varchar location
        varchar job_url
        numeric salary_min
        numeric salary_max
        varchar currency
        timestamptz applied_at
        text notes
        timestamptz created_at
        timestamptz updated_at
    }

    APPLICATION_EVENTS {
        uuid id PK
        uuid application_id FK
        varchar event_type
        varchar from_status
        varchar to_status
        timestamptz occurred_at
        text notes
        timestamptz created_at
    }
```

## Ownership and deletion

- Companies and applications belong directly to a user.
- Event ownership is inherited through the parent application.
- Deleting a user cascades to owned records.
- Deleting an application cascades to its events.
- A company referenced by an application cannot be deleted.

## Query indexes

Application listing uses compound indexes for the most common access paths:

- `(user_id, created_at)`
- `(user_id, status, created_at)`
- `(user_id, company_id, created_at)`

Pagination has a stable UUID tie-breaker. Free-text search uses escaped `ILIKE` expressions; trigram or full-text indexing can be introduced when measured data volume justifies it.

## Schema lifecycle

Alembic is the only schema-change mechanism. At startup, one container obtains a transaction-scoped advisory lock, upgrades to `head`, verifies the current database heads, grants the runtime role access to current and future objects, and only then starts the API.
