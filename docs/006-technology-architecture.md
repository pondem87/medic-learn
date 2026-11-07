# Technology architecture

## 1 Selected stack

Python 3.12 and uv manage Django 5.2, DRF, boto3, PyJWT/cryptography, Psycopg, Pika, and HTTPX.
PostgreSQL supplies transactional persistence; RabbitMQ supplies durable topic routing.
Cognito supplies identity and account emails; private S3 stores deployed evidence.
SMTP/Mailpit provides local application email testing. See [setup](../README.md#setup).

## 2 Deployment and configuration

Django and workers run on the host; Docker Compose services bind to loopback.
Production settings require separate secrets and explicit hosts, HTTPS and secure cookies.
Terraform provisions Fargate/ALB, RDS/MQ, private S3 and CloudFront static hosting. Meta credentials are external.
The [staging environment](../infrastructure/staging/README.md) has a separate
two-AZ VPC, Fargate PostgreSQL/RabbitMQ with EFS persistence, and a test Cognito pool.
MediaMTX is deferred, with its future Compose location documented under `docker/`.

## 3 Verification and operations

Ruff, mypy, Django checks, pytest/PostgreSQL, broker integration, OpenAPI validation,
and static collection run locally and in CI. Message acceptance does not prove delivery.
Inspect dead letters manually; preserve IDs for replay. Never automatically resend uncertain sends.

## 4 Open decisions

Availability, scaling, retention, and disaster recovery remain
[OPEN-001-1](001-general-description.md#open-001-1).

## 5 Identity deployment

See [Cognito configuration](../infrastructure/README.md). Terraform is linted
in CI; live AWS smoke testing requires separately configured resources.
