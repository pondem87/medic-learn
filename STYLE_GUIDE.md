# Style guide

Use this guide with [architecture](ARCHITECTURE.md) and the selected
[language profile](profiles/README.md). Shared rules describe intent; profiles
supply idiomatic syntax, naming, formatting, and test placement.

## Code organization

Group code by capability before technical layer. Keep responsibilities cohesive,
visibility narrow, dependencies explicit, and public contracts meaningful. Separate
transport schemas, domain values, and persistence representations. Prefer immutable
values and controlled state transitions. Use descriptive names from project domain
language; avoid generic utility modules that obscure ownership.

Document public contracts, preconditions, state restrictions, side effects, and
failure outcomes. Explain non-obvious invariants rather than repeating names.
Label illustrative examples and keep executable examples valid for the project.

## Error handling

Use structured error categories and fields. Translate at component boundaries,
retain internal diagnostic causes, and do not catch and silently ignore failures.
Do not use assertions or panics for expected input or infrastructure failures.
Avoid duplicate logging and redact sensitive data. See
[error boundaries](ARCHITECTURE.md#errors-and-diagnostics).

## Testing conventions

Test observable behavior and meaningful boundaries: successful operations, invalid
input, lifecycle restrictions, absence versus state mismatch, error translation,
and concurrent transitions when relevant. Include positive companion cases when
checking that a type system rejects prohibited operations.

Keep unit tests deterministic and independent of live services. Inject time and
external dependencies when needed. Persistence integration tests use isolated,
migrated test databases. Language profiles specify test placement and commands.
Never weaken assertions or suppress diagnostics merely to pass a check.

## Markdown source readability

Write Markdown for source editing and rendering. Requirements, business architecture,
and use cases use labeled records and numbered flows, including templates and
indexes; do not use Markdown or HTML tables in those documents. Elsewhere reserve
tables for compact comparisons or technical lookup data.

Preserve numbered headings, stable IDs, explicit anchors, and linked references.
Place anchors on their own lines before records. Keep field order consistent and
wrap prose at roughly 80–100 characters without breaking links or identifiers.
Avoid unrelated reflow. Follow the [documentation guide](docs/000-docs-guide.md)
and [documentation agent instructions](docs/AGENTS.md).
