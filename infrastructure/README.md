# Terraform Infrastructure

Infrastructure as Code for the Job Application Tracker project.

This directory contains the Terraform configuration used to provision and manage AWS infrastructure.

## Current Scope

The current Terraform implementation includes:

- Terraform version constraints
- AWS provider configuration
- default resource tags
- reusable input variables
- example Terraform variable values
- infrastructure outputs
- Terraform-specific ignore rules
- VPC networking
- two public subnets
- two private subnets
- Internet Gateway
- Elastic IP for NAT
- NAT Gateway
- public and private route tables
- route table associations across two Availability Zones
- Application Load Balancer security group
- ECS Fargate security group
- RDS PostgreSQL security group
- security group rules enforcing service-to-service access boundaries

## Networking Architecture

The networking layer uses a dedicated VPC across two Availability Zones in `eu-west-1`.

```text
VPC: 10.0.0.0/16

eu-west-1a
|-- Public subnet:  10.0.1.0/24
`-- Private subnet: 10.0.11.0/24

eu-west-1b
|-- Public subnet:  10.0.2.0/24
`-- Private subnet: 10.0.12.0/24
```

Public subnets route internet-bound traffic through an Internet Gateway.

Private subnets route outbound internet traffic through a single NAT Gateway located in the public subnet in `eu-west-1a`.

No inbound internet traffic is routed directly to private subnets.

### NAT Gateway Trade-off

The current design uses a single NAT Gateway as a deliberate portfolio cost optimisation.

A production high-availability architecture would typically provision one NAT Gateway per Availability Zone to reduce cross-AZ dependency and improve resilience.

For this project, infrastructure is intended to be provisioned temporarily for validation and documentation, then destroyed to minimise ongoing AWS costs.

## Security Architecture

The current security model uses dedicated Security Groups for the Application Load Balancer, ECS Fargate tasks, and the PostgreSQL RDS database.

```text
Internet
   |
   | TCP 80
   v
ALB Security Group
   |
   | TCP 8000
   v
ECS Security Group
   |
   | TCP 5432
   v
RDS Security Group
```

### Application Load Balancer

The ALB Security Group allows inbound HTTP traffic from the internet on port `80`.

It does not provide direct access to ECS or RDS resources.

### ECS Fargate

The ECS Security Group allows inbound application traffic on port `8000` only from the ALB Security Group.

This means ECS tasks are not directly exposed to the public internet.

### Amazon RDS

The RDS Security Group allows inbound PostgreSQL traffic on port `5432` only from the ECS Security Group.

The database does not accept inbound connections directly from the internet or from the ALB.

### Security Boundary

The intended communication path is:

```text
Internet -> ALB :80
ALB -> ECS :8000
ECS -> RDS :5432
```

The following direct access paths are intentionally not allowed:

```text
Internet -X-> ECS
Internet -X-> RDS
ALB      -X-> RDS
```

This design follows the principle of least privilege by limiting each service to only the network access it requires.

## Planned Infrastructure

The next infrastructure phases will introduce:

- Amazon ECR
- Amazon ECS Fargate
- Application Load Balancer
- Amazon RDS for PostgreSQL
- AWS Secrets Manager
- CloudWatch logging and alarms

## Requirements

- Terraform >= 1.16.0
- AWS CLI
- authenticated AWS credentials
- AWS region: `eu-west-1`

## Initialisation

From the `infrastructure` directory:

```bash
terraform init
```

Validate formatting and configuration:

```bash
terraform fmt
terraform validate
```

Preview infrastructure changes:

```bash
terraform plan
```

## Configuration

Copy the example variables file:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Then update local values as required.

The local `terraform.tfvars` file is intentionally ignored by Git.

## Outputs

The Terraform configuration exposes key infrastructure identifiers, including:

- VPC ID
- public subnet IDs
- private subnet IDs
- Internet Gateway ID
- NAT Gateway ID
- public route table ID
- private route table ID
- ALB Security Group ID
- ECS Security Group ID
- RDS Security Group ID

These outputs will be reused by later infrastructure components such as ECS, ALB, and RDS.

## State Management

Terraform state is currently local during the foundation, networking, and security phases.

Remote state and state locking will be introduced before persistent production infrastructure is managed.

## Security

Do not commit:

- Terraform state files
- local `.tfvars` files
- AWS credentials
- secrets
- generated Terraform working directories

Sensitive production values will be managed through appropriate AWS services rather than committed to source control.

Infrastructure access is intentionally restricted through Security Group references instead of broad CIDR-based access wherever possible.

## Portfolio Deployment Strategy

The AWS environment is intended for temporary validation rather than permanent public hosting.

Typical workflow:

```text
terraform plan
  |
  v
terraform apply
  |
  v
validate infrastructure
  |
  +-- test networking
  +-- validate security rules
  +-- validate services
  +-- capture screenshots
  +-- collect logs and metrics
  +-- document architecture
  |
  v
terraform destroy
```

This approach demonstrates real AWS provisioning, networking, security, and operational skills while avoiding unnecessary long-running cloud costs.
