# PRAXIS Universal Kit

**Workflow observability kit for understanding what AI is actually doing to your work, trust, and decisions**

PRAXIS instruments real human-AI workflows so you can see patterns that usually stay invisible: rework drag, trust calibration, session-boundary degradation, personality effects, and governance rules that emerge under pressure.

**Part of doctoral research.**

---

## What do I get as a user?

PRAXIS is not just a research logger. It gives you a **workflow diagnosis**.

After you log real work, PRAXIS can show you:
- where AI is saving time versus creating rework
- when you are over-trusting persuasive outputs
- whether session resets are damaging quality or continuity
- how much human correction your workflow still requires
- which governance rules are emerging from real failures instead of theory

If you install PRAXIS, you get a **mirror for your AI workflow** — and the study gets comparable longitudinal evidence.

---

## What is PRAXIS?

PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems) is a research framework for studying what happens when humans and AI systems work together under sustained production conditions.

This repository is the **measurement instrument**. It does not assume governance improves outcomes. It captures what changes — descriptively — when structure, personality, and continuity conditions shift.

Researchers and participants can study phenomena like:
- Rules that emerge organically from failures (governance emergence)
- How AI personality affects your trust and behavior (relational governance)
- What happens when you switch AI models with the same governance config (personality portability)
- How memory and calibration recover across session boundaries
- Whether workflow structure shows measurable influence on outcomes

In short:

> **PRAXIS is a cross-platform field instrumentation kit for studying how governance emerges, degrades, and transforms inside real human-AI production workflows.**

---

## Quick Start

### 1. Install

**macOS / Linux:**
```bash
bash install.sh
```

**Windows (PowerShell):**
```powershell
.\install.ps1
```

**Manual (any platform with Python 3.10+):**
```bash
python collector/praxis_cli.py init
```

### 2. Complete the pre-survey (~10 minutes)
```bash
praxis survey pre
```

### 3. Log your AI tasks

After each significant AI-assisted task:
```bash
praxis log "What you accomplished" -d 45 -m claude -q 4 -i 2 -h2 1
```

| Flag | Meaning | Example |
|------|---------|---------|
| `-d` | Duration in minutes | `-d 45` |
| `-m` | AI model/tool used | `-m claude` `-m copilot` `-m cursor` |
| `-q` | Self-rated quality 1-5 | `-q 4` |
| `-i` | AI generation cycles | `-i 2` (2 tries) |
| `-h2` | Human corrections | `-h2 1` (corrected once) |
| `--iteration-type` | Type of cycle | `--iteration-type design_cycle` |
| `--design-quality` | Creative quality lens | `--design-quality 4,3,4,5` |
| `--reviewer-feedback` | External review summary | `--reviewer-feedback "Playtesters found pacing flat"` |
| `--l1r` | Log relational governance observations | `--l1r` (interactive prompts) |

### 4. Log governance events

When something breaks and you learn from it:
```bash
praxis incident "AI used outdated library version"
```
This prompts for: what happened, root cause, incident category (`OPS`, `GOV`, `COM`, `PRD`, `RES`, `DES`), and whether a new rule should be created.

### 5. Activate structured observation (when ready)
```bash
praxis activate
```

This introduces the structured PRAXIS condition and transitions to Phase B. Injection is an experimental mechanism, not the core value proposition.

### 6. Export your data
```bash
praxis export
```

Generates an anonymized ZIP file for research analysis, including your user-facing workflow diagnosis.

### 7. View your diagnosis
```bash
praxis diagnose
```

Shows what PRAXIS is learning about your own AI workflow.

---

## Why this is different

Most AI tooling tells you how to prompt better.
PRAXIS tells you what your workflow is actually doing over time.

| Typical AI tool | PRAXIS |
|---------|---------|
| Optimizes one interaction | Observes patterns across many sessions |
| Focuses on output only | Tracks process, trust, rework, and continuity |
| Vendor-specific | Cross-platform and architecture-aware |
| Productivity rhetoric | Descriptive evidence about real practice |
| Gives advice | Gives diagnosis |

---

## What's new in v0.6

