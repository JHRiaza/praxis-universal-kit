# PRAXIS Universal Kit — Architecture Spec
## Version 0.9.2 — 2026-04-29

### Purpose
Cross-platform, platform-agnostic research package for observing and documenting governance phenomena in AI-assisted workflows. Designed for distribution to external participants using any AI platform (Claude Cowork, Codex, OpenClaw, Cursor, Copilot, Aider, Continue.dev, Cline, Roo Code, etc.).

The kit instruments workflows to capture what happens — governance emergence, relational governance effects, personality portability, session boundary behavior — before and after introducing structured governance. It supports both software production and creative/design workflows such as game design, writing, and narrative iteration.

### Current Status
- **Latest release:** v0.9.2 (2026-04-29)
- **Active development:** plugin adapter system for custom AI platform integrations
- **Pre-admission testing:** single-participant pilot ongoing (n=1, real production data)
- **Code signing:** pending post-admission (Azure Trusted Signing + Apple Developer)
- **Study deployment:** targeted for post-PhD admission (Oct-Nov 2026)

### Research Design
- **Type:** Observational field study — descriptive, not prescriptive
- **Data collection:** Passive capture + smart checkout + manual logging (three tiers, provenance-tagged)
- **Reliability scoring:** Each data point tagged with confidence level based on capture method (passive=0.45, checkout=1.0, manual=0.8)
- **2×2 Factorial (schema-ready):** Conditions A1, A2, B1, B2 in metrics schema for future controlled study design
- **Observation targets:** Governance emergence, trust calibration, session boundary behavior, rework patterns, model/workflow correlation

### P9: Architecture Independence
The kit works for both single-model and multi-agent setups:

| Architecture | Example | Governance mechanism |
|-------------|---------|---------------------|
| Single-model | Copilot, Aider, Cursor | Self-governance protocols (SELF_GOVERNANCE_TEMPLATE.md) |
| Multi-agent | OpenClaw, Cowork | External orchestrator + governance files (SOUL + AGENTS) |
| Hybrid | Cursor + Claude review | Mixed: self-governance for execution, orchestrator for review |

Single-model users receive self-governance templates that encode monitoring, escalation, validation, and calibration protocols directly into the model's configuration file.

### Known Limitation: OpenClaw to Cowork Bridge
OpenClaw and Claude Cowork are detected as separate platform targets. The kit can inject governance files into each environment independently, but it does not yet provide an automatic bridge that transfers runtime state, memory summaries, heartbeat outputs, task queues, or escalation context from OpenClaw into Cowork.

For studies that use both systems, researchers should treat OpenClaw-to-Cowork handoff as a manual boundary. Log the handoff as a session boundary observation and include any bridge failure, missing context, or manual rehydration work as a governance event or incident when it affects task outcome.

### Directory Structure
```
praxis-kit/
├── install.sh                    # Unix installer (macOS/Linux)
├── install.ps1                   # Windows installer (PowerShell)
├── README.md                     # Quick start guide (EN)
├── README_ES.md                  # Quick start guide (ES)
├── CONSENT.md                    # Research consent form (EN)
├── CONSENTIMIENTO.md             # Research consent form (ES)
├── LICENSE                       # CC BY-SA 4.0
├── CHANGELOG.md                  # Version history
├── CITATION.cff                  # Citation metadata (Zenodo/DOI)
├── config/
│   ├── platforms.json            # Platform detection signatures
│   └── metrics_schema.json       # Sprint metrics JSON schema (v0.2, L1-R + factorial)
├── collector/
│   ├── praxis_collector.py       # Metrics collector (Python 3.8+)
│   ├── requirements.txt          # Minimal deps (none — stdlib only)
│   └── praxis_cli.py             # CLI: status|log|incident|activate|govern|survey|export|platforms
├── surveys/
│   ├── pre_survey.json           # Pre-PRAXIS baseline survey (JSON, 23 items)
│   ├── post_survey.json          # Post-PRAXIS survey (JSON, 15+10 items)
│   └── praxis_q.json             # Per-sprint PRAXIS-Q rubric (3-point, <15sec)
├── templates/
│   ├── baseline/                 # Workspace files (minimal, no governance)
│   │   ├── METRICS.md            # "Log your tasks here" — lightweight prompt
│   │   └── .praxis/
│   │       ├── state.json        # Kit state (session data, participant ID)
│   │       └── metrics.jsonl     # Collected sprint metrics (JSONL)
│   ├── creative/                 # Domain-specific creative/design templates
│   │   └── CLAUDE_DESIGN_TEMPLATE.md  # Creative critique + governance template
│   └── governance/               # Governance files (injected on `praxis activate`)
│       ├── SOUL_TEMPLATE.md      # Governance personality + L1-R parameters
│       ├── AGENTS_TEMPLATE.md    # Operational procedures + self-governance protocol
│       ├── SELF_GOVERNANCE_TEMPLATE.md  # Single-model self-governance protocols (v0.2)
│       ├── MEMORY_TEMPLATE.md    # Memory protocol template
│       └── SPRINT_PROTOCOL.md    # How to run PRAXIS sprints
├── adapters/                     # Platform-specific integration adapters
│   ├── openclaw.py               # OpenClaw: workspace files + cron + heartbeat
│   ├── claude_cowork.py          # Claude Cowork: CLAUDE.md / project rules
│   ├── codex.py                  # Codex: AGENTS.md in sandbox
│   ├── cursor.py                 # Cursor: .cursorrules / .cursor/rules
│   ├── copilot.py                # Copilot: .github/copilot-instructions.md
│   ├── aider.py                  # Aider: .aider.conf.yml + conventions
│   ├── continue_dev.py           # Continue.dev: .continue/config.json
│   ├── cline.py                  # Cline: .cline/instructions.md
│   ├── roo_code.py               # Roo Code: .roo/rules.md
│   ├── windsurf.py               # Windsurf: .windsurfrules
│   └── generic.py                # Fallback: plain markdown files
└── export/
    └── anonymize.py              # Strip PII, generate participant ID, export ZIP
```

