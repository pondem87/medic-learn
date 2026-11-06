# Java profile

Apply [shared architecture](../ARCHITECTURE.md) and [style](../STYLE_GUIDE.md).
Use Java 21 as the source baseline and Maven as the default build tool. Pin the
chosen JDK, Maven wrapper, plugins, and dependencies when initializing; this profile
does not bundle a POM or promise compatibility with unselected framework versions.
Spring is optional for services, not a requirement for libraries or CLIs.

## Structure and contracts

Use Maven `src/main/java`, `src/main/resources`, and `src/test/java` conventions.
Choose a project-owned reverse-domain package; organize capabilities beneath it.
The following optional folders express responsibilities, not mandatory empty layers:

```text
<package>/<capability>/
    <Capability>Configuration.java   # only when using Spring
    app/                            # exported interfaces and consumer-facing errors
    services/                       # internal contracts and implementations
    repositories/                   # internal persistence contracts and adapters
    models/                         # domain values and persistence representations
    schemas/                        # transport data
    controllers/                    # HTTP adapters, if needed
    events/                         # capability-owned occurrences
```

Keep each top-level type in its own file. Keep internal interfaces with their owning
responsibility. Group populated model packages by concept; keep sealed families
together and data-only JPA entities beside related models. Only repositories access
entities; neither transport nor application contracts expose them.

Use constructor injection. With Spring, put explicit `@Configuration`/`@Bean`
wiring at capability roots. Implementations are ordinary classes without
`@Service`/`@Repository` scanning. Limit component discovery to configurations;
register controllers/advice explicitly while retaining MVC handler annotations.
Without Spring, compose ordinary objects at the entrypoint.

## Types, state, and errors

Use UpperCamelCase types, lowerCamelCase members, and UPPER_SNAKE_CASE true constants.
Prefer final fields, immutable values, explicit constructors, and suitable records.
Do not hide invariants behind generated methods.

Use distinct state-specific domain types with restricted construction when operation
availability depends on state. A common supertype supports multi-state queries;
keep checked concrete types. Use the State pattern when only behavior varies.
Java references are not consumed by transitions: enforce stale-write protection
in persistence even when the domain API restricts method availability.

Translate technical exceptions into structured consumer outcomes, preserving causes
internally. Document public contracts and non-obvious invariants with JavaDoc.

## Formatting and validation

Use four spaces, a 120-column wrapping target, annotations on separate lines,
expanded bodies, and useful blank lines between declarations and logical steps.
Configure Spotless with a committed Eclipse formatter profile and bind its check
to Maven validation when creating the build. No formatter configuration is supplied
by this documentation-only scaffold.

After Maven, wrapper, formatter, and tests are configured, run:

```sh
./mvnw spotless:check
./mvnw clean verify
./mvnw javadoc:javadoc
```

Use `./mvnw spotless:apply` when intentionally formatting code. CI uses the same
pinned JDK and wrapper. Use JUnit for meaningful behavior and boundary tests;
unit tests require no live services. Configure isolated persistence integration
tests when needed. Verify state-specific API restrictions and repository state
validation, including matching, missing, malformed, and wrong-state rows.
