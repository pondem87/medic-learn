# <Language> profile

Template: replace every prompt before selecting this profile. Apply
[shared architecture](../ARCHITECTURE.md) and [style](../STYLE_GUIDE.md).

## Tooling and applicability

- Language/version, project kinds, and rationale: <decision>
- Toolchain pinning, dependency locking, and initialization: <commands and files>
- Optional framework choices: <requirements and explicit selection>

## Structure and contracts

- Capability layout and exported contract location: <directory example>
- Service/repository file separation and idiomatic type grouping: <rules>
- Interfaces, visibility, constructor injection, and composition: <language mapping>
- Transport/domain/persistence separation: <mapping>

## State and errors

- Checked construction and state-specific operation availability: <mechanism>
- State transitions, ownership/aliasing, and multi-state results: <mapping>
- Repository validation and concurrency protection: <mapping>
- Structured outcomes, absence, diagnostic causes, and safe translation: <mapping>

If the language cannot enforce a constraint statically, document the limitation,
explicit runtime enforcement, tests, and a project ADR for any material departure.

## Style and validation

- Naming, formatting, API documentation, and formatter configuration: <rules>
- Test placement and behavior, state restriction, and error scenarios: <rules>
- Exact format/static analysis/build/test/documentation commands: <commands>
- Prerequisites and CI parity: <setup>

## Adoption check

Trace every shared architectural rule to a language mechanism or documented
limitation. Walk through a minimal project and a capability with persistence.
Record material exceptions in an ADR; placeholders are not accepted decisions.