### Platform Detection Logic
Each adapter checks for platform-specific signals:

| Platform | Detection Signal | Governance File | Notes |
|----------|-----------------|-----------------|-------|
| OpenClaw | `~/.openclaw/` dir OR `openclaw` in PATH | SOUL.md + AGENTS.md + HEARTBEAT.md | Deepest integration (cron, heartbeat, memory) |
| Claude Cowork | `CLAUDE.md` in project root OR `~/.claude/` | CLAUDE.md | Anthropic's project instructions file |
| Codex | `codex` CLI in PATH or `.codex/` dir | AGENTS.md | OpenAI sandbox agent |
| Cursor | `.cursor/` dir OR `cursor` in PATH | `.cursorrules` or `.cursor/rules/*.md` | AI IDE |
| Windsurf | `.windsurf/` dir | `.windsurfrules` | Codeium AI IDE |
| Copilot | `.github/copilot-instructions.md` exists | `.github/copilot-instructions.md` | GitHub Copilot |
| Aider | `.aider.conf.yml` OR `aider` in PATH | `.aider.conf.yml` + `CONVENTIONS.md` | CLI coding agent |
| Continue.dev | `.continue/` dir | `.continue/config.json` | VSCode/JetBrains extension |
| Cline | `.cline/` dir | `.cline/instructions.md` | VSCode extension |
| Roo Code | `.roo/` dir | `.roo/rules.md` | VSCode extension |
| Generic | Fallback | `PRAXIS_GOVERNANCE.md` | Plain markdown, works anywhere |

### Metrics Collection

#### Passive capture (automatic)
- Session start/end timestamps (from `.praxis/sessions.jsonl`)
- Platform detection (OpenClaw, Codex, Cowork bridge)
- Adapter telemetry (session counts, model info, workspace metadata)
- Duration tracking

#### Smart checkout (user calibrated)
After passive capture stops, the user runs `praxis checkout`:
- 1-line task summary
- Quality self-rating (1-5)
- Outcome (solved / partially / abandoned)
- Governance moment (context loss, AI off track, scope creep, etc.)
- L1-R trust observations
- Provenance tag: `smart_checkout` with reliability 1.0

#### Manual logging (power users)
```praxis log "Built auth system" --duration 45 --model sonnet --quality 4 --iterations 2 --interventions 1```

Fields:
- task: description (string)
- duration: minutes (int)
- model: AI model used (string, free text)
- quality: self-rated 1-5 (int)
- iterations: how many AI generation cycles (int)
- interventions: human corrections/overrides (int) — flag: `-h2`
- autonomous: did AI complete without human help? (bool, derived: interventions==0)
- iteration_type: software or creative cycle subtype (`implementation`, `design_cycle`, `playtest`, etc.)
- design_quality: optional clarity/tension/balance/elegance scores for creative work
- reviewer_feedback: optional external feedback object for playtests, editors, and reviewers
- governance_tag: checkout governance moment category
- checkout_outcome: solved / partially / abandoned

#### L1-R observations (v0.2)
When using the `--l1r` flag, the CLI prompts for relational governance observations:
- Perceived confidence (Likert 1-7): How confident did the AI seem?
- Perceived warmth (Likert 1-7): How warm/supportive did the AI feel?
- Trust willingness (Likert 1-7): Would you follow the AI's advice without verifying?
- Skepticism activation (Likert 1-7): Did you feel the need to verify independently?
- Perceived authority (Likert 1-7): How expert did the AI seem?
- Compliance tendency (boolean): Did you accept the AI's output without questioning?
- Personality mismatch (boolean + notes): Did the AI's behavior differ from SOUL_TEMPLATE settings?

These observations capture the relational governance layer — how the AI's personality affects user trust and behavior.

#### Governance events
- Governance events (new rules created, rules modified, incidents)
- `praxis govern "Added rule: always test after deploy"` — logs governance emergence
- `praxis incident "description"` — structured incident capture with root cause analysis and categories (`OPS`, `GOV`, `COM`, `PRD`, `RES`, `DES`)

#### Session boundary observations (v0.2)
When a session starts after a break, the schema captures:
- Memory recovery: instant / partial / lost
- Calibration recovery: immediate / gradual / significant_degradation

