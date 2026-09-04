# Job Application Tracker

Production-oriented job application tracking platform built with FastAPI, PostgreSQL, React, Docker, GitHub Actions, and Prometheus.

> Portfolio project focused on backend engineering, security, observability, testing, CI/CD, and cloud-ready architecture.

## Project Highlights

- Production-oriented FastAPI backend with PostgreSQL persistence
- JWT authentication with Argon2 password hashing
- User-scoped companies, applications, and application events
- Search, filtering, sorting, and pagination
- Structured JSON logging and request correlation IDs
- Prometheus metrics with low-cardinality route labels
- Liveness, readiness, and database health endpoints
- Hardened Docker runtime with non-root execution and reduced privileges
- Protected `main` branch with required GitHub Actions quality gate
- 337 automated tests passing in CI

## Status

Active development.

The backend is substantially implemented and production-oriented.

Current work is focused on:

- AWS deployment
- Terraform infrastructure
- cloud monitoring and alerting
- performance testing
- architecture documentation
- frontend feature development

## Purpose

Job searching often requires tracking vacancies, companies, recruiters, interviews, deadlines, notes, and status changes across several tools.

Job Application Tracker centralises that information into a single system and provides a structured view of the user's hiring pipeline.

The project is also designed as a portfolio-grade system that demonstrates practical software engineering concerns beyond CRUD development.

## Core Features

### Authentication and User Isolation

- User registration and login
- JWT-based authentication
- Argon2 password hashing
- Authenticated `/me` endpoint
- User-specific resource ownership
- Generic invalid-credential responses
- Inactive-user handling

### Company Management

- Create, retrieve, update, list, and delete companies
- Ownership enforcement for all company operations

### Job Application Management

- Create, retrieve, update, and delete job applications
- Filter by status, company, source, and work model
- Search
- Sorting
- Pagination
- Stable result ordering
- Salary and currency validation

### Application Timeline

- Application event history
- Automatic application-created events
- Automatic status-change events
- Manual notes and timeline events
- Interview and offer-related event types
- Chronological ordering
- Ownership enforcement through parent applications

## Architecture

The backend follows a layered structure:

```text
backend/
|-- app/
|   |-- api/
|   |   |-- routes/
|   |   |-- dependencies.py
|   |   |-- exception_handlers.py
|   |   |-- openapi.py
|   |   `-- router.py
|   |-- core/
|   |   |-- config.py
|   |   |-- logging.py
|   |   |-- metrics.py
|   |   |-- request_context.py
|   |   `-- security.py
|   |-- db/
|   |-- middleware/
|   |-- models/
|   |-- schemas/
|   |-- services/
|   `-- main.py
|-- migrations/
|-- tests/
|-- Dockerfile
|-- alembic.ini
|-- pyproject.toml
`-- uv.lock
```

Responsibilities are separated between:

- **routes** - HTTP and API concerns
- **schemas** - request and response validation
- **services** - business logic
- **models** - persistence and domain entities
- **core** - configuration, security, logging, and metrics
- **middleware** - cross-cutting request behaviour
- **db** - database engine and sessions

## Domain Model

```text
User
|-- Companies
`-- Applications
    `-- Application Events
```

Persisted models:

- User
- Company
- Application
- ApplicationEvent

Database schema evolution is managed with Alembic migrations.

## Technology Stack

### Backend

- Python 3.14
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- PostgreSQL 17
- psycopg
- Alembic

### Security

- PyJWT
- pwdlib
- Argon2
- HTTP Bearer authentication
- CORS hardening
- security response headers

### Observability

- Structured JSON logging
- Request correlation IDs
- Prometheus client
- HTTP request counters
- Request latency histograms
- Database health-failure counters

### Engineering Tooling

- uv
- Ruff
- MyPy
- pytest
- pytest-cov
- Git

### Containerisation

