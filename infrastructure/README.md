# Terraform Infrastructure

Infrastructure as Code for the Job Application Tracker project.

This directory contains the Terraform configuration used to provision and manage AWS infrastructure.

## Current Scope

The current foundation includes:

- Terraform version constraints
- AWS provider configuration
- default resource tags
- environment variables
- example Terraform variable values
- basic outputs
- Terraform-specific ignore rules

No AWS resources are created yet.

## Planned Infrastructure

The next infrastructure phases will introduce:

- VPC
- public and private subnets
- security groups
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
