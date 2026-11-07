# ADR 003 — Terraform deployment on AWS Fargate

**Date:** 2026-11-06
**Status:** Accepted

## 1 Context

The user selected Terraform, Cape Town, Fargate, RDS, Amazon MQ and the existing
Route 53 zone, with development-cost defaults. Application hosts are
api.mededbotswana.co.bw and www.mededbotswana.co.bw; Cognito managed login uses
oidc.api.mededbotswana.co.bw. Static assets and private media require S3 storage.

## 2 Decision

Terraform replaces the unprovisioned CloudFormation template from ADR-002.
Public subnets contain ALB and NAT; private application subnets contain Fargate
web/worker/one-off migration tasks; isolated data subnets contain PostgreSQL RDS
and RabbitMQ Amazon MQ. Security groups permit ALB-to-web and task-to-database/
broker traffic only. HTTPS egress through NAT supports AWS APIs and external providers.

The development default has one NAT, one web task, one worker, Single-AZ RDS and
single-instance MQ. Three AZs are allocated so an explicit HA configuration can
use AZ-local NAT, two web tasks, Multi-AZ RDS and a three-node broker. The worker
stays singleton with non-overlapping deployments because publication is not designed
for concurrent publishers. MQ uses TLS and quorum queues. Runtime database access
uses an application role, not the RDS administrator; the one-off bootstrap task alone
receives administrator credentials and grants schema privileges for migrations.

Cognito remains in Cape Town. Its CloudFront-backed domain certificate is issued
in us-east-1, with DNS validation in the existing hosted zone. The parent api host
must resolve before Cognito custom-domain creation. Existing DNS records must be
imported and reviewed rather than silently overwritten.

Static files use a private versioned S3 bucket with CloudFront origin access control;
only static objects are publicly readable through CloudFront. Media uses a separate
private unversioned bucket. Student evidence deletion must not leave retained object
versions. Other media stays private; Django storage uses short-lived signed URLs
that application authorization must control. No public media-serving route is added.

## 3 Consequences

Terraform state includes generated secrets and requires a private encrypted versioned
S3 backend with locking and restricted IAM. Application secrets are injected by ECS
from Secrets Manager, not built into the image. Provisioning, image publication,
migration and enabling services are distinct steps. No deployment occurs in tests.
The web container uses Gunicorn and trusts ALB forwarded HTTPS only because port 8000
is reachable solely from ALB. Static manifests are built into the same image deployed.

Single-AZ services and one NAT are deliberate development availability compromises.
Managed MQ, NAT, ALB and RDS incur standing costs even when ECS desired counts are zero.
SES sender verification and sandbox exit remain deployment prerequisites for real
application email; an existing identity can be supplied. Container builds require
access to package repositories and the AWS RDS certificate bundle endpoint.

## 4 Related decisions

[ADR-002](002-cognito-and-verified-profiles.md) remains adopted except for its
CloudFormation provisioning choice. See [deployment instructions](../../infrastructure/README.md).