| Feature | Description |
|---------|-------------|
| **L1-R: Relational Governance** | Log perceived AI confidence, warmth, trust, and compliance tendency per sprint (`--l1r` flag) |
| **P9: Architecture Independence** | Works for single-model (Copilot, Aider) and multi-agent (OpenClaw, Cowork) setups |
| **Self-governance templates** | Protocols for single-model systems without external orchestrator |
| **Personality calibration** | Built-in mechanism to detect when AI behavior differs from governance config |
| **Incident logging** | Structured capture of governance emergence events (`praxis incident`) |
| **Session boundary observations** | Track memory recovery and calibration degradation across sessions |
| **2×2 factorial support** | Experimental conditions: Model (Sonnet/Opus) × Structure (structured/unstructured) |
| **User-facing diagnosis** | Turns logs into a personal workflow mirror participants can actually use |
| **Submission throttling** | Optional submission flow can be rate-limited per participant to protect the research inbox |
| **Descriptive framing** | Kit documents phenomena rather than assuming governance "improves" things |

---

## Commands

```
praxis status          Show phase, days active, entry count, averages
praxis diagnose        Show your workflow diagnosis
praxis log "task"      Log a task (interactive if no args given)
praxis incident "desc" Log a governance emergence event
praxis activate        Transition Phase A → Phase B (governance on)
praxis govern "rule"   Log a governance rule event (Phase B)
praxis survey pre      Launch pre-survey
praxis survey post     Launch post-survey
praxis export          Generate anonymized data ZIP for research
praxis submit          Export and submit data when enabled
praxis platforms       Show detected AI platforms
```

### Optional: enable throttled inbox submission

PRAXIS can keep submission local-only, or it can send participant exports to the research inbox when explicitly enabled.

1. Create `.praxis/submission.json`
2. Configure your SMTP env vars: `PRAXIS_SMTP_HOST`, `PRAXIS_SMTP_PORT`, `PRAXIS_SMTP_USER`, `PRAXIS_SMTP_PASS`, `PRAXIS_SMTP_FROM`
3. Set a cooldown and monthly cap so one participant cannot flood the inbox

Example `submission.json`:

```json
{
  "enabled": true,
  "mode": "smtp",
  "email_to": "hello@javierherreros.xyz",
  "cooldown_hours": 168,
  "max_submissions_per_30d": 4
}
```

---

## Supported Platforms

| Platform | Governance File | Type |
|----------|-----------------|------|
| OpenClaw | SOUL.md + AGENTS.md + HEARTBEAT.md | Multi-agent orchestrator |
| Claude Cowork | CLAUDE.md | Multi-agent |
| Codex | AGENTS.md | Sandbox agent |
| Cursor | .cursorrules / .cursor/rules/ | AI IDE |
| Windsurf | .windsurfrules | AI IDE |
| Copilot | .github/copilot-instructions.md | AI assistant |
| Aider | .aider.conf.yml + conventions | CLI agent |
| Continue.dev | .continue/config.json | IDE extension |
| Cline | .cline/instructions.md | IDE extension |
| Roo Code | .roo/rules.md | IDE extension |
| Generic | PRAXIS_GOVERNANCE.md | Any system |

---

## Beyond Software: Creative and Design Work

PRAXIS can now instrument creative workflows alongside software work. If your project contains files such as `project.godot`, `game_design.md`, narrative docs, or design artifacts, adapters can detect it as a creative project and select design-oriented governance.

Creative support includes:
- `templates/creative/CLAUDE_DESIGN_TEMPLATE.md` for Claude/Cowork style design critique and governance
- Creative iteration types: `design_cycle`, `playtest`, `revision`, `refinement`
- Design-quality sub-metrics: clarity, tension, balance, elegance
- External reviewer tracking for playtests, editors, art direction, and design critique
- `DES` incident category for design-specific failures and governance emergence

Example logging commands:
```bash
praxis log "Reworked encounter economy" -d 55 -m claude --iteration-type design_cycle --design-quality 4,3,2,4
praxis log "Ran external narrative review" -d 40 -m codex --iteration-type revision --reviewer-feedback "Readers found Act 2 unclear" --reviewer-source editor
praxis incident "Tutorial wording obscured the core loop" --category DES
```

---

## Research Context

This kit is part of a doctoral thesis that documents governance phenomena in AI-assisted production systems. The research questions:

1. What governance phenomena emerge when AI systems operate under structured instrumentation?
2. How does AI personality (tone, confidence, warmth) affect user trust and behavior?
3. Does workflow structure show measurable influence on outcomes independent of model capability?
4. What do current AI governance frameworks (EU AI Act, OECD, NIST) fail to cover?

**Important disclosures:**
- Quality assessments in Phase A are self-rated by the participant
- External blind evaluation (PRAXIS-Q) is available for Phase B outputs
- All data is anonymized and stored locally — nothing is sent to any server automatically
- Participants can withdraw at any time

---

## Citing this work

