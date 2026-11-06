# Rust profile

Apply [shared architecture](../ARCHITECTURE.md) and [style](../STYLE_GUIDE.md).
Initialize a library or binary with Cargo according to the project purpose. Use
edition 2024 by default; pin a compatible toolchain in `rust-toolchain.toml` with
rustfmt and Clippy. Commit the generated lockfile and use it locally and in CI.
No runtime, web framework, database, or async dependency is selected here.

## Structure and contracts

Organize `src/` by capability. For example, when all these responsibilities exist:

```text
src/<capability>/
    mod.rs
    traits.rs
    models.rs
    services/
        mod.rs
        document_editing_service.rs
    repositories/
        mod.rs
        document_repository.rs
```

Keep exports and declarations in `mod.rs`. Each service or repository implementation
has its own file. A single implementation may use `services.rs` or `repositories.rs`;
multiple implementations use directories. Other types may share cohesive files.
Add adapter, schema, and event modules only when required.

Publicly accessible services, including crate-visible cross-capability services,
implement meaningful business traits in `traits.rs`. Keep business operations on
the trait, constructors and private helpers inherent. Choose generics or trait
objects according to the contract; do not assume async traits support dynamic dispatch.
Use narrow visibility and explicit production imports, grouped standard/external/local.
Use snake_case functions/modules, UpperCamelCase types, and SCREAMING_SNAKE_CASE constants.

## State, errors, and documentation

For lifecycle objects use a generic state parameter, private `PhantomData<State>`,
and documented markers. Specialized impl blocks expose state-valid operations.
Transitions consume the old value and return the new typed value; document ownership
on failure. Restrict construction and do not derive Clone automatically when stale
copies undermine lifecycle rules. Multi-state queries return enums of checked types.
Deserialization and markers alone do not validate stored states.

Return structured errors through Result; reserve Option for ordinary absence.
Do not expose driver error types through public service contracts. Avoid panic,
unwrap, or expect for expected runtime failures; tests may use them to fail tests.
Avoid blocking work or synchronous lock guards across await points. Document
background task failures and synchronization ownership.

Use Rustdoc on every struct and trait, including private helpers, markers, and test
fixtures. Document public APIs, relevant Errors/Panics sections, and examples.

## Tests and validation

Every source file with behavior has a colocated `#[cfg(test)] mod tests`; declaration
and re-export-only files are exempt. Extract testable entrypoint behavior as needed.
The first content in each test module is `//!` documentation naming the subject and
containing a `# Test plan` that names each test and its purpose. Keep it synchronized.

Use compile-fail examples or a harness for prohibited state operations and reuse
after consuming transitions, with valid companion cases. Test repository absence,
state mismatch, invalid data, and infrastructure errors, plus boundary translation.
Integration tests use isolated migrated storage when persistence exists.

After Cargo and the pinned toolchain are initialized, run:

```sh
cargo fmt --check
cargo check --locked
cargo clippy --all-targets --locked -- -D warnings
cargo test --locked
cargo doc --no-deps --locked
```

Run additional compile-fail/integration harnesses when introduced. CI must use the
same toolchain and lockfile. Offline mode is appropriate only with cached dependencies.
