# Technology architecture

## 1 Selected stack

Python 3.12 and uv manage Django 5.2, DRF, Simple JWT, Psycopg, Pika, and HTTPX.
PostgreSQL supplies transactional persistence; RabbitMQ supplies durable topic routing.
SMTP/Mailpit provides local email testing. See [setup](../README.md#setup).

## 2 Deployment and configuration

Django and workers run on the host; Docker Compose services bind to loopback.
Production settings require separate secrets and explicit hosts, HTTPS and secure cookies.
Production deployment/static hosting is not supplied. Meta credentials are external.
MediaMTX is deferred, with its future Compose location documented under `docker/`.

## 3 Verification and operations

Ruff, mypy, Django checks, pytest/PostgreSQL, broker integration, OpenAPI validation,
and static collection run locally and in CI. Message acceptance does not prove delivery.
Inspect dead letters manually; preserve IDs for replay. Never automatically resend uncertain sends.

## 4 Open decisions

Availability, scaling, retention, and disaster recovery remain
[OPEN-001-1](001-general-description.md#open-001-1).
