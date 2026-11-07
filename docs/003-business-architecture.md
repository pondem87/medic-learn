# Business architecture

## 1 Capabilities

<a id="cap-1"></a>
**CAP-1 — Account and profile management**

- **Purpose:** Establish identity, eligibility, role, and profile review outcomes.
- **Source:** [Account requirements](002-detailed-requirements.md#req-1.1.1).
- **Uses/modifies:** Account and profile information.

<a id="cap-2"></a>
**CAP-2 — User communication**

- **Purpose:** Coordinate optional notifications; Cognito delivers identity proofs.
- **Source:** [Communication requirements](002-detailed-requirements.md#req-2.1.1).
- **Uses/modifies:** Notification and message information.

## 2 Information

<a id="info-1"></a>
**INFO-1 — Account**

- **Definition:** Email identity with an eligibility lifecycle.
- **Associations:** Exactly one dependent profile; many verification activities and messages.
- **Types:** One professional/student category with separate verification and learner/trainer eligibility. Staff authority is independent.

## 3 Value stream

<a id="vs-1"></a>
**VS-1 — Establish participation**

1. Applicant registers and receives a verification message.
2. Applicant proves email ownership and gains authenticated access.
3. Participant submits a profile; staff reviews and records a validation outcome.

## 4 Open decisions

No course-delivery or streaming capability is inferred. See
[OPEN-001-1](001-general-description.md#open-001-1).