- Docker
- Docker Compose
- Multi-stage builds
- Non-root runtime
- Read-only root filesystem
- Dropped Linux capabilities
- `no-new-privileges`
- Health checks

### CI/CD

- GitHub Actions
- Protected `main` branch
- Required `Backend Quality Gate`

### Frontend

- React
- TypeScript
- Vite

### Cloud / Infrastructure

Planned:

- AWS
- Terraform
- cloud monitoring
- alerting

## API Overview

The API is versioned under:

```text
/api/v1
```

Main resource groups:

```text
/api/v1/auth
/api/v1/companies
/api/v1/applications
/api/v1/applications/{application_id}/events
```

Operational endpoints:

```text
/health
/live
/ready
/health/db
/metrics
```

Development documentation:

```text
/docs
/redoc
/openapi.json
```

API documentation exposure can be disabled through configuration.

## Security

Implemented controls include:

- Argon2 password hashing
- JWT access tokens
- required JWT claims
- restricted JWT algorithm configuration
- configurable token expiration
- production JWT secret-length validation
- generic invalid-credential responses
- authenticated ownership checks
- inactive-user enforcement
- explicit CORS configuration
- production CORS validation
- configurable API documentation exposure
- request ID validation and propagation
- environment-based secret configuration

Security headers include:

```text
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
```

Production secrets are not stored in source control.

## Observability

### Structured Logging

Application logs are emitted as JSON and can include:

```text
timestamp
level
logger
message
service
environment
request_id
event
http_method
http_path
status_code
duration_ms
```

Structured application events include:

```text
application.configured
http.request.completed
auth.login.succeeded
auth.login.failed
auth.login.inactive
database.readiness.failed
database.health.failed
```

### Request Correlation

Each HTTP request receives an `X-Request-ID`.

A valid client-provided request ID is propagated. Invalid or missing IDs are replaced with generated UUIDs.

The request ID is included in:

- structured logs
- API error responses
- response headers

### Prometheus Metrics

The API exposes:

```text
/metrics
```

Current application metrics include:

```text
http_requests_total
http_request_duration_seconds
database_health_failures_total
```

Dynamic identifiers are normalised to route templates to avoid high-cardinality metric labels.

Example:

```text
/api/v1/applications/{application_id}
```

instead of:

```text
/api/v1/applications/123
```

## Health and Readiness

### Liveness

```text
GET /live
```

Confirms that the application process is alive.

### Readiness

```text
GET /ready
```

Verifies that the application can connect to PostgreSQL.

Returns HTTP `503` when the database is unavailable.

### Database Health

```text
GET /health/db
```

Provides an explicit database health check.

These endpoints are suitable for container orchestration and future cloud load-balancer health checks.

## Database and Migrations

PostgreSQL is the primary database.

Current migration chain:

```text
users
-> companies
-> applications
-> application_events
-> application query indexes
```

CI verifies that:

- migrations can run from an empty database
- application models match the current migration head
- the dedicated test database can be independently migrated

## Query Performance

Application listing is supported by database indexes for common access patterns:

```text
user_id + created_at
user_id + status + created_at
user_id + company_id + created_at
```

Search, filtering, sorting, and pagination are executed at the database query level.

## Testing

The backend currently has:

```text
337 automated tests passing in CI
```

The test suite covers:

- routes
- services
- schemas
- authentication
- JWT handling
- OpenAPI contracts
- database isolation
- database sessions
- CORS
- security headers
- configuration validation
- error handlers
- health and readiness
- structured logging
- request correlation
- Prometheus metrics

A dedicated PostgreSQL test database is used:

```text
jobtracker_test
```

Safety checks prevent the test suite from accidentally running against the development database.

## Continuous Integration

The backend workflow runs on:

- pushes to `main`
- pull requests targeting `main`
- manual workflow dispatches

The `Backend Quality Gate` performs:

