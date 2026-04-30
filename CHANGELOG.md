# PRAXIS Universal Kit — Changelog

## v0.10.0 (2026-04-30) — Scientific Integrity Update

All 7 critical findings from the Cowork scientific foundation audit resolved.

### MUST fixes (all resolved)
- **M1: Schema v0.3** — enums corrected (obs/passive instead of A/B experimental), all undocumented fields formally defined (field_provenance, capture_mode, passive_capture, session_id, reviewed, governance_tag, checkout_outcome, l1r_source, provenance_completeness, notes)
- **M2: L1-R source tracking** — new `l1r_source` field: observed | derived | mixed | unknown. Derived L1-R values flagged as NOT psychological measurements
- **M3: Fixed `_derive_condition()` crash** — NameError (`entry` undefined) in manual log path. Replaced with observational condition derivation
- **M4: `autonomous` default documented** — schema and code now clarify that passive capture defaults to true regardless of actual autonomy
- **M5: Governance capture verified** — end-to-end tested: incident → governance.jsonl → load → round-trip ✅
- **M6: `reliability_score` renamed** — now `provenance_completeness` (measures capture completeness, not data quality). Legacy alias retained
- **M7: Consent forms corrected** — "Pseudonymization" (not "anonymization") in both EN and ES consent forms, with explanation that same participant on different machine gets different ID

### Also includes (from v0.9.5)
- Git pre-flight check (no macOS CLT popup)
- Timezone capture in state.json
- `git_unavailable` flag in git telemetry
- Dashboard warning banner when git missing

## v0.9.2 (2026-04-29)

### Added
- **Plugin adapter system** — drop-in custom adapters via `~/.praxis/adapters/`
- Adapters auto-discovered at runtime, no code changes needed to support new platforms

## v0.9.1 (2026-04-29)

### Added
- **Cowork/Claude bridge telemetry adapter** — detects Cowork bridge queue, pending/completed tasks, latest task metadata

## v0.9.0 (2026-04-28)

### Added
- **Thin platform adapters** — OpenClaw + Codex telemetry adapters with session counting, model detection, workspace metadata
- Adapter telemetry stored in `sessions.jsonl` alongside passive capture data

## v0.8.0 (2026-04-28)

### Changed
- **PRAXIS-Q survey removed** — replaced by smart contextual checkout (less friction, more reliable data)
- **Session discard** — users can discard passive captures that weren't real work sessions
- **Auto-fill detected data** — checkout pre-populates platforms, duration, and session timing from telemetry

## v0.7.2 (2026-04-28)

### Changed
- **Protocol tab and A/B phase logic removed** — prescriptive injection is a post-thesis product. Kit now purely observes.

## v0.7.1 (2026-04-28)

### Fixed
- Desktop build packaging for submission module

## v0.7.0 (2026-04-28)

### Changed
- **Default logging model redesigned** — full manual task logging is no longer the intended default path for participants.
- **Telemetry stance clarified** — PRAXIS now distinguishes passive capture, micro-checkout, manual logging, and reliability/provenance instead of treating all data as equally trustworthy.

### Added
- **`praxis start` / `praxis stop`** — passive session capture flow for low-friction telemetry.
- **`praxis checkout`** — 10-second human calibration step to strengthen passive drafts.
- **`sessions.jsonl`** — passive session timeline export.
- **Reliability scoring** — session/export-level confidence based on provenance richness.
- **Provenance-aware diagnosis** — workflow diagnosis now reflects passive-only vs calibrated evidence.

## v0.6.0 (2026-04-28)

### Changed
- **Positioning pivot** — PRAXIS is now framed clearly as a workflow observability kit and field instrument, not a governance solution.
- **README / README_ES rewritten** — the participant value proposition now leads with diagnosis, workflow mirror, and descriptive evidence.
- **Desktop copy updated** — dashboard and export screens now reflect baseline/structured observation language instead of governance-first language.

### Added
- **`praxis diagnose`** — CLI workflow diagnosis command.
- **User-facing diagnosis layer** — dashboard, export, and ZIP exports now include personal workflow insights.
- **Optional throttled submission flow** — SMTP-based delivery can be enabled with participant-level cooldowns and monthly caps.
- **`submission.json` template** — per-project submission config scaffold for research inbox delivery.

## v0.3.2 (2026-04-25)

### Fixed
- **macOS platform detection** — expanded PATH search for .app bundles (Homebrew, npm, local bins)
- **macOS Gatekeeper** — ad-hoc codesign in CI to prevent "corrupted" warning

## v0.3.1 (2026-04-24)

### Added
- **Desktop app (GUI)** — CustomTkinter + PyInstaller, Windows .exe + macOS .dmg
- **Init wizard** — consent + participant ID generation + project directory selection
- **Dashboard** — phase, days active, metrics, platform detection
- **Log Sprint** — visual form with model dropdown, quality slider, creative mode detection
- **Export** — one-click anonymized ZIP with redact option
- **PRAXIS-Q tab** — 5-dimension survey (Completeness, Quality, Coherence, Efficiency, Traceability)
- **Session controls** — Start/Stop/Initialize with status indicator
- **CI/CD** — GitHub Actions for Windows + macOS builds, auto-release on tag
- **Disclaimer** — liability limitation, unsigned binary warnings, participant autonomy

## v0.3.0 (2026-04-24)

### Changed
- **Version bumped** from 0.2 to 0.3 (desktop app release)
- **Platform detection** — now scans system-wide (PATH + home dirs), not just project dir
- **README** — install instructions for Windows/macOS, desktop app section, disclaimer

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
