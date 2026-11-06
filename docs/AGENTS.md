# Documentation agent instructions

## 1 Scope and sources

These instructions apply to `docs/` and supplement [the root instructions](../AGENTS.md).
Read [000-docs-guide.md](000-docs-guide.md) before editing, together with the root
[style](../STYLE_GUIDE.md), [architecture](../ARCHITECTURE.md), and
[contribution](../CONTRIBUTING.md) standards. Consult the upstream requirements
and maps for the artifact being changed.

## 2 Editing rules

- Follow the guide's templates, numbered headings, typed identifiers, and explicit
  anchors. Keep identifiers stable and cross-document references linked.
- Optimize Markdown for source reading and small diffs. Requirements, business
  architecture, and use cases must use separate records with labeled bullets,
  not Markdown or HTML tables. Apply this to templates, indexes, cross-mappings,
  open decisions, and legacy mappings as well. Preserve existing content and IDs
  when changing presentation.
- Put anchors on their own lines before record titles. Keep field order consistent
  and wrap prose at roughly 80–100 characters without breaking links or identifiers.
  Avoid manual alignment and unrelated reflow. Reserve tables elsewhere for small,
  stable comparisons or technical lookup data.
- Preserve business meaning. Correct grammar and numbering without silently
  changing permissions, states, relationships, or acceptance conditions.
- Derive capabilities, information concepts, and value streams from requirements;
  derive data and application designs from those maps. Do not treat existing code
  or tables as the sole definition of the business.
- Keep business abilities and concepts separate from implementation mechanisms.
  Do not turn every attribute into a concept or every capability into a service.
- State whether material is required design, a supported derivation, a proposal,
  or implementation evidence. A source file is not proof of an operational feature.
- Record unknown rules under a document-qualified `OPEN` identifier. Ask for
  business decisions when needed; never fill gaps with invented policy.
- Review downstream references after an upstream change. Update affected maps,
  acceptance criteria, and evidence, or identify the unresolved impact explicitly.
- Use the guide's self-contained methodology. Blank templates are
  illustrative and do not establish requirements or implementation evidence.

## 3 Constructing grouped use cases

Use [use-cases/000-use-case-template.md](use-cases/000-use-case-template.md) to
create detailed use cases in `use-cases/NNN-<area>-use-cases.md`, starting at `001`.
Group related actor goals by domain, based on the project requirements. Keep `000`
for the template and preserve allocated filenames.

- Begin each file with numbered group scope and use-case index sections. Each use
  case gets a numbered H2 section and all 17 template fields as H3 subsections.
  Adjust their numeric prefix for the containing case; do not restart headings
  at 1 for each use case.
- Write indexes and record fields as labeled lists, success flows as numbered
  steps with actor/system bullets, and alternatives/exceptions as separate branch
  blocks. Do not collapse a use case or its flows into a table.
- Allocate globally unique `UC-001`-style IDs across this directory, independently
  of file numbers. Search existing IDs first, preserve them when moving cases,
  and create explicit anchors and links. Alternative, exception, and acceptance
  labels are local to their UC.
- Derive each case from linked REQ and CAP records and relevant value stages.
  Follow the trail through business rules, INFO objects, state changes, domain
  events, and application contracts. Describe business interactions rather than
  language-specific calls, SQL, or assumed screen sequences.
- Define actors, triggers, preconditions, success outcomes, alternatives,
  exceptions, and failure guarantees. Branches identify their origin and rejoin
  or termination. Do not assume universal authentication, automatic rollback,
  delivery guarantees, or unrecorded lifecycle transitions.
- Reference rules through their owning requirements. If a separate shared rule
  is needed, define its unique `BR-001`-style record and anchor alongside the source
  requirement in `002-detailed-requirements.md`; reuse it rather than duplicating
  policy in several cases. Keep proposals and approval status explicit.
- Use `OPEN-UC-001-1`-style IDs for new case-specific questions, and link existing
  upstream OPEN records when they already own the decision. Do not allocate real
  records from the illustrative template until a case is authored.
- Keep priority and status evidence-based. Review, approval, and implementation
  labels require supporting evidence. Ensure acceptance criteria cover relevant
  branch outcomes, state restrictions, and requirements before marking a case ready.

## 4 Recording architecture decisions

Use [decisions/README.md](decisions/README.md) as the authority for creating and
maintaining Architecture Decision Records (ADRs). Read relevant ADRs before
making a material architectural change and follow accepted decisions unless the
change explicitly revisits them. Create an ADR for significant boundary,
dependency, communication, domain-model, or trade-off decisions; routine
implementation details do not normally need one.

Name records `NNN-short-description.md` using the next available number. Never
renumber existing records. Preserve decision history by creating a replacement
ADR and marking the earlier record Superseded with a link. Keep statuses
evidence-based and distinguish proposals from adopted rules. Update the decision
index and link relevant ADRs in affected architecture documents and pull requests.

## 5 Validation and handoff

Check heading numbering, identifier uniqueness, parent relationships, anchors,
relative links, and cross-map targets. Review state names, type classifications,
cardinalities, and terminology across documents. During restructuring, preserve
a mapping from ambiguous or changed legacy references to their replacements.
Inspect the raw Markdown and diff, including fenced templates, for readability
and compliance with the table restrictions.
For use cases, also check group indexes, globally unique IDs, flow step references,
related-case direction, and acceptance coverage. Links to the main numbered docs
from `use-cases/` must use the appropriate `../` path.

Keep templates recognizable as examples, with placeholders distinct from project
decisions. Verify technical evidence against the repository and label its limits.
For documentation-only changes, use documentation checks rather than unrelated
code repairs. Report changed artifacts, checks performed, and open decisions.
