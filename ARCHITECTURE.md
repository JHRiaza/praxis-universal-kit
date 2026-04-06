# PRAXIS Universal Kit — Architecture Spec
## Version 0.1 — 2026-04-06

### Purpose
Cross-platform, platform-agnostic PRAXIS research package that enables within-subjects quasi-experimental comparison of AI-assisted workflows BEFORE and AFTER PRAXIS governance adoption. Designed for distribution to external participants (Claude Cowork, Codex, OpenClaw, Cursor, Copilot, Hermes, Aider, Continue.dev, Cline, Roo Code, etc.).

### Research Design
- **Type:** Within-subjects quasi-experiment (ABA' possible, AB minimum)
- **Phase A (Baseline):** 1-2 weeks. Metrics collector active. NO governance injection. User works naturally.
- **Phase B (Treatment):** 2+ weeks. PRAXIS governance activated via `praxis activate`. Same metrics continue. PRAXIS-Q rubric added per sprint.
- **Comparison:** Same user, same projects, same tools. Delta on autonomy, iterations, intervention frequency, quality, governance emergence.

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
├── config/
│   ├── platforms.json            # Platform detection signatures
│   └── metrics_schema.json       # Sprint metrics JSON schema (from PRAXIS v1.0)
├── collector/
│   ├── praxis_collector.py       # Metrics collector daemon (Python 3.8+)
│   ├── requirements.txt          # Minimal deps (none if possible, stdlib only)
│   └── praxis_cli.py             # CLI: praxis status|activate|export|log
├── surveys/
│   ├── pre_survey.json           # Pre-PRAXIS baseline survey (JSON, 23 items)
│   ├── post_survey.json          # Post-PRAXIS survey (JSON, 15+10 items)
│   └── praxis_q.json             # Per-sprint PRAXIS-Q rubric (3-point, <15sec)
├── templates/
│   ├── baseline/                 # Phase A workspace files (minimal, no governance)
│   │   ├── METRICS.md            # "Log your tasks here" — lightweight prompt
│   │   └── .praxis/
│   │       ├── state.json        # Kit state (phase, install date, participant ID)
│   │       └── metrics.jsonl     # Collected sprint metrics (JSONL)
│   └── governance/               # Phase B files (injected on `praxis activate`)
│       ├── SOUL_TEMPLATE.md      # PRAXIS governance personality template
│       ├── AGENTS_TEMPLATE.md    # PRAXIS operational procedures template
│       ├── MEMORY_TEMPLATE.md    # PRAXIS memory protocol template
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
| Hermes | TBD (research needed) | TBD | Need to identify config mechanism |
| Generic | Fallback | `PRAXIS_GOVERNANCE.md` | Plain markdown, works anywhere |

### Metrics Collection (Both Phases)

#### Automatic (passive)
- Sprint start/end timestamps (from `.praxis/metrics.jsonl`)
- File change frequency (git diff stats if git repo)
- Session count per day

#### Semi-automatic (user prompted)
After each significant task, the CLI prompts (or user runs `praxis log`):
```
praxis log "Built auth system" --duration 45 --model sonnet --quality 4 --iterations 2 --interventions 1
```

Shorthand: `praxis log "task" -d 45 -m sonnet -q 4 -i 2 -h 1`

Fields:
- task: description (string)
- duration: minutes (int)
- model: AI model used (string, free text)
- quality: self-rated 1-5 (int)
- iterations: how many AI generation cycles (int)
- interventions: human corrections/overrides (int)
- autonomous: did AI complete without human help? (bool, derived: interventions==0)
- layer: PRAXIS layer (L1-L5, Phase B only)
- praxis_q: PRAXIS-Q score (Phase B only, prompted if phase==B)

#### Phase B additions
- PRAXIS-Q rubric (3-point scale per dimension, <15 seconds)
- Governance events (new rules created, rules modified, incidents)
- `praxis govern "Added rule: always test after deploy"` — logs governance emergence

### CLI Commands

```bash
praxis status          # Show current phase, days active, metrics count
praxis log "task"      # Log a sprint/task with metrics
praxis activate        # Transition from Phase A → Phase B (irreversible)
praxis govern "rule"   # Log a governance event (Phase B)
praxis survey pre      # Launch pre-survey (Phase A, first run)
praxis survey post     # Launch post-survey (after Phase B)
praxis export          # Generate anonymized data ZIP for research
praxis platforms       # Show detected AI platforms
```

### Phase Transition: `praxis activate`

When user runs `praxis activate`:
1. Confirm Phase A has ≥7 days of data (warn if less, allow override)
2. Present consent reminder
3. For each detected platform, inject governance files via adapter:
   - Copy SOUL_TEMPLATE → platform's governance file location
   - Copy AGENTS_TEMPLATE → platform's operational file location
   - Prompt user to customize (name, role, principles)
4. Enable PRAXIS-Q prompts after each `praxis log`
5. Enable governance event logging
6. Update `.praxis/state.json`: phase="B", activated_at=now
7. Print "PRAXIS activated. Your AI systems now have governance structure."

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

**Tier 4 — Generic (any system)**
- Plain PRAXIS_GOVERNANCE.md in project root
- Full manual CLI logging
- Works with ANY AI tool, even ChatGPT web