### CLI Commands

```bash
praxis status          # Show session count, days active, averages
praxis start           # Start passive session capture
praxis stop            # Stop passive capture, create draft entry
praxis checkout        # Calibrate latest passive draft (outcome, quality, governance tag)
praxis log "task"      # Log a sprint/task with metrics
praxis incident "desc" # Log a governance emergence incident (structured)
praxis activate        # Activate structured observation mode
praxis govern "rule"   # Log a governance event
praxis survey pre      # Launch pre-survey
praxis survey post     # Launch post-survey
praxis export          # Generate anonymized data ZIP for research
praxis diagnose        # Show workflow diagnosis
praxis platforms       # Show detected AI platforms
```

### `praxis activate`

When user runs `praxis activate`:
1. Present consent reminder
2. For each detected platform, inject governance files via adapter:
   - Detect whether the project is software or creative/design based on workspace files
   - Copy SOUL_TEMPLATE / AGENTS_TEMPLATE or a domain-specific template to the platform's governance location
   - For single-model platforms, also inject SELF_GOVERNANCE_TEMPLATE
   - Prompt user to customize (name, role, principles, L1-R parameters)
3. Enable governance event logging
4. Update `.praxis/state.json`
5. Print "PRAXIS activated."

### Incident Logging (v0.2)

`praxis incident "description"` provides structured capture of governance emergence:
1. Prompts: What happened? Root cause? Incident category? Should a new rule be created?
2. Logs the incident as a governance event with type `incident` and optional category metadata
3. If a rule is proposed, user can integrate it via `praxis govern`

This captures the **Governance Emergence Cycle (GEC)**: incident → analysis → rule → integration.

### Surveys

All surveys stored as JSON with question schema:
```json
{
  "id": "A1",
  "section": "demographics",
  "type": "single_choice|multi_choice|likert_5|likert_7|open_text|numeric",
  "text_en": "...",
  "text_es": "...",
  "options_en": [...],
  "options_es": [...],
  "required": true
}
```

Surveys rendered in terminal (interactive CLI) or exportable as web form URL.

### Data Privacy & Ethics
- All data stored locally in `.praxis/` directory
- No telemetry, no cloud upload, no phoning home
- `praxis export` creates anonymized ZIP:
  - Participant ID = `PRAXIS-P###` (sequential, assigned at install)
  - Task descriptions optionally redacted (user choice)
  - No file contents, no conversation logs, no project data
  - Only: metrics, surveys, governance events, timestamps
- Consent form must be accepted during install (stored in state.json)
- Participant can withdraw: `praxis withdraw` → deletes all collected data

### Technical Requirements
- Python 3.8+ (only stdlib — no pip dependencies)
- Works offline (no internet required after install)
- Cross-platform: macOS, Linux, Windows (PowerShell 5.1+)
- No admin/root required
- ~50KB total install size (excluding Python itself)

### Integration Depth Tiers

**Tier 1 — Deep (OpenClaw)**
- Auto-creates cron jobs for metric reminders
- Heartbeat integration for passive data collection
- Memory system maps directly to L4
- Agent spawning = L2/L3 evidence

**Tier 2 — Medium (Claude Cowork, Codex, Cursor, Windsurf)**
- Governance files map to native config format
- User manually logs metrics via CLI
- Git integration for change frequency

**Tier 3 — Light (Aider, Continue, Cline, Roo Code, Copilot)**
- Governance files injected into platform's convention file
- All metrics via manual CLI logging
- Minimal platform hooks
- Self-governance template injected for single-model platforms

**Tier 4 — Generic (any system)**
- Plain PRAXIS_GOVERNANCE.md in project root
- Full manual CLI logging
- Works with ANY AI tool, even ChatGPT web

### PRAXIS Layers

| Layer | Name | Scope |
|-------|------|-------|
| L1 | Governance | Rules, principles, identity, incident response |
| L1-R | Relational Governance | Personality parameters, trust calibration, compliance tendency (v0.2) |
| L2 | Orchestration | Task planning, decomposition, delegation |
| L3 | Execution | Coding, writing, design, analysis |
| L4 | Memory | Knowledge persistence, episodic/semantic/hardened facts |
| L5 | Production | Final validation, delivery, quality review |

### Experimental Conditions (2×2 factorial, schema-ready)

| Condition | Model | Structure | Description |
|-----------|-------|-----------|-------------|
| A1 | Sonnet-class | Unstructured | Lower-capability model, no governance |
| A2 | Opus-class | Unstructured | Higher-capability model, no governance |
| B1 | Sonnet-class | PRAXIS-lite | Lower-capability model, governance active |
| B2 | Opus-class | PRAXIS-lite | Higher-capability model, governance active |

This design separates model capability effects from governance structure effects. The `condition` field in metrics_schema.json tracks which condition each sprint belongs to. Conditions are schema-ready for future controlled study deployment.

### Framework Version
- **Kit version:** 0.9.2
- **Schema version:** 0.2
- **PRAXIS framework:** v1.1 (includes L1-R, P9)
- **License:** CC BY-SA 4.0
