## v0.13.0 (2026-05-07) — Signal Enrichment + Heuristic Governance Detection

### New features
- **Heuristic governance detection engine:** Rule-based signal detection (Layer 1 of cross-validation stack). 9 detection rules: iteration_loop, human_override, governance_event, long_session, task_failure, active_steering, high_skepticism, quality_outcome_mismatch, high_governance_activity.
- **Delegation depth capture:** 0=direct, 1=delegated, 2=multi-hop (checkout dialog)
- **Context provision effort:** 1-5 Likert scale (checkout dialog)
- **Decision latency:** Seconds between session end and checkout (auto-computed)
- **Heuristic insights in diagnostics:** Most common governance signals reported

### Checkout dialog expanded
- Delegation depth selector (Direct / Delegated / Multi-hop)
- Context provision effort Likert (1-5)
- Window resized to accommodate new fields

### Files changed
- collector/heuristics.py — NEW: rule-based governance detection engine
- collector/praxis_collector.py — heuristic integration, delegation, context, latency
- collector/diagnostics.py — heuristic insights
- desktop/views/checkout_dialog.py — delegation, context effort fields
- config/metrics_schema.json — new fields
- ARCHITECTURE.md — heuristic docs
- install.ps1, install.sh — version bump
## v0.12.0 (2026-05-07) — Scientific Measurement Validity Fix

### Breaking changes
- utonomous field: now 
ull for passive sessions (was 	rue). Use governance_activity_score for all new analysis.
- Schema version bumped to 0.4. Old entries remain compatible.

### New features
- **Governance Activity Score (GAS):** Composite metric (0.0-1.0) replacing binary autonomy. Composed of correction_density, tag_weight, steering_proxy, skepticism_signal.
- **Steering intensity Likert:** New 1-5 scale in checkout dialog ("How much did you steer the AI?")
- **Multi-line session notes:** Checkout dialog expanded from 1-line task summary to multi-line text box
- **Operational definition of governance emergence:** Documented in ARCHITECTURE.md with observable event mapping
- **L1-R data integrity:** diagnostics.py now filters derived L1-R values from Likert aggregations

### Bug fixes
- Passive sessions no longer report utonomous: true (was measurement pollution)
- diagnostics.py no longer mixes derived and observed L1-R values in averages
- GAS computed for all checked-out and manually logged sessions

### Files changed
- collector/praxis_collector.py — GAS computation, version bump, passive/manual/checkout paths
- collector/diagnostics.py — GAS insights, L1-R filtering by l1r_source
- config/metrics_schema.json — v0.4, GAS fields, steering_intensity
- desktop/views/checkout_dialog.py — steering Likert, multi-line notes
- desktop/views/dashboard.py — GAS display replaces autonomy rate
- desktop/viewmodel.py — GAS metric mapping
- ARCHITECTURE.md — GAS docs, operational definition, L1-R integrity
- install.ps1, install.sh — version bump
# PRAXIS Universal Kit â€” Changelog

## v0.10.0 (2026-04-30) â€” Scientific Integrity Update

All 7 critical findings from the Cowork scientific foundation audit resolved.

### MUST fixes (all resolved)
- **M1: Schema v0.3** â€” enums corrected (obs/passive instead of A/B experimental), all undocumented fields formally defined (field_provenance, capture_mode, passive_capture, session_id, reviewed, governance_tag, checkout_outcome, l1r_source, provenance_completeness, notes)
- **M2: L1-R source tracking** â€” new `l1r_source` field: observed | derived | mixed | unknown. Derived L1-R values flagged as NOT psychological measurements
- **M3: Fixed `_derive_condition()` crash** â€” NameError (`entry` undefined) in manual log path. Replaced with observational condition derivation
- **M4: `autonomous` default documented** â€” schema and code now clarify that passive capture defaults to true regardless of actual autonomy
- **M5: Governance capture verified** â€” end-to-end tested: incident â†’ governance.jsonl â†’ load â†’ round-trip âœ…
- **M6: `reliability_score` renamed** â€” now `provenance_completeness` (measures capture completeness, not data quality). Legacy alias retained
- **M7: Consent forms corrected** â€” "Pseudonymization" (not "anonymization") in both EN and ES consent forms, with explanation that same participant on different machine gets different ID

### Also includes (from v0.9.5)
- Git pre-flight check (no macOS CLT popup)
- Timezone capture in state.json
- `git_unavailable` flag in git telemetry
- Dashboard warning banner when git missing

## v0.9.2 (2026-04-29)

### Added
- **Plugin adapter system** â€” drop-in custom adapters via `~/.praxis/adapters/`
- Adapters auto-discovered at runtime, no code changes needed to support new platforms

## v0.9.1 (2026-04-29)

### Added
- **Cowork/Claude bridge telemetry adapter** â€” detects Cowork bridge queue, pending/completed tasks, latest task metadata

## v0.9.0 (2026-04-28)

### Added
- **Thin platform adapters** â€” OpenClaw + Codex telemetry adapters with session counting, model detection, workspace metadata
- Adapter telemetry stored in `sessions.jsonl` alongside passive capture data

## v0.8.0 (2026-04-28)

### Changed
- **PRAXIS-Q survey removed** â€” replaced by smart contextual checkout (less friction, more reliable data)
- **Session discard** â€” users can discard passive captures that weren't real work sessions
- **Auto-fill detected data** â€” checkout pre-populates platforms, duration, and session timing from telemetry

