# ADR 004 — Persistent container data for staging

**Date:** 2026-11-06
**Status:** Accepted

## 1 Context

Production-like identity and review flows need a deployed test environment. The
user requested a simpler staging VPC with Fargate PostgreSQL and RabbitMQ images,
separate Cognito and staging domains. Test data and broker messages must survive
task replacement while keeping staging cost below managed data services.

## 2 Decision

Staging has its own Terraform state key and AWS resources. A two-AZ public/private
VPC has one NAT, a public ALB and private Fargate tasks. Single-instance PostgreSQL
and RabbitMQ services use separate EFS access points with IAM and transit
encryption. ECS stops each old data task before its replacement starts. Application
protocol traffic stays private and uses plaintext PostgreSQL/AMQP; the existing
deployment retains verified database TLS and RabbitMQ TLS. Daily logical PostgreSQL
backups go to a private S3 bucket with seven-day expiration.

Staging uses the same application image and settings, with an explicit database
SSL-mode override. It has a separate Cognito test pool, ECR repositories, Secrets
Manager secrets, static/media buckets, certificates and DNS records. Web and worker
services remain disabled until the image is published and migrations succeed.

## 3 Consequences

EFS preserves data during Fargate task replacement, but its latency and filesystem
semantics differ from RDS storage. A single broker and stop-before-start rollout
cause downtime and do not validate production failover. RabbitMQ messages have no
independent recovery backup. A logical PostgreSQL dump is required because a live
EFS snapshot alone is not an application-consistent database backup. Staging test
results establish application behavior, not managed-service availability or TLS.

## 4 Related decisions

[ADR-003](003-terraform-fargate-deployment.md) defines the managed deployment.
See the [staging runbook](../../infrastructure/staging/README.md).
