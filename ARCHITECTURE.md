# Architecture

These rules define responsibilities, not a mandatory technology stack. Apply them
when the relevant components exist. A library or CLI may consist of a small domain
module and an entrypoint; do not create empty layers to satisfy a diagram.
See [profiles](profiles/README.md) for language mappings and the
[documentation guide](docs/000-docs-guide.md) for deriving project architecture.

## Capabilities and dependencies

Organize code by cohesive business capability or responsibility. A capability is
not automatically a process, service deployment, database, or one class. Keep
implementation details inside the owning capability. Cross-capability consumers
use exported contracts rather than reaching into repositories or concrete services.

| Component | Responsibility |
| --- | --- |
| Transport or CLI adapter | Parse input, invoke application contracts, translate outcomes. |
| Application service | Coordinate use cases, authorization, transactions, and ports. |
| Domain model | Enforce business invariants and valid lifecycle operations. |
| Repository | Access storage, map records, and return validated domain values. |
| Schema | Represent transport data separately from domain and persistence shapes. |
| Event and handler | Describe an occurrence and coordinate subsequent capabilities. |
| Composition boundary | Construct resources and inject explicit dependencies. |

A typical execution path is adapter → service → repository → storage. Domain
models do not depend on transport, framework, or database APIs. Adapters do not
bypass use cases by querying repositories. Services consume repository and other
capability contracts; composition supplies concrete implementations. Constructors
must make dependencies explicit rather than hiding resource acquisition.

Publicly accessible business services expose meaningful interfaces or traits that
cover their business operations. Private helpers need no artificial contract.
Keep each service and repository implementation in its own file; language profiles
specify idiomatic file grouping for other types and export placement.

## State and repository contracts

Use state-specific types when an operation must be unavailable in some lifecycle
states. Restrict construction and transitions so callers cannot forge a trusted
state. Use state-dependent behavior dispatch when an operation remains valid in
all states but behaves differently. Profiles describe how to express these rules.

Repositories deserialize into internal persistence representations, validate stored
state and invariants, then return checked domain values. Apply this to reads and
values returned by writes. Never expose an unchecked persistence object as a
trusted business object.

For an identity lookup promising a particular state, distinguish:

- No row within the applicable lookup scope: absence.
- Existing row in another state: state mismatch.
- Malformed or invalid stored data: invalid-data failure.
- Storage failure: structured infrastructure outcome.
- Matching valid row: a checked state-specific value.

Do not hide wrong-state rows with an expected-state filter and interpret the
result as absence. Collection queries may filter by state but must validate each
returned value. Multi-state queries return a sum type or common supertype retaining
validated concrete states. Authorization is separate from state validation.

A validated object represents state at read time. Transactions, conditional writes,
or locks must protect persisted transitions against concurrent changes. Stale
writes produce conflicts, not false success or absence.

## Errors and diagnostics

Translate technical failures into structured outcomes at each boundary:

```text
Infrastructure → repository/port outcome → application outcome → external response
Domain rule violation ──────────────────→ application outcome
```

Domain errors express business rules. Public application contracts must not require
consumers to inspect database-driver or framework errors or parse message text.
Retain technical causes internally; never serialize their chains to clients.
Preserve meaningful distinctions such as absence and state mismatch through layers.
Transport mappings are use-case decisions, not universal status-code rules.

Log operational failures once at the responsible boundary with safe context.
Expected business failures need not be logged as incidents. Redact secrets and
sensitive data from logs, diagnostic strings, and responses.

## Transactions and events

Services define atomic use-case boundaries. Do not imply atomicity across databases
or remote providers. Document transaction ownership and side-effect ordering.
External I/O within a transaction requires an explicit rationale.

Capabilities own their event vocabulary; shared adapters own delivery mechanisms.
Publish committed occurrences after the changes succeed. An outbox record may be
written inside the business transaction and dispatched after commit. Define actual
delivery, retry, ordering, deduplication, and recovery guarantees; an event interface
or framework annotation alone provides none of these guarantees.

## Technology and composition

Select frameworks, storage, authentication, and deployment topology from project
requirements. Record choices in the technology architecture and significant
tradeoffs in [ADRs](docs/decisions/README.md). Prefer standard facilities where
adequate. Configure resources at entrypoints or explicit library initialization
boundaries; keep business behavior testable without live infrastructure.

Keep secrets external. Validate required settings at initialization, document
safe examples, and place authorization near protected use cases. Adopt only
requirements-supported access, lifecycle, retention, and delivery policies.
