# Language profiles

The root guides own shared rules. Profiles map those rules to language constructs;
they do not silently override architectural constraints. Record material departures
in a project ADR with rationale and scope. Select active profiles and their source
directories in the project README. The active project profile is Python.

- [Python](python.md): uv, Django, PostgreSQL, Ruff, mypy, and pytest.
- [Java](java.md): Java 21 baseline, Maven, and optional Spring wiring.
- [Rust](rust.md): edition 2024, traits, typestate, and Cargo checks.
- [New language template](language-template.md): complete before adoption.

Retain this directory when copying the scaffold so all guide links remain valid.
There is no universal physical folder tree: a contract in Java `app/` and Rust
`traits.rs` has the same architectural responsibility.
