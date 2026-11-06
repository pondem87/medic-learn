# Data architecture

## 1 Derivation

[Account information](003-business-architecture.md#info-1) maps to custom User/Profile records.
Email is case-insensitively unique and retained after soft deletion. UUIDs identify accounts.
Profile is one-to-one and protected against orphaning through normal service creation.

## 2 Persistence

PostgreSQL stores users/profiles, proofs and issuance controls, event inbox/outbox,
notifications, messages, normalized provider observations, web sessions and refresh blacklists.
Django migrations define physical constraints. Conditional uniqueness permits only one ready proof.
Database role privileges allow test database creation locally; production roles require separate setup.

## 3 Integrity and lifecycle

Row locks serialize account/proof transitions. Attempt reservations commit before proof consumption.
Verification and account activation commit with their outbox event. Message dispatch claims commit
before provider I/O; uncertain outcomes are retained without automatic resend.
No proof plaintext enters persistent application records. SMTP recipients can see delivered proofs.

## 4 Open decisions

Retention, archival, backup/recovery targets, and hard deletion are
[OPEN-001-1](001-general-description.md#open-001-1); no destructive cleanup is scheduled.
