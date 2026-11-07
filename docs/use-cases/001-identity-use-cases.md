# Identity and participation use cases

## 1 Group scope

Approved identity/profile plan. Covers [CAP-1](../003-business-architecture.md#cap-1)
and [VS-1](../003-business-architecture.md#vs-1); excludes training delivery.

## 2 Use-case index

**[UC-001](#uc-001) — Authenticate and recover access**

- **Primary actor:** Applicant or account holder.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Priority:** Required for the approved increment.
- **Status:** Approved by the implementation-plan request.

**[UC-002](#uc-002) — Submit professional or student status**

- **Primary actor:** Confirmed account holder.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Priority:** Required for the approved increment.
- **Status:** Approved by the implementation-plan request.

**[UC-003](#uc-003) — Review and maintain verified status**

- **Primary actor:** Staff reviewer.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Priority:** Required for the approved increment.
- **Status:** Approved by the implementation-plan request.

**[UC-004](#uc-004) — Manage biography and assumed role**

- **Primary actor:** Confirmed account holder.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Priority:** Required for the approved increment.
- **Status:** Approved by the implementation-plan request.

**[UC-005](#uc-005) — Restrict access or recover a lost authenticator**

- **Primary actor:** Staff operator.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Priority:** Required for the approved increment.
- **Status:** Approved by the implementation-plan request.

<a id="uc-001"></a>

## 3 UC-001 — Authenticate and recover access

### 3.1 Use case identification

- **ID:** UC-001.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.1); approved implementation plan.
- **Priority:** Required for this increment.
- **Status:** Approved; AWS acceptance remains a deployment check.

### 3.2 Purpose

- **Goal:** Authenticate and recover access.
- **Value:** Controlled, attributable participation.

### 3.3 Actors

- **Primary:** Applicant or account holder.
- **Supporting:** Staff and Cognito where authentication is involved.
- **Stakeholder:** Account holder; secure access and accurate credentials.

### 3.4 Preconditions

No session is required for registration, login, confirmation or reset. MFA setup requires recent authenticated access.

### 3.5 Trigger

The actor requests to authenticate and recover access.

### 3.6 Main success flow

1. **Actor:** Provide registration or sign-in details.
   **System:** Delegate credentials to Cognito and request required confirmation or MFA.

2. **Actor:** Complete the requested proof.
   **System:** Create a web session or issue mobile Cognito credentials only after authentication succeeds.

### 3.7 Alternative flows

**A1 — Alternative outcome**

- **Branch:** Step 2.
- **Action/response:** Optional TOTP challenges and password recovery use their dedicated custom web screens; mobile uses managed login.
- **Termination:** The selected outcome is returned.

### 3.8 Exception flows

**E1 — Unavailable transition or dependency**

- **Failure point:** Steps 1–2.
- **Response and guarantees:** Provider failure returns a safe error; a completed remote signup may precede local persistence. Later login reconciles by subject, never automatic email linkage.
- **Recovery:** Correct the input/reload or retry after dependency recovery.

### 3.9 Postconditions

- **Success:** Authenticated account/session; email confirmation does not imply professional/student approval.
- **Failure:** E1 guarantees apply; external effects are not globally atomic.

### 3.10 Business rules

- **Authority:** [Requirement](../002-detailed-requirements.md#req-1.1.1).
- **Application:** Both main steps and A1/E1.

### 3.11 Data / information requirements

- **Input/output:** Credentials/proofs are transient; issuer/subject bind local identity. No credential values enter audit.
- **Objects:** [INFO-1](../003-business-architecture.md#info-1).

### 3.12 State changes

- **Transition/guard:** registered → verified on confirmed authentication; suspended/disabled/deleted never grant access.
- **Invalid transitions:** Rejected under [Requirement](../002-detailed-requirements.md#req-1.1.1).

### 3.13 Events

users.verified is enqueued once with local email-confirmation activation.

### 3.14 Non-functional requirements

- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.1) and [architecture](../../ARCHITECTURE.md).
- **Constraint:** Safe errors, protected credentials and transactional local activity.
- **Evidence:** Account and integration tests; live AWS is separately smoke-tested.

### 3.15 Acceptance criteria

- **AC1:** Given the preconditions, completing the main flow yields: Authenticated account/session; email confirmation does not imply professional/student approval.
- **AC2:** Given E1, the action returns a safe failure with its documented guarantees.
- **AC3:** A1 yields only the category/access outcomes allowed by [Requirement](../002-detailed-requirements.md#req-1.1.1).
- **Evidence:** [Account tests](../../tests/test_accounts.py) and
  [integration tests](../../tests/test_integration.py).

### 3.16 Related use cases

- **Related:** Other cases in this group share account/profile state.
- **Includes/extends:** None; no mandatory nested use-case invocation is claimed.

### 3.17 Notes / open decisions

School contact, course delivery and wider operating policies remain deferred under
[OPEN-001-1](../001-general-description.md#open-001-1).

<a id="uc-002"></a>

## 4 UC-002 — Submit professional or student status

### 4.1 Use case identification

- **ID:** UC-002.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.3); approved implementation plan.
- **Priority:** Required for this increment.
- **Status:** Approved; AWS acceptance remains a deployment check.

### 4.2 Purpose

- **Goal:** Submit professional or student status.
- **Value:** Controlled, attributable participation.

### 4.3 Actors

- **Primary:** Confirmed account holder.
- **Supporting:** Staff and Cognito where authentication is involved.
- **Stakeholder:** Account holder; secure access and accurate credentials.

### 4.4 Preconditions

Account is confirmed; no submitted/pending review is already active.

### 4.5 Trigger

The actor requests to submit professional or student status.

### 4.6 Main success flow

1. **Actor:** Choose category and supply council/number or student card.
   **System:** Validate the submission and privately store student evidence.

2. **Actor:** Submit for staff review.
   **System:** Record submitted status and audit; remove prior role eligibility pending approval.

### 4.7 Alternative flows

**A1 — Alternative outcome**

- **Branch:** Step 2.
- **Action/response:** Returned or rejected applicants can resubmit; category changes also require fresh approval.
- **Termination:** The selected outcome is returned.

### 4.8 Exception flows

**E1 — Unavailable transition or dependency**

- **Failure point:** Steps 1–2.
- **Response and guarantees:** Invalid files or missing registry details fail safely. Failed submission uploads remain tracked for cleanup; existing review state is preserved.
- **Recovery:** Correct the input/reload or retry after dependency recovery.

### 4.9 Postconditions

- **Success:** Submission is reviewable; user has onboarding access only.
- **Failure:** E1 guarantees apply; external effects are not globally atomic.

### 4.10 Business rules

- **Authority:** [Requirement](../002-detailed-requirements.md#req-1.1.3).
- **Application:** Both main steps and A1/E1.

### 4.11 Data / information requirements

- **Input/output:** Council/number are claims until approval. Cards accept JPEG/PNG/PDF up to 10 MB and are not public.
- **Objects:** [INFO-1](../003-business-architecture.md#info-1).

### 4.12 State changes

- **Transition/guard:** unvalidated/rejected/revoked/validated → submitted; an in-progress review cannot be overwritten.
- **Invalid transitions:** Rejected under [Requirement](../002-detailed-requirements.md#req-1.1.3).

### 4.13 Events

No broker event; an activity record describes the local submission.

### 4.14 Non-functional requirements

- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.3) and [architecture](../../ARCHITECTURE.md).
- **Constraint:** Safe errors, protected credentials and transactional local activity.
- **Evidence:** Account and integration tests; live AWS is separately smoke-tested.

### 4.15 Acceptance criteria

- **AC1:** Given the preconditions, completing the main flow yields: Submission is reviewable; user has onboarding access only.
- **AC2:** Given E1, the action returns a safe failure with its documented guarantees.
- **AC3:** A1 yields only the category/access outcomes allowed by [Requirement](../002-detailed-requirements.md#req-1.1.3).
- **Evidence:** [Account tests](../../tests/test_accounts.py) and
  [integration tests](../../tests/test_integration.py).

### 4.16 Related use cases

- **Related:** Other cases in this group share account/profile state.
- **Includes/extends:** None; no mandatory nested use-case invocation is claimed.

### 4.17 Notes / open decisions

School contact, course delivery and wider operating policies remain deferred under
[OPEN-001-1](../001-general-description.md#open-001-1).

<a id="uc-003"></a>

## 5 UC-003 — Review and maintain verified status

### 5.1 Use case identification

- **ID:** UC-003.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.3); approved implementation plan.
- **Priority:** Required for this increment.
- **Status:** Approved; AWS acceptance remains a deployment check.

### 5.2 Purpose

- **Goal:** Review and maintain verified status.
- **Value:** Controlled, attributable participation.

### 5.3 Actors

- **Primary:** Staff reviewer.
- **Supporting:** Staff and Cognito where authentication is involved.
- **Stakeholder:** Account holder; secure access and accurate credentials.

### 5.4 Preconditions

Staff is authenticated and is not reviewing their own account; a current profile version is supplied.

### 5.5 Trigger

The actor requests to review and maintain verified status.

### 5.6 Main success flow

1. **Actor:** Start review and check registry entry or student card.
   **System:** Record pending status and identify the evidence.

2. **Actor:** Enter verified details and a reason; approve.
   **System:** Atomically record validation and activity, grant category roles and revoke access to card evidence.

### 5.7 Alternative flows

**A1 — Alternative outcome**

- **Branch:** Step 2.
- **Action/response:** Staff can return for correction, reject, revoke approval or update verified fields. Every decision requires a reason; school contact is deferred.
- **Termination:** The selected outcome is returned.

### 5.8 Exception flows

**E1 — Unavailable transition or dependency**

- **Failure point:** Steps 1–2.
- **Response and guarantees:** Stale versions conflict without overwriting the newer decision. Missing required fields/evidence cannot approve. Deletion failures remain durable pending work.
- **Recovery:** Correct the input/reload or retry after dependency recovery.

### 5.9 Postconditions

- **Success:** Verified fields and decision are attributable; students learn and professionals learn/train.
- **Failure:** E1 guarantees apply; external effects are not globally atomic.

### 5.10 Business rules

- **Authority:** [Requirement](../002-detailed-requirements.md#req-1.1.3).
- **Application:** Both main steps and A1/E1.

### 5.11 Data / information requirements

- **Input/output:** Verified registered name and professional council/number/profession or student programme/school; staff sees full activity, users see feedback.
- **Objects:** [INFO-1](../003-business-architecture.md#info-1).

### 5.12 State changes

- **Transition/guard:** submitted → pending → validated; return → unvalidated; rejection → rejected; revocation → revoked.
- **Invalid transitions:** Rejected under [Requirement](../002-detailed-requirements.md#req-1.1.3).

### 5.13 Events

Evidence deletion is durably requested on approval/rejection; no globally atomic storage deletion is claimed.

### 5.14 Non-functional requirements

- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.3) and [architecture](../../ARCHITECTURE.md).
- **Constraint:** Safe errors, protected credentials and transactional local activity.
- **Evidence:** Account and integration tests; live AWS is separately smoke-tested.

### 5.15 Acceptance criteria

- **AC1:** Given the preconditions, completing the main flow yields: Verified fields and decision are attributable; students learn and professionals learn/train.
- **AC2:** Given E1, the action returns a safe failure with its documented guarantees.
- **AC3:** A1 yields only the category/access outcomes allowed by [Requirement](../002-detailed-requirements.md#req-1.1.3).
- **Evidence:** [Account tests](../../tests/test_accounts.py) and
  [integration tests](../../tests/test_integration.py).

### 5.16 Related use cases

- **Related:** Other cases in this group share account/profile state.
- **Includes/extends:** None; no mandatory nested use-case invocation is claimed.

### 5.17 Notes / open decisions

School contact, course delivery and wider operating policies remain deferred under
[OPEN-001-1](../001-general-description.md#open-001-1).

<a id="uc-004"></a>

## 6 UC-004 — Manage biography and assumed role

### 6.1 Use case identification

- **ID:** UC-004.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.2); approved implementation plan.
- **Priority:** Required for this increment.
- **Status:** Approved; AWS acceptance remains a deployment check.

### 6.2 Purpose

- **Goal:** Manage biography and assumed role.
- **Value:** Controlled, attributable participation.

### 6.3 Actors

- **Primary:** Confirmed account holder.
- **Supporting:** Staff and Cognito where authentication is involved.
- **Stakeholder:** Account holder; secure access and accurate credentials.

### 6.4 Preconditions

Bio editing requires confirmed access; role selection requires approved category eligibility.

### 6.5 Trigger

The actor requests to manage biography and assumed role.

### 6.6 Main success flow

1. **Actor:** Edit personal contact details or biography.
   **System:** Save and audit only user-managed fields, labelled unverified.

2. **Actor:** Choose an eligible role.
   **System:** Keep the web selection per session; validate mobile request role against current permissions.

### 6.7 Alternative flows

**A1 — Alternative outcome**

- **Branch:** Step 2.
- **Action/response:** Approved professionals can choose learner or trainer; students have learner only. Another device retains its independent web selection.
- **Termination:** The selected outcome is returned.

### 6.8 Exception flows

**E1 — Unavailable transition or dependency**

- **Failure point:** Steps 1–2.
- **Response and guarantees:** Forged staff/unsupported role is rejected. Verified fields cannot be written through profile PATCH. Revoked status removes capability access.
- **Recovery:** Correct the input/reload or retry after dependency recovery.

### 6.9 Postconditions

- **Success:** Biography remains editable after approval without changing verified details.
- **Failure:** E1 guarantees apply; external effects are not globally atomic.

### 6.10 Business rules

- **Authority:** [Requirement](../002-detailed-requirements.md#req-1.1.2).
- **Application:** Both main steps and A1/E1.

### 6.11 Data / information requirements

- **Input/output:** User-managed name, phone, biography and notification preference; no claims of verification for bio.
- **Objects:** [INFO-1](../003-business-architecture.md#info-1).

### 6.12 State changes

- **Transition/guard:** Profile approval is unchanged by bio edits. Role selection does not change category or staff authority.
- **Invalid transitions:** Rejected under [Requirement](../002-detailed-requirements.md#req-1.1.2).

### 6.13 Events

Profile edits and web role selections append activity; no broker event.

### 6.14 Non-functional requirements

- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.2) and [architecture](../../ARCHITECTURE.md).
- **Constraint:** Safe errors, protected credentials and transactional local activity.
- **Evidence:** Account and integration tests; live AWS is separately smoke-tested.

### 6.15 Acceptance criteria

- **AC1:** Given the preconditions, completing the main flow yields: Biography remains editable after approval without changing verified details.
- **AC2:** Given E1, the action returns a safe failure with its documented guarantees.
- **AC3:** A1 yields only the category/access outcomes allowed by [Requirement](../002-detailed-requirements.md#req-1.1.2).
- **Evidence:** [Account tests](../../tests/test_accounts.py) and
  [integration tests](../../tests/test_integration.py).

### 6.16 Related use cases

- **Related:** Other cases in this group share account/profile state.
- **Includes/extends:** None; no mandatory nested use-case invocation is claimed.

### 6.17 Notes / open decisions

School contact, course delivery and wider operating policies remain deferred under
[OPEN-001-1](../001-general-description.md#open-001-1).

<a id="uc-005"></a>

## 7 UC-005 — Restrict access or recover a lost authenticator

### 7.1 Use case identification

- **ID:** UC-005.
- **Capability:** [CAP-1](../003-business-architecture.md#cap-1).
- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.4); approved implementation plan.
- **Priority:** Required for this increment.
- **Status:** Approved; AWS acceptance remains a deployment check.

### 7.2 Purpose

- **Goal:** Restrict access or recover a lost authenticator.
- **Value:** Controlled, attributable participation.

### 7.3 Actors

- **Primary:** Staff operator.
- **Supporting:** Staff and Cognito where authentication is involved.
- **Stakeholder:** Account holder; secure access and accurate credentials.

### 7.4 Preconditions

Staff is authenticated, targets another account, and records a reason; MFA reset requires an external identity check.

### 7.5 Trigger

The actor requests to restrict access or recover a lost authenticator.

### 7.6 Main success flow

1. **Actor:** Record restriction or verified recovery request.
   **System:** Invalidate local credentials and append activity and durable external work.

2. **Actor:** Inspect operation outcome.
   **System:** Retry Cognito synchronization/reset and record safe outcome; expose pending failures to staff.

### 7.7 Alternative flows

**A1 — Alternative outcome**

- **Branch:** Step 2.
- **Action/response:** Suspension/disable can be restored; deletion is terminal. Lost MFA recovery does not rely solely on email password reset.
- **Termination:** The selected outcome is returned.

### 7.8 Exception flows

**E1 — Unavailable transition or dependency**

- **Failure point:** Steps 1–2.
- **Response and guarantees:** No self-action or blank reason is accepted. Provider outages do not restore blocked local access; operations remain pending.
- **Recovery:** Correct the input/reload or retry after dependency recovery.

### 7.9 Postconditions

- **Success:** Local access reflects the restriction; remote outcome is independently traceable.
- **Failure:** E1 guarantees apply; external effects are not globally atomic.

### 7.10 Business rules

- **Authority:** [Requirement](../002-detailed-requirements.md#req-1.1.4).
- **Application:** Both main steps and A1/E1.

### 7.11 Data / information requirements

- **Input/output:** Actor, subject, reason, timestamp and operation identifiers; never passwords, tokens or MFA secrets.
- **Objects:** [INFO-1](../003-business-architecture.md#info-1).

### 7.12 State changes

- **Transition/guard:** Eligible account → suspended/disabled/deleted; restore preserves prior eligible state and invalidates old credentials.
- **Invalid transitions:** Rejected under [Requirement](../002-detailed-requirements.md#req-1.1.4).

### 7.13 Events

Durable operation request and outcome activity; no secret-bearing broker payload.

### 7.14 Non-functional requirements

- **Source:** [Requirement](../002-detailed-requirements.md#req-1.1.4) and [architecture](../../ARCHITECTURE.md).
- **Constraint:** Safe errors, protected credentials and transactional local activity.
- **Evidence:** Account and integration tests; live AWS is separately smoke-tested.

### 7.15 Acceptance criteria

- **AC1:** Given the preconditions, completing the main flow yields: Local access reflects the restriction; remote outcome is independently traceable.
- **AC2:** Given E1, the action returns a safe failure with its documented guarantees.
- **AC3:** A1 yields only the category/access outcomes allowed by [Requirement](../002-detailed-requirements.md#req-1.1.4).
- **Evidence:** [Account tests](../../tests/test_accounts.py) and
  [integration tests](../../tests/test_integration.py).

### 7.16 Related use cases

- **Related:** Other cases in this group share account/profile state.
- **Includes/extends:** None; no mandatory nested use-case invocation is claimed.

### 7.17 Notes / open decisions

School contact, course delivery and wider operating policies remain deferred under
[OPEN-001-1](../001-general-description.md#open-001-1).

