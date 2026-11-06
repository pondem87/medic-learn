# Python profile

## Tooling and applicability

Python 3.12.14, uv, Django 5.2, DRF and PostgreSQL govern all Python source.
Use `uv sync --locked`; dependencies and development tooling are pinned by `uv.lock`.
Use the commands in the [README](../README.md#verification) locally and in CI.

## Structure and contracts

Group by capability under `medic_learn`; configuration belongs to `config`.
HTTP serializers/forms translate input; services own authorization and transaction boundaries.
Pure domain values use frozen dataclasses. Protocols express provider contracts.
Django models are persistence representations, not trusted domain objects.
Keep provider calls outside database transactions. Service functions are exported operations;
module-local helpers are implementation details. Do not reach into another capability's storage.
Django infrastructure adapters may use ORM models; domain policy must remain framework-independent.

## State and errors

State transitions validate current persisted state while holding database row locks.
Python annotations do not prevent runtime construction: validate inputs and test invalid transitions.
AccountError exposes structured code/message/status without driver or provider exception details.
Keep proof plaintext out of durable events, messages, and logs.
Retain exception causes internally and avoid logging the same operational failure twice.

## Style and validation

Use snake_case, PascalCase classes, explicit imports, and Ruff's 100-column formatting.
Use type annotations for public contracts and document non-obvious transaction/failure semantics.
Tests belong under `tests/`; persistence tests use isolated PostgreSQL databases.
Use injected or mocked channel transports and deterministic inputs to test provider failures.
Concurrency tests must use real database transactions rather than SQLite substitutes.

## Adoption and exceptions

See [ADR-001](../docs/decisions/001-django-foundation.md) for Django adapter boundaries,
Python runtime state enforcement, and the narrower port of the Java messaging services.