## v0.7.2 (2026-04-28)

### Changed
- **Protocol tab and A/B phase logic removed** â€” prescriptive injection is a post-thesis product. Kit now purely observes.

## v0.7.1 (2026-04-28)

### Fixed
- Desktop build packaging for submission module

## v0.7.0 (2026-04-28)

### Changed
- **Default logging model redesigned** â€” full manual task logging is no longer the intended default path for participants.
- **Telemetry stance clarified** â€” PRAXIS now distinguishes passive capture, micro-checkout, manual logging, and reliability/provenance instead of treating all data as equally trustworthy.

### Added
- **`praxis start` / `praxis stop`** â€” passive session capture flow for low-friction telemetry.
- **`praxis checkout`** â€” 10-second human calibration step to strengthen passive drafts.
- **`sessions.jsonl`** â€” passive session timeline export.
- **Reliability scoring** â€” session/export-level confidence based on provenance richness.
- **Provenance-aware diagnosis** â€” workflow diagnosis now reflects passive-only vs calibrated evidence.

## v0.6.0 (2026-04-28)

### Changed
- **Positioning pivot** â€” PRAXIS is now framed clearly as a workflow observability kit and field instrument, not a governance solution.
- **README / README_ES rewritten** â€” the participant value proposition now leads with diagnosis, workflow mirror, and descriptive evidence.
- **Desktop copy updated** â€” dashboard and export screens now reflect baseline/structured observation language instead of governance-first language.

### Added
- **`praxis diagnose`** â€” CLI workflow diagnosis command.
- **User-facing diagnosis layer** â€” dashboard, export, and ZIP exports now include personal workflow insights.
- **Optional throttled submission flow** â€” SMTP-based delivery can be enabled with participant-level cooldowns and monthly caps.
- **`submission.json` template** â€” per-project submission config scaffold for research inbox delivery.

## v0.3.2 (2026-04-25)

### Fixed
- **macOS platform detection** â€” expanded PATH search for .app bundles (Homebrew, npm, local bins)
- **macOS Gatekeeper** â€” ad-hoc codesign in CI to prevent "corrupted" warning

## v0.3.1 (2026-04-24)

### Added
- **Desktop app (GUI)** â€” CustomTkinter + PyInstaller, Windows .exe + macOS .dmg
- **Init wizard** â€” consent + participant ID generation + project directory selection
- **Dashboard** â€” phase, days active, metrics, platform detection
- **Log Sprint** â€” visual form with model dropdown, quality slider, creative mode detection
- **Export** â€” one-click anonymized ZIP with redact option
- **PRAXIS-Q tab** â€” 5-dimension survey (Completeness, Quality, Coherence, Efficiency, Traceability)
- **Session controls** â€” Start/Stop/Initialize with status indicator
- **CI/CD** â€” GitHub Actions for Windows + macOS builds, auto-release on tag
- **Disclaimer** â€” liability limitation, unsigned binary warnings, participant autonomy

## v0.3.0 (2026-04-24)

### Changed
- **Version bumped** from 0.2 to 0.3 (desktop app release)
- **Platform detection** â€” now scans system-wide (PATH + home dirs), not just project dir
- **README** â€” install instructions for Windows/macOS, desktop app section, disclaimer

## v0.2.1 (2026-04-24)

### Added
- **Creative/design domain support** â€” project-type detection in adapters with creative template auto-selection for design-heavy Claude workflows
- **`templates/creative/CLAUDE_DESIGN_TEMPLATE.md`** â€” PRAXIS adaptation of the Barrunto design-critique pattern
- **Creative metrics fields** â€” `iteration_type`, `design_quality`, and `reviewer_feedback`
- **`DES` incident category** â€” structured logging for design, writing, game-design, and playtest failures

### Changed
- **README and architecture docs updated** â€” creative/design workflows documented alongside software workflows
- **Sprint and metrics templates updated** â€” examples now include playtests, revisions, and design-quality logging


## v0.2.0 (2026-04-15)

### Added
- **L1-R: Relational Governance** â€” personality parameters in SOUL_TEMPLATE, L1-R observation fields in metrics schema, `--l1r` flag for logging relational observations
- **P9: Architecture Independence** â€” self-governance template for single-model systems (Copilot, Aider, generic)
- **`praxis incident` command** â€” structured capture of governance emergence events (incident â†’ root cause â†’ new rule)
- **Personality calibration mechanism** â€” built into SOUL_TEMPLATE, with mismatch logging
- **Session boundary observations** â€” fields in metrics schema for memory/calibration recovery tracking
- **2Ã—2 factorial experiment support** â€” conditions A1, A2, B1, B2 in metrics schema
- **External evaluator fields** â€” quality_external and quality_evaluator_id for blind PRAXIS-Q scoring
- **CITATION.cff** â€” for Zenodo DOI integration
- **LICENSE** â€” CC BY-SA 4.0
- **CHANGELOG.md** â€” this file

### Changed
- **README rewritten** â€” descriptive framing ("observe governance phenomena") replaces prescriptive ("measure whether governance improves")
- **SOUL_TEMPLATE rewritten** â€” now includes L1-R personality parameters and calibration notes
- **AGENTS_TEMPLATE rewritten** â€” now includes self-governance protocol, rule emergence log, delegation policy for single and multi-model
- **metrics_schema.json updated** â€” v0.2 with L1-R observations, session boundaries, governance events, external evaluator fields

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


