# Architecture Decisions

## 1 Purpose

This directory contains Architecture Decision Records (ADRs) for significant
technical, architectural, and design decisions. ADRs preserve why a decision was
made so future contributors can understand its context and trade-offs.

## 2 When to create an ADR

Create an ADR when a decision affects system structure, conventions, module or
service boundaries, important dependencies, inter-module communication, domain
modelling, or a significant trade-off. Use one when a future contributor would
reasonably ask why the project took a particular direction. Routine implementation
details do not normally need an ADR.

## 3 Naming and status

Use sequential filenames with a short descriptive name, for example
`001-initial-architecture.md`. Do not renumber existing ADRs. Refer
to records by stable identifiers such as `ADR-001`.

Use one of these statuses:

- **Proposed** — under consideration; not an adopted project rule.
- **Accepted** — currently adopted by the project.
- **Experimental** — being tested before full adoption.
- **Deprecated** — no longer recommended for new work.
- **Superseded** — replaced by a later ADR; link to its replacement.
- **Rejected** — considered and deliberately not adopted.

The date records when this ADR was written, not necessarily when the decision was
originally made. State when the original decision date is unknown. Do not infer
approval from implementation evidence alone.

## 4 ADR structure

Use numbered headings and keep only sections that add useful information. The
date and status fields are required; other sections may be omitted when they do
not apply.

```markdown
# ADR NNN — Decision title

**Date:** YYYY-MM-DD (record date; original decision date unknown, if applicable)
**Status:** Proposed | Accepted | Experimental | Deprecated | Superseded | Rejected

## 1 Context

<Problem, constraint, or architectural question.>

## 2 Decision

<What was decided, with scope and limits.>

## 3 Rationale

<Why this direction was chosen.>

## 4 Alternatives considered

- <Alternative and why it was not selected, or why it remains open.>

## 5 Consequences

- **Benefits:** <Expected benefits>
- **Costs and limitations:** <Trade-offs>

## 6 Related decisions

- <Links to related ADRs or architecture records, or None.>
```

## 5 Decision index

- [ADR-001 — Django foundation](001-django-foundation.md): Accepted.

## 6 Relationship to other documentation

- Requirements and use cases describe what the system must do.
- Architecture documents describe how responsibilities and components are
  structured.
- Style and contribution guides define conventions and workflow.
- ADRs explain why significant choices were made and what trade-offs they carry.

Update architecture documentation when an ADR changes the documented design.
Do not use ADRs to hide unresolved business requirements or to imply that a
proposed choice has been approved.

## 7 Updating decisions

Accepted ADRs should generally remain as historical records. When a decision
changes, create a new ADR and mark the earlier one **Superseded**, linking to the
replacement. Minor clarifications and corrections are fine; preserve the original
reasoning and decision history.

## 8 Using ADRs during development

Before a significant architectural change:

1. Read relevant existing ADRs.
2. Follow accepted decisions unless the change explicitly revisits them.
3. Write a new ADR when a material decision is introduced or an existing decision
   no longer fits.
4. Link relevant ADRs in the pull request using the project template.

ADRs should make implementation and review clearer without adding paperwork to
routine changes.
