# Data architecture

## 1 Derivation

[Account information](003-business-architecture.md#info-1) maps to custom User/Profile records.
Email is case-insensitively unique and retained after soft deletion. UUIDs identify accounts.
Profile is one-to-one and protected against orphaning through normal service creation.

## 2 Persistence

PostgreSQL stores profiles, councils, private evidence metadata, immutable activity,
retryable operations, rate-limit counters, database sessions and messaging records.
Cognito owns passwords/proofs. Local passwords are unusable. Historical proof and
blacklist tables can remain but are not used for access. Issuer/subject uniquely
identify external users. Session tokens are encrypted with a separate Fernet key.
Student evidence uses private local storage or private S3, never public media URLs.

## 3 Integrity and lifecycle

Row locks and profile versions serialize decisions; audit writes share transactions.
PostgreSQL triggers reject audit update/delete. Verified fields are staff-only;
submitted council/number are claims until approval. Account restrictions and credential
cutoffs reject stale access. Final decisions revoke evidence access immediately and
schedule retryable deletion; interrupted uploads remain cleanup-addressable.

## 4 Open decisions

Evidence deletion after final decisions is defined. Other archival, backup/recovery
and retention policies remain [OPEN-001-1](001-general-description.md#open-001-1).
