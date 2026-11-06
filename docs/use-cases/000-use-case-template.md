# Use-case template

## 1 Purpose and use

Use this template to describe actor goals and business interactions before designing
service or API operations. Follow the [documentation guide](../000-docs-guide.md)
and [documentation agent instructions](../AGENTS.md). The design trail is:

Requirements → Capability → Use Case → Business Rules → Domain Objects → State
Transitions → Domain Events → Service/API Design.

Link to existing requirements, capabilities, information concepts, and value-stream
stages. Use cases elaborate their behavior; they do not replace those records or
authorize new policy. One capability may support several use cases, and one use
case may need several capabilities. A use case is not automatically one endpoint
or service.

Keep all 17 sections for each use case. Use `None` or `Not applicable` with a reason
when appropriate. Mark unknowns with an open-decision reference instead of guessing.
The placeholders and examples here are illustrative; they do not allocate IDs,
set priorities, or approve product behavior.

Keep this template and populated use cases readable as raw Markdown. Use labeled
bullets for fields, separate blocks for records, and numbered steps for flows;
do not use Markdown or HTML tables. Follow the
[source-readability conventions](../../STYLE_GUIDE.md#markdown-source-readability).

## 2 Grouped files and identifiers

Create one file per coherent domain or business area using
`NNN-<area>-use-cases.md`, for example `001-document-management-use-cases.md` or
`002-search-use-cases.md`. The sequence starts at `001` within
this directory; `000` is reserved for this template. Do not create those example
files until there are use cases to document. Preserve allocated filenames.

Use globally unique, stable IDs such as `UC-001` across all grouped files. Allocate
the next unused ID after checking the directory; IDs are independent of filenames
and heading numbers. Do not restart the UC sequence in each file or reuse retired
IDs. Add an explicit anchor such as `<a id="uc-001"></a>` before each use-case
heading. Link cross-file references to that anchor.

Start each grouped file with scope and an index. Each use case then occupies an
H2 section, with the 17 fields as H3 subsections. For the first use case these are
`3.1`–`3.17`; the next case uses `4.1`–`4.17`. Flow step numbers and local branch
labels `A1`, `E1` are separate from heading numbering and are scoped to that UC.
Use anchors such as `uc-001-a1` when a branch needs a link.

```markdown
# <Domain> use cases

## 1 Group scope

<Domain, included actor goals, exclusions, and links to source requirements,
capabilities, and relevant value streams.>

## 2 Use-case index

**[UC-001](#uc-001)**

- **Name:** <Verb Noun>
- **Primary actor:** <Actor>
- **Capability:** <CAP link>
- **Priority:** <Priority>
- **Status:** Draft

<a id="uc-001"></a>
## 3 UC-001 — <Verb Noun>

<Insert all subsections from section 3 of the template below.>

<Repeat for additional use cases, using the next heading number and an unused UC ID.>
```

## 3 Detailed use-case block

Copy this block below the first use-case heading. Replace placeholders, link
references, and adjust the heading prefix for subsequent cases. Do not copy
example behavior as a requirement without a supporting source.

```markdown
### 3.1 Use case identification

- **Use Case ID:** UC-001
- **Use Case Name:** <Short verb–noun phrase, such as Export Document.>
- **Business Capability:** <Linked CAP IDs; identify the principal capability.>
- **Source Requirements:** <Linked REQ IDs and relevant VS/STAGE IDs.>
- **Domain / Module:** <Business domain; implementation allocation if known.>
- **Priority:** <High / Medium / Low, or Not specified with an OPEN reference.>
- **Status:** Draft
- **Status Evidence:** <Review/approval reference or implementation and test evidence,
  as applicable; do not infer approval from document creation.>

### 3.2 Purpose

- **Goal:** <Observable outcome the primary actor seeks.>
- **Business Value:** <Benefit to the actor, organisation, or customer.>

### 3.3 Actors

- **Primary Actor:** <Person or external system initiating the use case.>
- **Supporting Actors:** <Other people, systems, or services participating.>

**Stakeholder: <Stakeholder>**

- **Interest in the outcome:** <Benefit, responsibility, or concern>

### 3.4 Preconditions

- <Condition that must already hold; reference the applicable rule.>
- <Required object or lifecycle state, if any.>

<Do not assume all cases require authentication or an existing account. Distinguish
assumed preconditions from checks in the flow and explain how violations are handled.>

### 3.5 Trigger

<The actor intention, external event, or time condition that begins the interaction.>

### 3.6 Main success flow

1. **Step 1**

   - **Actor:** <Initiates the business operation.>
   - **System:** <Responds with the next business interaction.>

2. **Step 2**

   - **Actor:** <Provides the required information, if applicable.>
   - **System:** <Validates against linked rules.>

3. **Step 3**

   - **Actor:** <Requests completion, if applicable.>
   - **System:** <Performs the operation and establishes its outcome.>

4. **Step 4**

   - **Actor:** —
   - **System:** <Communicates successful completion and relevant next steps.>

<Adapt these illustrative steps to the actual interaction. Describe what happens
in business terms, not controllers, implementation methods, SQL statements, or screen design.>

### 3.7 Alternative flows

**A1**

- **Branch point and condition:** <Main step and supported variation>
- **Numbered actions and system responses:**
  1. <Actor action and corresponding system response.>
  2. <Next action and response, if needed.>
- **Rejoin or termination:** <Resume at step N, or end with outcome>
- **Resulting effects:** <State, data, and side effects>

<Examples to consider only when supported: actor cancellation, optional information,
or an alternate channel. Reference defined defaults rather than inventing them.
Use None with a reason if there are no alternative flows.>

### 3.8 Exception flows

**E1**

- **Failure point and condition:** <Main step and failure>
- **Numbered actions and system responses:**
  1. <Detection, actor-facing outcome, and system response.>
  2. <Correction or recovery action, if permitted.>
- **Recovery or termination:** <Correction/retry and resume step, or final outcome>
- **Guarantees:** <What remains valid; any committed or external effects>

<Consider invalid input, unauthorized action, missing objects, wrong-state objects,
concurrent changes, and dependency failure where relevant. Missing and wrong-state
objects are distinct outcomes. Describe safe actor-facing results without leaking
technical errors. Do not add audit logging or retries unless required by a source.>

### 3.9 Postconditions

**Success Postconditions**

- <Resulting business object, state, and observable outcome.>
- <Required events or notifications, distinguishing initiation from delivery.>

**Failure Postconditions**

- <Invariants that remain true for each relevant failure.>
- <Permitted partial results and any recovery or compensation required.>

<Do not promise that nothing changed when a failure can occur after persistence
or an external side effect. Link guarantees to the relevant exception flow.>

### 3.10 Business rules

**Rule reference: <Linked REQ or BR ID>**

- **Rule summary:** <Concise statement consistent with its canonical definition>
- **Where applied:** <Main step, branch, or transition>

<Reference an existing requirement when it already defines the rule. For a distinct
shared business rule, define a globally unique BR-001-style record beside its source
requirement in 002-detailed-requirements.md, with an explicit br-001 anchor. Link
that definition from all uses; do not create conflicting copies in grouped files.>

### 3.11 Data / information requirements

**Direction: Input**

- **Information:** <Business input>
- **Constraints and source:** <Validation, sensitivity, REQ/INFO references>

**Direction: Output**

- **Information:** <Business result or identifier>
- **Constraints and source:** <Meaning, visibility, REQ/INFO references>

**Business Objects:** <Linked INFO IDs; DATA links where representations are defined.>

<Use business vocabulary. Leave storage layout and wire schemas to their owning
architecture documents. Record missing concepts as open decisions.>

### 3.12 State changes

**Business object: <INFO link>**

- **Initial state:** <Named state, or Does not yet exist for creation>
- **Resulting state:** <Named state>
- **Trigger / guard:** <Condition>
- **Flow or rule reference:** <Step and linked rule>

**Invalid Transitions:** <Source-supported prohibited transitions and expected
outcomes, or an OPEN reference where the lifecycle is not yet defined.>

<Use the states defined in the information map. Record unchanged state or no lifecycle
explicitly where appropriate. Do not infer one object's transition from a change to
another object, or prescribe new transitions solely to fit an implementation.>

### 3.13 Events

**Direction: Produced**

- **Domain event:** <Event name>
- **Business meaning and information:** <Outcome and relevant INFO references>
- **When / flow reference:** <Successful outcome / step>
- **Consumer or related use case:** <Link or Not specified>

**Direction: Consumed**

- **Domain event:** <Event name>
- **Business meaning and information:** <Input meaning>
- **When / flow reference:** <Trigger or step>
- **Consumer or related use case:** <Origin link or Not specified>

<Use None when there are no events. Link defined events and guarantees in application
architecture. Record proposed events as proposals, not implementation evidence.
Success events must describe committed changes. Specify ordering, duplication,
or delivery needs only when supported; do not imply exactly-once delivery.>

### 3.14 Non-functional requirements

**Requirement: <Linked NFR ID or established project standard>**

- **Relevance to this use case:** <Relevant security, timing, reliability, or usability constraint>
- **Acceptance evidence:** <Measure/scenario, or OPEN reference>

<Include only applicable constraints. Do not invent latency targets, audit duties,
deduplication policies, or availability guarantees. Link new requirements to 002
before treating them as accepted constraints.>

### 3.15 Acceptance criteria

**AC1**

- **Testable statement:** Given <preconditions>, when <action>, then <observable success>.
- **Flow / rule / requirement:** <Main flow and linked source>

**AC2**

- **Testable statement:** Given <condition>, when <variation or failure>, then
  <observable outcome and invariants>.
- **Flow / rule / requirement:** <A/E branch and linked source>

<Cover applicable alternatives, exceptions, state restrictions, event outcomes,
and quality constraints. AC labels are local to the UC. Link implementation tests
when available; a written criterion is not evidence that a test passed.>

### 3.16 Related use cases

**Relationship: Includes**

- **Use case:** <Linked UC ID or None>
- **Meaning and interaction point:** <Required reused behavior and invoking step>

**Relationship: Extends**

- **Use case:** <Linked base UC ID or None>
- **Meaning and interaction point:**
  <Condition under which this UC extends the base, and extension point>

**Relationship: Related**

- **Use case:** <Linked UC ID or None>
- **Meaning and interaction point:** <Association or sequence without inclusion semantics>

<Do not list a validation helper as a use case automatically. If another UC extends
this one, identify that direction explicitly. A later notification is not an extension
merely because it follows this operation.>

### 3.17 Notes / open decisions

<a id="open-uc-001-1"></a>

**OPEN-UC-001-1**

- **Question and source:** <Unresolved question and why it arose>
- **Affected flows or artifacts:** <Sections / links>
- **Decision needed:** <Business or design decision>

<Reuse an existing upstream OPEN record when it already owns the question. New
use-case-specific questions use OPEN-UC-001-1, OPEN-UC-001-2, and so on. Record
assumptions as provisional, with their source; do not silently turn them into rules.>
```

## 4 Review and completion

Use the status values `Draft`, `Reviewed`, `Approved`, and `Implemented`.
`Reviewed` records an actual review; `Approved` needs an explicit acceptance
reference; `Implemented` needs linked implementation and validation evidence.
Do not advance status merely because a template was filled in or code exists.
Unknown priorities remain explicit rather than defaulting to High.

Check every branch point and rejoin step, actor responsibility, rule reference,
state transition, and postcondition. Cover the applicable paths in acceptance
criteria. Verify numbering, globally unique UC/BR IDs, index entries, anchors,
and relative links from the nested directory. Update affected requirements and
architecture references when a use case reveals a gap; keep open decisions visible.
