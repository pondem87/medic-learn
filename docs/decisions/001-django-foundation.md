# ADR 001 — Django authentication and messaging foundation

**Date:** 2026-11-03
**Status:** Accepted

## 1 Context

The approved plan selects Python/uv, server-rendered Django, mobile REST/JWT,
PostgreSQL, RabbitMQ, and SMTP/Mailpit, following the software project blueprint.
The Java IoT reference supplies architectural guidance, not a cross-language runtime dependency.

## 2 Decision

Use capability modules, shared application operations, explicit database transactions, and pure
account-transition values. Django ORM models remain inside framework adapters/application
composition; they are not declared to be immutable trusted domain objects. Python runtime checks
and PostgreSQL constraints enforce state restrictions rather than Java sealed-class typestate.
The initial Django services coordinate ORM operations directly. This is a deliberate narrower
adapter implementation than the blueprint's repository-interface-per-service architecture;
extract repository ports as additional domain behavior needs independent storage implementations.

Borrow the Java ADR-008/012/013/015/018 patterns: keyed, single-use proofs; separate issuance
controls; transient confidential delivery; durable events; idempotent notification capture;
message claim before provider I/O; uncertain sends require operator resolution.
Do not import organisation tenancy, Java permissions, media, or legacy compatibility logic.
Generation limits are scoped per account/email-verification purpose, not shared globally.

Email is the primary identity. Staff profile role controls business review; Django is_staff
controls admin access separately. Account deletion is terminal soft deletion retaining identity.
Profile validation is independent of role and account eligibility.

SMTP is new Python code because the reference has no email-channel implementation.
WhatsApp uses configured Meta templates and signature-verified observations, disabled by default.
Notifications/messages share PostgreSQL, allowing notification handoff and queued-message creation
to commit atomically. RabbitMQ consumers deduplicate UUIDs and reject changed payload meaning.
Webhook acknowledgement follows durable local outbox capture, a deliberate improvement over
requiring immediate broker availability. Publication and provider dispatch are not globally atomic.

## 3 Consequences

Public HTML/API flows share policy. Account credential versions invalidate old credentials
when blocked and remain changed on restoration. Numeric proof attempts survive failed verification.
General notification opt-in does not suppress requested verification messages.
Python domain typestate is runtime-enforced. No exactly-once provider delivery is claimed.
Media binaries, arbitrary inbound-message business actions, and multi-tenant channel routing
remain outside this foundation. Raw inbound observations are stored for future interpretation;
they never authenticate an account or trigger a business action automatically.

## 4 Evidence

See [requirements](../002-detailed-requirements.md), [application architecture](../005-application-architecture.md),
and the PostgreSQL/broker tests under `tests/`.
