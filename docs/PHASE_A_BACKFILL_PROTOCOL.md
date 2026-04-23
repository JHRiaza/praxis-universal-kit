# Phase A Backfill Protocol
## Retroactive Baseline Reconstruction

### Purpose
This protocol defines how to reconstruct Phase A baseline evidence when a participant began using AI-assisted workflows before installing PRAXIS Universal Kit instrumentation.

Backfilled Phase A data is useful for contextual analysis, but it is weaker than prospectively collected data. It must be labeled, separated from live metrics where possible, and treated as reconstructed evidence rather than native telemetry.

### Scope
Use this protocol when:
- A participant has meaningful pre-PRAXIS workflow history.
- The original Phase A period was not instrumented by the kit.
- The researcher needs a baseline comparison before Phase B governance activation.

Do not use this protocol to overwrite prospectively collected Phase A data.

### Anonymized Project Mapping
Replace every real project, product, client, repository, person, or organization name with stable generic identifiers:

| Identifier | Meaning |
|------------|---------|
| Project A | First reconstructed project or workflow stream |
| Project B | Second reconstructed project or workflow stream |
| Project C | Third reconstructed project or workflow stream |
| Tool A | First AI platform or agent environment |
| Tool B | Second AI platform or agent environment |
| Participant A | Primary participant |
| Reviewer A | External reviewer or evaluator |

Use the same identifier consistently throughout the backfill. Store any real-name mapping outside the PRAXIS export package.

### Evidence Sources
Prefer sources that already exist as operational artifacts:
- Git commit history, issue trackers, pull requests, and release notes.
- Local task logs, sprint notes, or daily work summaries.
- Terminal history or command logs when privacy review permits.
- Calendar entries or timestamped planning notes.
- Existing AI task summaries, excluding raw private conversations unless explicitly consented.

Exclude private content that is not necessary for baseline reconstruction.

### Minimum Backfill Record
Each reconstructed entry should include:
- `phase`: `A`
- `backfilled`: `true`
- `backfill_confidence`: `high`, `medium`, or `low`
- `source_type`: evidence category used for reconstruction
- `timestamp` or bounded date range
- anonymized project identifier
- task summary
- estimated duration in minutes
- AI tool or model label, anonymized if needed
- quality estimate, with evaluator source noted
- iterations estimate
- human intervention estimate
- notes on uncertainty

### Confidence Rules
Use `high` only when timestamps, task boundaries, and outcome evidence are independently visible.

Use `medium` when the task and outcome are clear but duration, iterations, or intervention count must be estimated.

Use `low` when the entry is reconstructed primarily from memory or sparse notes. Low-confidence entries may support qualitative context but should not drive quantitative claims.

### Procedure
1. Define the intended Phase A window before reviewing individual evidence.
2. Inventory available evidence sources without adding project names to the working export.
3. Assign anonymized identifiers such as Project A and Tool A.
4. Reconstruct entries in chronological order.
5. Mark every reconstructed entry with `backfilled: true`.
6. Record confidence and uncertainty for every entry.
7. Keep reconstructed entries separate from native telemetry during analysis.
8. Run an anonymization audit before export.

### Analysis Constraints
Backfilled data may be used for:
- qualitative baseline description
- rough pre/post comparison
- identifying governance emergence patterns
- session boundary and handoff analysis

Backfilled data should not be used as equivalent to live Phase A telemetry without a limitation note.

### Required Limitation Note
Any report using this data must state:

> Phase A includes retroactively reconstructed baseline records. These records were backfilled from operational artifacts and are not equivalent to prospectively collected telemetry.

### Anonymization Audit
Before sharing or exporting, search the backfill document and derived files for real names, repository names, client names, product names, and private identifiers. Replace every occurrence with the stable anonymized identifiers defined above.