```bibtex
@software{herreros2026praxis,
  author = {Herreros Riaza, Javier},
  title = {PRAXIS Universal Kit},
  version = {0.3.2},
  year = {2026},
  publisher = {Javier Herreros Riaza},
  url = {https://github.com/JHRiaza/praxis-universal-kit}
}
```

## License

CC BY-SA 4.0 — see [LICENSE](LICENSE)

## Desktop App (GUI)

PRAXIS Kit also ships with a desktop GUI built with CustomTkinter. It provides the same functionality as the CLI through a visual interface with forms, sliders, and buttons — ideal for researchers who prefer not to use the terminal.

### Download

Download the latest release for your platform:

| Platform | File | Architecture |
|----------|------|-------------|
| **Windows** | `praxis-desktop.exe` | x64 |
| **macOS** | `PRAXIS-Kit-macOS-arm64.dmg` | Apple Silicon (M1/M2/M3/M4) |

👉 **[Download from GitHub Releases](https://github.com/JHRiaza/praxis-universal-kit/releases/latest)**

No Python installation required — the binaries are self-contained.

### Installation

**Windows:**
1. Download `praxis-desktop.exe`
2. You may see a **"Windows protected your PC"** SmartScreen warning — this is normal for unsigned apps
3. Click **"More info"** → **"Run anyway"**
4. The app launches directly — no installer needed

**macOS:**
1. Download and open `PRAXIS-Kit-macOS-arm64.dmg`
2. Drag **PRAXIS Kit** to your Applications folder
3. On first launch, macOS will block it ("cannot be verified")
4. Go to **System Settings → Privacy & Security** → scroll down → click **"Open Anyway"**
5. Alternatively, right-click (or Control-click) the app → **Open** → confirm
6. Or run in Terminal: `xattr -cr /Applications/PRAXIS\ Kit.app`

### Run from source (any platform)

```bash
pip install customtkinter
python desktop/app.py
```

### Features

- **Init Wizard** — First-run setup: consent + participant ID generation
- **Dashboard** — Live status view plus a user-facing workflow diagnosis
- **Log Sprint** — Visual form with dropdowns, sliders, and number inputs
- **Export & Submit** — ZIP generation, diagnosis review, and optional inbox submission
- **PRAXIS-Q Survey** — 5-dimension quality rubric (Phase B)
- **Session Controls** — Start/Stop/Initialize buttons with status indicator
- **Platform Detection** — Auto-detects installed AI tools from system
- **Creative mode** — Automatically detects creative projects (Godot, game design) and shows extra design quality sub-metrics

### Build standalone .exe

```bash
pip install customtkinter pyinstaller
desktop\build_exe.bat
```

Produces `dist/praxis-desktop.exe` — a single-file Windows executable with no Python installation required.

### Architecture

The desktop app imports `praxis_collector` directly (no subprocess, no CLI parsing). Both the CLI and the GUI can be used interchangeably on the same `.praxis/` directory.

```
desktop/
├── app.py              # Main entry point
├── viewmodel.py        # Controller layer (bridges views ↔ collector)
├── views/
│   ├── init_wizard.py  # First-run setup
│   ├── dashboard.py    # Status overview
│   ├── log_sprint.py   # Sprint logging form
│   └── export.py       # ZIP export
├── build.spec          # PyInstaller spec
├── build_exe.bat       # Windows build script
└── requirements.txt    # customtkinter
```

---

## Disclaimer & Limitation of Liability

PRAXIS Universal Kit is a **research instrument** developed as part of doctoral work. It is provided **"as is"** without warranty of any kind, express or implied.

- **No guarantee of fitness** for any particular purpose. The kit is designed for academic research and may contain bugs or unexpected behavior.
- **Data is stored locally** on your machine. The developers are not responsible for any data loss, corruption, or unintended exposure.
- **No automatic transmission by default.** Data stays local unless the participant explicitly enables submission. Optional SMTP submission can be rate-limited per participant.
- **Unsigned binaries.** The Windows and macOS desktop apps are not code-signed with developer certificates. Your operating system may display security warnings (see installation instructions above).
- **Research use only.** This tool is not intended for production environments, critical workflows, or commercial deployment.
- **Participant autonomy.** All data collection requires explicit consent. Participants can withdraw at any time and request deletion of their data.

By using PRAXIS Universal Kit, you acknowledge that the authors shall not be held liable for any damages arising from its use.

---

*PRAXIS Universal Kit v0.6.0 — 2026-04-28*
*Doctoral research — Javier Herreros Riaza*
