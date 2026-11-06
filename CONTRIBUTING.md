# Contributing

Read [architecture](ARCHITECTURE.md), [style](STYLE_GUIDE.md), the selected
[profile](profiles/README.md), and relevant requirements and ADRs before changing
behavior. Inspect affected code, callers, tests, and current Git changes.

## Development and changes

Follow [project setup](README.md) before using language tooling. Pin compatible
toolchains and dependencies; use the same versions locally and in CI. Document
configuration, build, usage, and test commands as components are introduced.
This project requires uv and the local PostgreSQL service; broker tests also require RabbitMQ.

Keep changes focused and preserve unrelated work. Identify acceptance cases,
implement the behavior, and update tests, requirements, contracts, and architecture
together. Explain dependency additions. Resolve material business ambiguities
rather than inventing lifecycle, access, retention, or delivery policies.

Preserve migrations applied in shared environments; add new ones. Document data
conversion, deployment order, compatibility, and recovery when relevant. Consider
consumers of service, transport, and event contracts. Never use production or
shared data for destructive testing.

## Issue tracking

Use the supplied [bug](.github/ISSUE_TEMPLATE/bug_report.md),
[feature](.github/ISSUE_TEMPLATE/feature_request.md), and
[task](.github/ISSUE_TEMPLATE/task.md) templates. Search for duplicates, describe
one reviewable outcome, and include acceptance criteria. Small fixes may go straight
to a PR. Other hosting platforms may reuse the Markdown bodies.

Triage scope and evidence, agree acceptance criteria, link implementation work,
then review verification. Close an issue when its criteria are met; retain unresolved
scope explicitly. Use `Closes #123` only for complete resolutions and `Refs #123`
for partial work, replacing example numbers. Issues do not replace requirements
or imply approval of business rules. No custom labels or automation are required.

## Validate and report results

For documentation changes, check relative links and anchors, examples, numbering,
identifier uniqueness, cross-references, profile consistency, and source readability.
Template IDs are illustrative until allocated; check uniqueness within their
intended scope, not across repeated example blocks. Check placeholders have not
been mistaken for requirements and project-specific content has not leaked into
reusable guidance.

For code changes, run selected profile formatting, static
analysis, build, test, and documentation checks plus relevant integration checks.
Configure CI to enforce those same checks. Use isolated infrastructure, and report
unavailable checks and their impact rather than claiming success. Check boundary
errors, lifecycle constraints, and safe external responses where applicable.

Inspect the final diff for scope, secrets, generated artifacts, and unintended edits.
Report commands actually run, outcomes, and unresolved failures. Required checks
must pass before code is described as ready to merge; pre-existing failures remain
visible and unrelated repairs stay separately scoped.

## Prepare the review

Use the [PR template](.github/pull_request_template.md). Lead with the problem and
resulting behavior, then describe material decisions, compatibility, verification,
and documentation updates. Keep detail proportional to the change. Never mark a
check complete without evidence; use `Not applicable` with a reason where needed.
