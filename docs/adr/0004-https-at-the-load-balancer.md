# ADR-0004: HTTPS at the application load balancer

- Status: Accepted
- Date: 2026-09-16

## Context

Credentials and bearer tokens must never cross the public internet over plaintext HTTP.

## Decision

Use an ACM certificate validated through Route 53 on the ALB HTTPS listener. Keep port 80 only to issue an HTTP 301 redirect to HTTPS. Communication from the ALB to ECS stays inside the VPC.

## Consequences

A managed domain and Route 53 hosted zone are required. Certificate renewal is handled by ACM. End-to-end TLS inside the VPC is not currently implemented.
