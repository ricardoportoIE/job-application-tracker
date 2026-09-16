# Job Application Tracker

A production-oriented job search workspace built with FastAPI, PostgreSQL, React, Docker, Terraform, AWS ECS, and Prometheus.

The project combines a functional browser MVP with a user-isolated API, automatic schema management, structured observability, hardened containers, and an HTTPS-only AWS architecture.

## Current capabilities

### Product

- Registration and login
- Pipeline summary by hiring stage
- Search and status filtering
- Company management
- Application creation, editing, and deletion
- Application timeline with notes, interviews, and offers
- Responsive desktop and mobile interface
- Loading, empty, error, and success states

### Backend

- Versioned FastAPI API under `/api/v1`
- PostgreSQL persistence with SQLAlchemy and Alembic
- JWT authentication and Argon2 password hashing
- User-scoped companies, applications, and events
- Database-level filtering, sorting, and pagination
- Stable JSON error contracts with request IDs
- Structured logging, health checks, and Prometheus metrics

### Delivery and infrastructure

- Non-root, read-only backend container
- Automatic serialized migrations before API startup
- Schema-aware readiness checks
- HTTPS-only public entry point with ACM and Route 53
- ECS Fargate in private subnets
- Private RDS PostgreSQL
- Separate administrative and runtime database roles
- Secrets Manager for JWT, metrics, and database credentials
- CI gates for backend, frontend, Terraform, and Docker

## Architecture

```text
Browser
  |
  | HTTPS + JWT + X-Request-ID
  v
Application Load Balancer
  |
  | private VPC traffic
  v
FastAPI on ECS Fargate
  |
  | limited application role
  v
PostgreSQL RDS
```

Detailed documentation:

- [System architecture](docs/architecture.md)
- [Database model](docs/database.md)
- [AWS deployment](docs/deployment.md)
- [Architecture Decision Records](docs/adr/README.md)
- [Terraform reference](infrastructure/README.md)

## Repository structure

```text
.
|-- .github/workflows/     CI quality gates
|-- backend/               FastAPI service, migrations, and tests
|-- frontend/              React and TypeScript browser application
|-- infrastructure/        AWS Terraform configuration
|-- docs/                  Architecture, database, deployment, and ADRs
|-- compose.yaml            Local PostgreSQL and backend stack
`-- .env.example            Backend environment template
```

## Run locally

### Complete container stack

Copy the backend environment template:

```bash
cp .env.example .env
```

Start PostgreSQL, the backend, and the Nginx-served frontend:

```bash
docker compose up --build
```

The backend waits for PostgreSQL, acquires a migration lock, applies every Alembic migration, verifies the schema, and then starts Uvicorn. The frontend waits for the backend healthcheck and proxies browser API calls over the private Compose network.

Available endpoints:

```text
Frontend:   http://localhost:5173
API:        http://localhost:8000/api/v1
Swagger:    http://localhost:8000/docs
Readiness:  http://localhost:8000/ready
Metrics:    http://localhost:8000/metrics
```

Stop the complete stack without deleting database data:

```bash
docker compose down
```

### Frontend development mode

```bash
cd frontend
cp .env.example .env
npm ci
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` requests to the containerized backend on port `8000`.

The browser stores the access token in `sessionStorage`, so signing out or closing the tab removes the local session.

## Backend development

Requirements: Python 3.14, uv, and PostgreSQL 17.

```bash
cd backend
uv sync --locked
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Quality checks:

```bash
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m mypy app
uv run python -m pytest
```

Tests require a dedicated `jobtracker_test` database. Safety checks reject the development database as a test target.

## Frontend development

```bash
cd frontend
npm ci
npm run lint
npm run build
```

Set `VITE_API_BASE_URL` to the versioned API base URL. The local default is `http://localhost:8000/api/v1`.

## Security model

### Authentication

- Passwords are hashed with Argon2.
- JWTs require `sub`, `iat`, and `exp` claims.
- Production enforces a minimum 32-character signing secret.
- Resource access always includes the authenticated user's ID.

### Transport and network

- Public AWS traffic enters through HTTPS 443.
- HTTP 80 only redirects to HTTPS.
- ECS and RDS have no direct public ingress.
- Security groups enforce `Internet -> ALB -> ECS -> RDS`.

### Database privileges

Container startup temporarily uses the RDS-managed credential to create or rotate `jobtracker_app`, migrate, and grant the required DML privileges. Administrative variables are removed before Uvicorn starts; the running API uses only the application role.

### Metrics

Production `/metrics` requests require a dedicated bearer token. Unknown routes are labeled `__unmatched__`, preventing arbitrary URLs from creating unbounded Prometheus time series.

## Observability

Every request receives an `X-Request-ID`. The header is accepted and exposed through CORS so the frontend can correlate a visible error with backend logs.

Application metrics include:

```text
http_requests_total
http_request_duration_seconds
database_health_failures_total
```

Logs are JSON and include service, environment, request ID, route template, status, and duration where applicable.

## AWS deployment

Terraform provisions:

- VPC with public and private subnets across two Availability Zones
- Internet and NAT gateways
- ALB, HTTPS listener, ACM certificate, and Route 53 records
- ECS cluster, task definition, and service
- ECR with immutable tags and image scanning
- Private encrypted RDS PostgreSQL
- Secrets Manager values and least-privilege execution permissions
- CloudWatch log group

Copy the example variables:

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

Provide secrets without writing them to disk:

```bash
export TF_VAR_jwt_secret_value="..."
export TF_VAR_db_app_password="..."
export TF_VAR_metrics_bearer_token="..."
```

Then validate and plan:

```bash
terraform init
terraform fmt -check -recursive
terraform validate
terraform plan
```

See [deployment documentation](docs/deployment.md) for required DNS inputs and operational trade-offs.

## Continuous integration

Pull requests and `main` are checked by:

- **Backend CI:** migrations, Alembic consistency, Ruff, formatting, MyPy, and the complete pytest suite
- **Frontend CI:** locked install, ESLint, and production build
- **Terraform CI:** formatting, provider initialization, and validation
- **Docker CI:** production image build, Compose validation, automatic-migration startup, and readiness smoke test

## Known trade-offs

- The portfolio AWS environment uses one ECS task, one NAT Gateway, and Single-AZ RDS to control cost; it is not highly available.
- JWT access tokens do not yet support refresh or individual revocation.
- Application search uses escaped `ILIKE`; full-text or trigram indexing should follow measured need.
- Company and event listing are not yet paginated.
- The frontend is an MVP and does not yet include automated browser tests or offline support.
- Remote Terraform state, alarms, autoscaling, and a frontend hosting pipeline remain future work.

## Roadmap

- [x] User-isolated backend domain
- [x] Functional React MVP
- [x] Automatic schema migration and verification
- [x] HTTPS AWS ingress
- [x] Protected, low-cardinality metrics
- [x] Limited runtime database role
- [x] Backend, frontend, Terraform, and Docker CI
- [x] Architecture, database, deployment, and ADR documentation
- [ ] Frontend component and end-to-end tests
- [ ] Refresh-token rotation and revocation
- [ ] Remote Terraform state and locking
- [ ] ECS autoscaling and Multi-AZ production profile
- [ ] CloudWatch dashboards and alarms
- [ ] Performance and load-test evidence

## Author

Ricardo Porto — [GitHub](https://github.com/ricardoportoIE)
