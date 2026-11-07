# Detailed requirements

## 1 Approved foundation requirements

<a id="req-1.1.1"></a>
**REQ-1.1.1 — Account access**

- **Status:** Required design.
- **Source:** Approved implementation plan, revised by the Cognito/profile plan on 2026-11-06.
- **Behavior:** Cognito email login with Django browser sessions and managed-login/code/PKCE mobile access tokens. Local registered, verified, suspended, disabled, deleted states remain. Registered users may only verify, resend, or log out. Blocked users lose existing credentials; deleted accounts cannot return.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-1.1.2"></a>
**REQ-1.1.2 — Profiles**

- **Status:** Required design.
- **Source:** Approved implementation plan, revised by the Cognito/profile plan on 2026-11-06.
- **Behavior:** Create one profile per account. One professional/student category. Pending users manage onboarding only; approved students learn and approved professionals learn or train. Staff authority is independent. Verification progresses unvalidated → submitted → pending → validated, with return, rejection, revocation and no self-review. Category changes remove access until reapproval. Biography/contact fields remain user-managed and explicitly unverified.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-1.1.3"></a>
**REQ-1.1.3 — Verification**

- **Status:** Required design.
- **Source:** Approved implementation plan, revised by the Cognito/profile plan on 2026-11-06.
- **Behavior:** Cognito owns email confirmation, recovery and optional TOTP MFA. Professionals submit council/number for manual registry checks; students upload private JPEG/PNG/PDF cards up to 10 MB. Staff populate verified registered name and professional credentials or programme/school. Card review suffices; school contact is deferred. Decisions require reasons and current versions; cards are inaccessible after approval/rejection and deletion retries durably.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-2.1.1"></a>
**REQ-2.1.1 — Communication**

- **Status:** Required design.
- **Source:** Approved implementation plan, revised by the Cognito/profile plan on 2026-11-06.
- **Behavior:** Durable events drive optional welcome notifications. Messages own provider dispatch, deduplication, and delivery evidence. Cognito owns requested identity-message delivery independently of application notification opt-in.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-3.1.1"></a>
**REQ-3.1.1 — Development**

- **Status:** Required design.
- **Source:** Approved implementation plan, revised by the Cognito/profile plan on 2026-11-06.
- **Behavior:** Run Django through uv with PostgreSQL, RabbitMQ and Mailpit in Docker Compose. Provide HTML and REST interfaces, automated checks, and documented configuration.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-1.1.4"></a>
**REQ-1.1.4 — Activity and recovery**

- **Status:** Required design.
- **Source:** Approved Cognito/profile plan, 2026-11-06.
- **Behavior:** Append-only activity traces actor, subject, time, reason and changed
  values. Staff see history; users see status and review feedback. Staff-assisted MFA
  reset requires an external identity check and reason; self-reset is forbidden.
  Credentials, codes, tokens and evidence contents never enter activity records.
- **Acceptance evidence:** Audit immutability/rollback and recovery tests.

## 2 Open decisions

See [OPEN-001-1](001-general-description.md#open-001-1).
