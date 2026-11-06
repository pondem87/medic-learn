# Documentation guide

## 1 Purpose and document ownership

This guide defines the structure and derivation of the numbered project documents.
The starter ships blank templates; they are not approved requirements or evidence
of implemented features. Fill relevant sections and mark others `Not applicable`
with a reason. Use it with [ARCHITECTURE.md](../ARCHITECTURE.md), which owns implementation
boundaries, [STYLE_GUIDE.md](../STYLE_GUIDE.md), which owns coding conventions, and
[CONTRIBUTING.md](../CONTRIBUTING.md), which owns contribution and validation rules.
The numbered architectures describe each new project using those standards; they must
not establish conflicting rules.

| File | Purpose and principal input | Output |
| --- | --- | --- |
| [001-general-description.md](001-general-description.md) | Product intent, stakeholders, and scope | Shared vocabulary, capability overview, quality goals |
| [002-detailed-requirements.md](002-detailed-requirements.md) | Elaborate 001 into observable obligations | Functional and quality requirements with acceptance criteria |
| [003-business-architecture.md](003-business-architecture.md) | Interpret 002 in business terms | Capability, information, and value maps with cross-mappings |
| [004-data-architecture.md](004-data-architecture.md) | Derive data from 003 and its source requirements | Conceptual relationships, logical entities, attributes, physical mappings |
| [005-application-architecture.md](005-application-architecture.md) | Allocate business capabilities and workflows to components | Contracts, interactions, state handling, and failure boundaries |
| [006-technology-architecture.md](006-technology-architecture.md) | Realize 004 and 005 under quality constraints from 002 | Runtime, infrastructure, deployment, security, and operational design |
| [use-cases/000-use-case-template.md](use-cases/000-use-case-template.md) and grouped use-case files | Elaborate requirements and capabilities into actor interactions | Detailed flows, shared-rule references, state/event outcomes, and acceptance criteria |
| [decisions/README.md](decisions/README.md) and numbered ADRs | Preserve why significant design choices were made | Context, adopted direction, alternatives, and consequences |

## 2 Numbering and references

### 2.1 Files and headings

Retain the `NNN-kebab-case.md` filenames and sequence `000`–`006`. Agent
instructions retain the special filename `AGENTS.md`. Each document has one H1
title. Use numbered H2 sections (`## 1 Purpose`), H3 subsections (`### 1.1 Scope`),
and H4 subsections (`#### 1.1.1 Detail`). Numbers follow their actual parent and
are sequential within each level. Labeled lists may hold records without creating
a heading for each one. Template code fences are examples, not sections of this
guide.

The `use-cases/` directory has its own three-digit file sequence: `000` holds its
template, followed by `001-<area>-use-cases.md`, `002-<area>-use-cases.md`, and so on.
Each grouped file follows the same heading rules and contains multiple use cases.
The `decisions/` directory has an independent three-digit sequence beginning at
`001`; `README.md` explains ADR status, structure, and maintenance. ADR identifiers
use the `ADR-001` form and remain stable when records are superseded.

### 2.2 Stable record identifiers

Heading numbers express presentation order. Record identifiers express identity
and are independent of heading numbers. Define each record once in its owning
document; references elsewhere must link to that definition.

| Prefix | Owner | Example |
| --- | --- | --- |
| `REQ` | 002: functional obligation, grouped by domain and operation | `REQ-1.1.1` |
| `NFR` | 002: quality obligation, grouped by quality area | `NFR-1.1` |
| `CAP` | 003: capability and its child capabilities | `CAP-1.7.2` |
| `INFO` | 003: concept; dependent concepts may use their parent's prefix | `INFO-1.3` |
| `VS`, `STAGE` | 003: value stream and owned stage | `VS-1`, `STAGE-1.2` |
| `DATA` | 004: logical entity candidate or defined entity | `DATA-1` |
| `APP` | 005: application component | `APP-1` |
| `TECH` | 006: technology element | `TECH-1` |
| `UC` | A grouped file in use-cases/: unique across all groups | `UC-001` |
| `BR` | 002: shared business rule defined alongside its source requirement | `BR-001` |
| `OPEN` | Document owning the unresolved decision | `OPEN-003-1` |

Use-case-specific open decisions use `OPEN-UC-001-1` to avoid collisions with
numbered architecture documents. UC and BR identifiers use independent sequences
with three-digit numbers. Reuse REQ IDs directly where they already identify a
rule; allocate a BR ID only for a distinct rule that needs its own shared record.
ADRs use their sequence as identity (`ADR-001`) and are owned by
`docs/decisions/README.md`; do not renumber them when their status changes.

