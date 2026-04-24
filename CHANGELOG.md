# PRAXIS Universal Kit — Changelog

## v0.2.1 (2026-04-24)

### Added
- **Creative/design domain support** — project-type detection in adapters with creative template auto-selection for design-heavy Claude workflows
- **`templates/creative/CLAUDE_DESIGN_TEMPLATE.md`** — PRAXIS adaptation of the Barrunto design-critique pattern
- **Creative metrics fields** — `iteration_type`, `design_quality`, and `reviewer_feedback`
- **`DES` incident category** — structured logging for design, writing, game-design, and playtest failures

### Changed
- **README and architecture docs updated** — creative/design workflows documented alongside software workflows
- **Sprint and metrics templates updated** — examples now include playtests, revisions, and design-quality logging


## v0.2.0 (2026-04-15)

### Added
- **L1-R: Relational Governance** — personality parameters in SOUL_TEMPLATE, L1-R observation fields in metrics schema, `--l1r` flag for logging relational observations
- **P9: Architecture Independence** — self-governance template for single-model systems (Copilot, Aider, generic)
- **`praxis incident` command** — structured capture of governance emergence events (incident → root cause → new rule)
- **Personality calibration mechanism** — built into SOUL_TEMPLATE, with mismatch logging
- **Session boundary observations** — fields in metrics schema for memory/calibration recovery tracking
- **2×2 factorial experiment support** — conditions A1, A2, B1, B2 in metrics schema
- **External evaluator fields** — quality_external and quality_evaluator_id for blind PRAXIS-Q scoring
- **CITATION.cff** — for Zenodo DOI integration
- **LICENSE** — CC BY-SA 4.0
- **CHANGELOG.md** — this file

### Changed
- **README rewritten** — descriptive framing ("observe governance phenomena") replaces prescriptive ("measure whether governance improves")
- **SOUL_TEMPLATE rewritten** — now includes L1-R personality parameters and calibration notes
- **AGENTS_TEMPLATE rewritten** — now includes self-governance protocol, rule emergence log, delegation policy for single and multi-model
- **metrics_schema.json updated** — v0.2 with L1-R observations, session boundaries, governance events, external evaluator fields

### Fixed
- Sprint count references updated from 98 to 120+ where applicable
- Framework references updated from v1.0 to v1.1
- Collector, CLI, and export version constants updated from 0.1 to 0.2 to match the documented kit version.

## v0.1.0 (2026-04-07)
- Initial release
- 11 platform adapters
- CLI with status, log, activate, govern, survey, export, platforms, withdraw, init
- Bilingual surveys and consent forms (EN/ES)
- Anonymization and export pipeline
- Python 3.8+ stdlib only
