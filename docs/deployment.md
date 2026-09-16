# AWS Deployment

```mermaid
flowchart TB
    Internet((Internet)) -->|HTTP :80| Redirect[ALB redirect]
    Internet -->|HTTPS :443| HTTPS[ALB HTTPS listener]
    Route53[Route 53 API record] --> HTTPS
    ACM[ACM certificate] --> HTTPS

    subgraph VPC[Application VPC]
        subgraph Public[Public subnets · two AZs]
            Redirect
            HTTPS
            NAT[NAT Gateway]
        end
        subgraph Private[Private subnets · two AZs]
            ECS[ECS Fargate service]
            RDS[(RDS PostgreSQL)]
        end
        HTTPS -->|ALB SG · :8000| ECS
        ECS -->|ECS SG · :5432| RDS
        ECS --> NAT
    end

    ECR[ECR immutable images] --> ECS
    Secrets[Secrets Manager] --> ECS
    ECS --> CloudWatch[CloudWatch Logs]
```

## Container startup

```mermaid
sequenceDiagram
    participant Task as ECS task
    participant DB as PostgreSQL
    participant API as Uvicorn

    Task->>DB: Connect with temporary admin credentials
    Task->>DB: Acquire advisory transaction lock
    Task->>DB: Create/update limited application role
    Task->>DB: Apply Alembic migrations
    Task->>DB: Verify current heads equal expected heads
    Task->>DB: Grant runtime privileges
    Task->>Task: Remove admin credentials from environment
    Task->>API: exec Uvicorn with application credentials
    API->>DB: Readiness checks connectivity and schema head
```

## Required Terraform inputs

Non-secret inputs:

- `api_domain_name`
- `route53_zone_id`
- `frontend_origin` using HTTPS

Ephemeral sensitive inputs:

- `jwt_secret_value`
- `db_app_password`
- `metrics_bearer_token`

Pass sensitive values through `TF_VAR_...` environment variables or a secrets-aware CI system. Do not place them in `.tfvars` files.

Increment `secrets_version` whenever rotating one of the write-only values so Terraform creates the corresponding new secret versions.

## Availability and cost trade-offs

The portfolio environment runs one ECS task, one NAT Gateway, and Single-AZ RDS. It demonstrates the production topology but does not claim high availability. A persistent production environment should use at least two tasks, autoscaling, Multi-AZ RDS, one NAT Gateway per AZ or VPC endpoints, longer backups, deletion protection, alarms, and remote Terraform state with locking.
