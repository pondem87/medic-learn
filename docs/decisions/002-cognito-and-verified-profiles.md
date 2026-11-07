# ADR 002 — Cognito identity and verified participation

**Date:** 2026-11-06
**Status:** Accepted for identity/profile behavior. CloudFormation provisioning is
superseded by [ADR-003](003-terraform-fargate-deployment.md).

## 1 Context

The user approved Cognito/BFF authentication, professional/student verification,
role switching and attributable activity. This replaces local credential/proof
ownership and the single profile role in ADR-001.

## 2 Decision

Cognito owns registration, credentials, confirmation, recovery and optional TOTP.
Django retains custom web screens and server-side sessions with encrypted provider
tokens. Native mobile uses managed login/code/PKCE; DRF validates scoped access tokens.
Issuer/sub identify an account; email never automatically links identities.

Local account restrictions, staff permissions, one category, verification and role
eligibility remain in PostgreSQL. Pending users have onboarding access only.
Approved students learn; approved professionals learn or train. Biography/contact
fields remain editable and explicitly unverified. Staff verify registries or student
cards and alone populate verified details. School contact is deferred.

Review versions/row locks prevent conflicting decisions. Audit shares local mutation
transactions and rejects update/delete through a PostgreSQL trigger. Private evidence
becomes inaccessible on approval/rejection; durable work retries physical deletion.
External operations serialize bounded provider I/O under account/operation locks.
This is an explicit exception to the normal no-network-in-transaction rule to avoid
stale enable/disable ordering across workers; remote and DB effects are not atomic.

## 3 Consequences

Old sessions/passwords are invalidated; development identities require explicit
operator linking or new registration. Historical migrations and proof tables remain.
Cognito code policies replace five-digit local proofs. General messaging is retained.
Missing Cognito settings fail authentication closed. Terraform deployment is
separate, and AWS operating costs apply. Local blocks are immediate; ordinary mobile
logout cannot immediately revoke an offline-validated access JWT (five-minute expiry).
Out-of-band AWS changes are not a realtime local session revocation feed.

## 4 Related decisions

[ADR-001](001-django-foundation.md) is superseded for identity, role and proofs;
its messaging and narrower Django service boundary remain adopted. See
[operations](../../infrastructure/README.md) and
[requirements](../002-detailed-requirements.md).
