# Detailed requirements

## 1 Approved foundation requirements

<a id="req-1.1.1"></a>
**REQ-1.1.1 — Account access**

- **Status:** Required design.
- **Source:** Approved implementation plan.
- **Behavior:** Email login with registered, verified, suspended, disabled, deleted states. Registered users may only verify, resend, or log out. Blocked users lose existing credentials; deleted accounts cannot return.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-1.1.2"></a>
**REQ-1.1.2 — Profiles**

- **Status:** Required design.
- **Source:** Approved implementation plan.
- **Behavior:** Create one profile per account. Signup permits learner/trainer; staff assigns roles. Validation progresses unvalidated → submitted → pending → validated, with staff return for changes and no self-review.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-1.1.3"></a>
**REQ-1.1.3 — Verification**

- **Status:** Required design.
- **Source:** Approved implementation plan.
- **Behavior:** Five-digit, ten-minute email proofs are single-use and replaced on resend. Five attempts per proof; five issuances per ten-minute account window. Repeated blocks within 24 hours require staff review.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-2.1.1"></a>
**REQ-2.1.1 — Communication**

- **Status:** Required design.
- **Source:** Approved implementation plan.
- **Behavior:** Durable events drive optional welcome notifications. Messages own provider dispatch, deduplication, and delivery evidence. Requested proof delivery is transient and independent of general opt-in.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

<a id="req-3.1.1"></a>
**REQ-3.1.1 — Development**

- **Status:** Required design.
- **Source:** Approved implementation plan.
- **Behavior:** Run Django through uv with PostgreSQL, RabbitMQ and Mailpit in Docker Compose. Provide HTML and REST interfaces, automated checks, and documented configuration.
- **Acceptance evidence:** Automated account, messaging, and integration tests.

## 2 Open decisions

See [OPEN-001-1](001-general-description.md#open-001-1).