Create explicit lowercase anchors, for example `<a id="req-1.1.1"></a>`, immediately
on its own line before a record's title. Link as
`[REQ-1.1.1](002-detailed-requirements.md#req-1.1.1)`. Do not rely on generated
heading anchors for durable record references. A child capability has exactly one
parent. A stage belongs to the value stream with the same first numeric component.

Once real records are allocated, preserve identifiers when records move. Add new
IDs without reusing retired ones; retain a redirect or migration record for a
renamed, merged, or retired item. During a deliberate hierarchy change, record
both the old and new parent and identifiers. Legacy mappings must include the
original section and label when the old number was ambiguous.

### 2.3 Status and uncertainty

Separate **required design** (an explicit requirement or adopted project rule),
**derived design** (a reasoned mapping with linked sources), **proposed design**
(awaiting a decision), and **implementation evidence** (what inspected artifacts
actually establish). A derived mapping does not approve new business policy.

Use `Not specified — OPEN-...` for unknown values, and `None` only for confirmed
absence. Open-decision records name the question, its source, affected artifacts,
and the decision needed. An incomplete acceptance criterion is not a passing
test or a completed requirement.

### 2.4 Markdown for human editing

Follow the [Markdown source style](../STYLE_GUIDE.md#markdown-source-readability).
Requirements, business architecture, and detailed use cases must not use Markdown
or HTML tables, including their indexes, cross-mappings, open decisions, and legacy
mappings. Use one record per block with its anchor, a bold ID or descriptive label,
and consistently ordered labeled bullets. Keep each field separately editable.

Use numbered lists for sequential interactions. Wrap prose and list continuations
at roughly 80–100 characters without splitting links or identifiers. Avoid wide
lines containing several fields, manual space alignment, and unrelated reflow.
Keep the same source format in templates. Small, stable reference tables elsewhere
in this guide or technical architectures are permitted; prose-heavy records should
remain lists.

## 3 Deriving architecture from requirements

### 3.1 Capabilities and information

1. Identify stakeholders, obligations, business objects, and outcomes in 002.
2. Name capabilities by business object and action, such as Document Management or
   Document Definition. Define what the business can do in one sentence, independently
   of process order, organizational chart, framework, or vendor.
3. Define parents before children, with each child inside its parent's scope.
   Reuse capabilities across value streams rather than duplicating them. Use
   Object/Other Object Matching for associations, with the controlling object first.
4. Derive information concepts from the business objects. A primary concept is
   independent; a secondary concept depends on another concept for existence.
   Do not promote an attribute, rating, or validation result to an entity by default.
5. Capture each concept's business definition, types, finite states, dependencies,
   and relationships. Types classify; states describe lifecycle conditions. Model
   variations as types rather than duplicating the same concept under different names.
6. Record each association once from its controlling object or parent, with
   bidirectional traceability. Map capabilities that **use** information separately
   from those that **modify** it. Document missing concepts or unclear ownership.

### 3.2 Stakeholder value

Define each value stream in action/object language with its triggering stakeholder
and desired value proposition. Stages express increments of stakeholder value,
not HTTP requests, screen sequences, or implementation tasks. Record each stage's
entry conditions, exit conditions, value items, and participating stakeholders.
Use information states to explain navigation where the source supports them.

Map stages to capabilities performing work in that stage. Do not map a capability
solely because the stage consumes data produced by it elsewhere. Use the highest
capability level whose children are all relevant; otherwise select the relevant
children. A capability can enable several stages or streams.

### 3.3 Data, application, and technology derivation

Treat every primary and secondary information concept as an entity candidate,
not automatically as one physical table. Carry its business definition forward.
Use concept associations and matching capabilities to propose relationships;
validate cardinality, optionality, and ownership against concrete scenarios.
Derive attributes from decomposed capabilities and their outcomes. Distinguish
business identifiers and uniqueness rules from technical surrogate keys; not
every attribute is a natural key.

Carry types, states, and state-changing outcomes into data constraints and domain
behavior. Explain any merge, split, or deferred entity. Separate conceptual
meaning, logical structure, and physical storage. Trace acquisition, access,
modification, retention, provenance, and quality requirements to their business
sources; leave unspecified policies open.

Map capabilities and value stages to application responsibilities and contracts;
there is no required one-to-one capability/service correspondence. Map data and
application needs to technology choices using quality requirements. Record
technical evidence separately from target design. Reconcile these views whenever
requirements change rather than reverse-engineering business rules from code.

### 3.4 Detailed use cases

Use [the use-case template](use-cases/000-use-case-template.md) to elaborate
capabilities into actor goals and interactions, then trace business rules,
information needs, transitions, and events into service/API design. Group related
cases by business area. Use cases supplement requirements and value streams;
they must not introduce unapproved rules or confuse business stages with technical
implementation steps. Follow [the scoped instructions](AGENTS.md#3-constructing-grouped-use-cases)
for numbering, shared rule ownership, and validation.

### 3.5 Architecture decisions

Use ADRs to record why a significant technical, architectural, or design choice
was made. ADRs supplement the numbered architecture documents: architecture
describes the current or target structure, while an ADR preserves context,
alternatives, rationale, and consequences. An ADR does not establish business
policy absent an approved requirement. Follow
[decisions/README.md](decisions/README.md) and
[the scoped instructions](AGENTS.md#4-recording-architecture-decisions).

## 4 Document templates

Replace angle-bracket placeholders when applying a template. Example identifiers
and anchors do not allocate project records until the template is populated.
Repeated record blocks are intentional; allocate real identifiers and anchors. Fill each section with
evidence, a justified `Not applicable`, or an explicit open decision. The outlines
below are the required section structure; add numbered subsections as needed.

### 4.1 General description template

Input: product intent and stakeholder needs. Output: scope and high-level goals
linked to detailed requirements. Completion: every original goal is represented,
and scope boundaries are explicit without invented exclusions.

```markdown
# General description

## 1 Purpose

<Problem, product value, and intended outcome.>

## 2 Stakeholders and scope

<Beneficiaries, operators, external participants, included work, and open scope.>

## 3 Domain and capability overview

**Area: <Area>**

- **Business meaning and desired behavior:** <Description>
- **Detailed requirements:** <Linked REQ identifiers>

## 4 Quality goals

**Area: <Quality area>**

- **Goal:** <Goal without invented thresholds>
- **Detailed requirements:** <Linked NFR identifiers>

## 5 Traceability

<How overview goals feed 002 and business concepts in 003.>

## 6 Assumptions and open decisions

<Assumptions with sources and anchored OPEN records. Add legacy mappings only
when migrating existing documentation.>
```

### 4.2 Detailed requirements template

Input: 001 and supported business decisions. Output: testable obligations used by
003–006. Completion: every requirement has actor, trigger/precondition, outcome,
constraints, acceptance evidence, and source; unknowns are linked to OPEN records.
Shared fields may be stated once at the start of a group rather than repeated in
every record.

```markdown
# Detailed requirements

## 1 Functional requirements

### 1.1 <Domain>

Actor and trigger: <Shared context; override per record when needed.>

<a id="req-1.1.1"></a>

**REQ-1.1.1**

- **Required outcome and constraints:** <Observable obligation>
- **Acceptance criterion:** <Given/when/then or equivalent>
- **Source:** <Source>

## 2 Quality requirements

<a id="nfr-1.1"></a>

**NFR-1.1**

- **Context and obligation:** <Quality constraint>
- **Acceptance evidence:** <Measure or linked unresolved target>
- **Source:** <Source>

## 3 Downstream traceability

<Links to capabilities, value stages, and relevant architecture decisions.>

## 4 Open decisions

<Question, affected requirements, and decision needed for each OPEN record.>

## 5 Legacy reference mapping

<Use only when migrating existing records; otherwise mark Not applicable.>

**Original section and label: <Unambiguous old reference>**

- **New identifier or location:** <Linked replacement>

```

### 4.3 Business architecture template

Input: 002 and the mapping principles in section 3. Output: business abilities,
shared vocabulary, stakeholder value, and the links needed by data/application
design. Completion: one parent per capability; concept dependencies and state
uncertainties are explicit; stages have outcomes and enabling-capability links.

```markdown
# Business architecture

## 1 Purpose and sources

<Requirements, derivation status, and scope.>

## 2 Capability map

### 2.1 <Top-level capability>

<a id="cap-1"></a>

**CAP-1**

- **Name:** <Object Action>
- **Business ability or outcome:** <One-sentence definition>
- **Source:** <REQ or supported source>

## 3 Information map

<a id="info-1"></a>

**INFO-1**

- **Concept and definition:** <Business definition>
- **Category and parent:** <Primary or secondary; parent>
- **Types:** <Types>
- **States:** <States>
- **Source:** <CAP/REQ>

**Controlling concept: <INFO link>**

- **Related concept:** <INFO link or OPEN>
- **Business relationship:** <Meaning and dependency>
- **Establishing capability:** <CAP link>

## 4 Value streams

### 4.1 <Action Object>

<Anchored VS ID; definition; triggering stakeholder; value proposition; sources.>

<a id="stage-1.1"></a>

**STAGE-1.1**

- **Entry:** <Condition>
- **Exit:** <Condition>
- **Value item:** <Stakeholder value>
- **Participants:** <Roles>
- **Enabling capabilities:** <CAP links>

## 5 Cross-mappings and downstream derivation

**Concept: <INFO link>**

- **Capabilities that use it:** <CAP links>
- **Capabilities that modify it:** <CAP links>
- **Data/application references:** <DATA/APP links or OPEN>

## 6 Open decisions

<Unresolved concepts, policies, stage conditions, and mapping coverage.>

## 7 Legacy reference mapping

<When migrating existing records, map original labels to new IDs. Otherwise
mark this section Not applicable.>
```

### 4.4 Data architecture template

Input: information map, capabilities, scenarios, and constraints. Output: justified
entities and relationships with persistence mappings. Completion: business sources
exist for entities and attributes; physical evidence does not silently define policy.

```markdown
# Data architecture

## 1 Purpose and derivation

<Information-to-entity derivation and design/evidence distinction.>

## 2 Conceptual relationships

| Source concept | Entity candidate | Relationship and cardinality | Scenario or open decision |
| --- | --- | --- | --- |
| <INFO link> | <DATA link> | <Ownership, multiplicity, optionality> | <REQ/scenario/OPEN> |

## 3 Logical entities and attribute dictionary

### 3.1 <Entity>

<Anchored DATA ID; definition; source INFO/CAP/REQ; identity and lifecycle.>

| Attribute | Logical type | Constraints and business meaning | Derivation |
| --- | --- | --- | --- |
| <Name> | <Type> | <Nullability, identifier role, invariant> | <Source or technical rationale> |

## 4 Lifecycle and integrity

<States, types, supported transitions, relationships, and concurrency constraints.>

## 5 Physical mappings and evidence

<Tables, columns, SQL types, indexes, migration links, and naming differences.>

## 6 Governance and quality

<Sources, use/modify access, ownership, freshness, retention, lineage, validation.>

## 7 Open decisions and legacy mapping

<Unresolved rules, entity candidates, and old-to-new record references.>
```

### 4.5 Application architecture template

Input: capabilities, value streams, data, and root architecture rules. Output:
responsibilities and interactions allocated to components. Completion: workflow
steps trace to business outcomes and evidence never implies unsupported guarantees.

```markdown
# Application architecture

## 1 Context and design status

<Actors, external systems, scope, and status/evidence conventions.>

## 2 Components and contracts

| ID | Responsibility and contract | Business/data sources | Implementation evidence |
| --- | --- | --- | --- |
| <Anchored APP ID> | <Inputs, outputs, dependencies> | <CAP/REQ/DATA links> | <File and limits> |

## 3 Workflows and events

<Numbered steps linked to stages, components, states, and event outcomes.>

## 4 Persistence, state, and error boundaries

<Transactions, repository checks, error translation, and side-effect ordering.>

## 5 Security and quality responsibilities

<Component obligations tied to NFR and access requirements.>

## 6 Traceability and open decisions

<Coverage, unresolved interfaces and guarantees, acceptance evidence needed.>
```

### 4.6 Technology architecture template

Input: data/application needs and quality requirements. Output: justified technical
choices and operational constraints. Completion: each choice has a purpose and
source; deployment and reliability claims have evidence or remain open.

```markdown
# Technology architecture

## 1 Scope and evidence

<Target environment, evidence sources, and limits of current configuration.>

## 2 Technology elements

| ID | Element and purpose | Application/data/quality sources | Evidence and status |
| --- | --- | --- | --- |
| <Anchored TECH ID> | <Choice and rationale> | <APP/DATA/NFR links> | <Config or proposed decision> |

## 3 Connectivity and deployment

<Boundaries, ports, topology, protocols, and external dependencies.>

## 4 Configuration and data lifecycle

<Secrets, startup validation, migrations, persistence, backup and recovery.>

## 5 Operations and verification

<Observability, test environments, CI, security, and measurable quality checks.>

## 6 Traceability and open decisions

<Requirement coverage and unresolved technical choices or targets.>
```

## 5 Validation and maintenance

Check source readability and ensure requirements, business architecture, and
use-case documents and templates contain no tables. Check filenames, heading
hierarchy, identifier uniqueness, explicit anchors, links,
and parent references. Cross-check types, state spellings, relationship meanings,
and capability outcomes across the maps. Verify every migrated source item has a
destination or an open decision. A numbered blank heading does not define a rule.

For each populated requirement, follow its links through capabilities, information,
data, components, and technology where applicable. Check that each target exists
and supports the claimed relationship. Do not turn placeholder links into claims
of completed traceability. The methodology in this guide is self-contained.