```text
1. Checkout
2. Python setup
3. uv installation
4. Locked dependency installation
5. PostgreSQL service startup
6. Dedicated test database creation
7. Main database migrations
8. Alembic model consistency check
9. Test database migrations
10. Ruff linting
11. Ruff formatting check
12. MyPy type checking
13. Full pytest suite
```

The `main` branch is protected and requires the `Backend Quality Gate` before changes are integrated.

## Docker

The backend uses a multi-stage Docker build.

The runtime container:

- runs as a non-root user
- uses a slim Python base image
- installs only runtime dependencies
- uses a read-only root filesystem
- drops Linux capabilities
- enables `no-new-privileges`
- uses tmpfs for temporary writable storage
- exposes an application health check

Docker Compose currently runs:

```text
PostgreSQL
Backend API
```

## Running Locally

### Requirements

- Docker
- Docker Compose

Clone the repository:

```bash
git clone https://github.com/ricardoportoIE/job-application-tracker.git
cd job-application-tracker
```

Start the stack:

```bash
docker compose up --build
```

Services:

```text
Backend API: http://localhost:8000
PostgreSQL:  localhost:5432
```

When documentation is enabled:

```text
Swagger UI: http://localhost:8000/docs
ReDoc:      http://localhost:8000/redoc
Metrics:    http://localhost:8000/metrics
Liveness:   http://localhost:8000/live
Readiness:  http://localhost:8000/ready
```

Stop the stack:

```bash
docker compose down
```

Remove the development PostgreSQL volume:

```bash
docker compose down -v
```

## Running the Backend Without Docker

From the `backend` directory:

```bash
uv sync
```

Run migrations:

```bash
uv run alembic upgrade head
```

Start the API:

```bash
uv run uvicorn app.main:app --reload
```

Run the quality checks:

```bash
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m mypy app
uv run python -m pytest
```

## Repository Structure

```text
.
|-- .github/
|   `-- workflows/
|-- backend/
|-- frontend/
|-- infrastructure/
|-- docs/
|-- .env.example
|-- .gitignore
|-- compose.yaml
`-- README.md
```

## Development Workflow

```text
main
  |
  v
feature branch
  |
  v
implementation
  |
  v
local quality checks
  |
  v
commit
  |
  v
push
  |
  v
pull request
  |
  v
Backend Quality Gate
  |
  v
merge
```

Recent engineering work has been delivered through separate pull requests for:

- backend container hardening
- liveness and readiness
- API security hardening
- observability and metrics

## Roadmap

### Completed

- [x] Backend project structure
- [x] PostgreSQL persistence
- [x] Alembic migrations
- [x] User authentication
- [x] JWT security
- [x] Company management
- [x] Application management
- [x] Application timeline and events
- [x] Search, filtering, sorting, and pagination
- [x] User data isolation
- [x] API error contracts
- [x] OpenAPI documentation
- [x] Health and readiness checks
- [x] Structured logging
- [x] Request correlation
- [x] Prometheus metrics
- [x] Security hardening
- [x] Production-oriented Docker container
- [x] Backend CI quality gate
- [x] Protected `main` branch

### Planned

- [ ] Frontend application features
- [ ] Terraform infrastructure
- [ ] AWS deployment
- [ ] Cloud monitoring dashboards
- [ ] Alerting
- [ ] Performance and load testing
- [ ] Architecture diagram
- [ ] Database diagram
- [ ] Deployment diagram
- [ ] Architecture Decision Records
- [ ] Performance benchmarks
- [ ] Production screenshots
- [ ] Trade-offs and known limitations documentation

## Engineering Focus

This project is intentionally designed to demonstrate:

- backend architecture
- API design
- database modelling
- authentication and authorization
- security hardening
- observability
- test isolation
- type safety
- container hardening
- CI enforcement
- production-oriented engineering practices
- cloud-ready architecture

## Author

**Ricardo Porto**

GitHub: [@ricardoportoIE](https://github.com/ricardoportoIE)
