# Application architecture

## 1 Components

HTML/REST adapters call account application operations. Cognito owns identity;
its adapter translates errors and verifies tokens. Accounts owns local eligibility,
profiles, review, audit and retryable external operations. Private storage owns
student-card I/O. General events, notifications and messages retain their boundaries.
Historical email-proof tables have no runtime authentication service.

## 2 Flows

1. Web registers through Cognito then binds issuer/sub locally. Confirmation/login
   reconcile interrupted local creation; email conflicts require explicit linking.
2. Web completes password/MFA before creating a Django session; native mobile uses
   managed login/code/PKCE and sends scoped Cognito access tokens to DRF.
3. Users submit registry details or student evidence. Staff review with reason/version,
   populate verified fields and approve, return, reject or revoke. Audit commits locally.
4. Worker processes evidence deletion and Cognito access/MFA changes, then existing
   outbox/broker/notification/message work. Failures remain inspectable and retryable.

## 3 Boundaries and failures

Identity uses issuer/sub, never automatic email linkage. Local account restrictions
apply on every authenticated request. Capability adapters must check VerifiedRole or
require_role for current eligibility; onboarding endpoints allow pending users.
Provider errors are safe; credentials never enter activity or operation payloads.
[ADR-002](decisions/002-cognito-and-verified-profiles.md) documents transaction
exceptions and revocation limits. No cross-provider atomicity is claimed.

## 4 Interfaces and limits

See [web/mobile contracts](../infrastructure/README.md#web-and-mobile-contracts).
No training delivery, CPD tracking, automated registry lookup or school contact is
implemented. WhatsApp remains an optional notification/observation adapter.
