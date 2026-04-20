# PRAXIS Universal Kit

**Cross-platform research tool for observing governance phenomena in AI-assisted workflows**

PRAXIS Kit instruments your AI workflow to capture what actually happens — governance emergence, personality effects, session boundaries, quality patterns — before and after introducing structured governance.

**Part of doctoral research at Universidad Complutense de Madrid.**

---

## What is PRAXIS?

PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems) is a research framework that documents what happens when humans and AI systems work together under sustained production conditions.

This kit is the **measurement instrument** — it captures data so researchers can study governance phenomena like:
- Rules that emerge organically from failures (governance emergence)
- How AI personality affects your trust and behavior (relational governance)
- What happens when you switch AI models with the same governance config (personality portability)
- How memory and calibration recover across session boundaries
- Whether workflow structure shows measurable influence on outcomes

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

**Manual (any platform with Python 3.8+):**
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
| `--l1r` | Log relational governance observations | `--l1r` (interactive prompts) |

### 4. Log governance events

When something breaks and you learn from it:
```bash
praxis incident "AI used outdated library version"
```
This prompts for: what happened, root cause, and whether a new rule should be created.

### 5. Activate structured governance (when ready)
```bash
praxis activate
```

This injects governance files into your AI tools and transitions to Phase B.

### 6. Export your data
```bash
praxis export
```

Generates an anonymized ZIP file for research analysis.

---

## What's new in v0.2

| Feature | Description |
|---------|-------------|
| **L1-R: Relational Governance** | Log perceived AI confidence, warmth, trust, and compliance tendency per sprint (`--l1r` flag) |
| **P9: Architecture Independence** | Works for single-model (Copilot, Aider) and multi-agent (OpenClaw, Cowork) setups |
| **Self-governance templates** | Protocols for single-model systems without external orchestrator |
| **Personality calibration** | Built-in mechanism to detect when AI behavior differs from governance config |
| **Incident logging** | Structured capture of governance emergence events (`praxis incident`) |
| **Session boundary observations** | Track memory recovery and calibration degradation across sessions |
| **2×2 factorial support** | Experimental conditions: Model (Sonnet/Opus) × Structure (structured/unstructured) |
| **Descriptive framing** | Kit documents phenomena rather than testing whether governance "improves" things |

---

## Commands

```
praxis status          Show phase, days active, entry count, averages
praxis log "task"      Log a task (interactive if no args given)
praxis incident "desc" Log a governance emergence event
praxis activate        Transition Phase A → Phase B (governance on)
praxis govern "rule"   Log a governance rule event (Phase B)
praxis survey pre      Launch pre-survey
praxis survey post     Launch post-survey
praxis export          Generate anonymized data ZIP for research
praxis platforms       Show detected AI platforms
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

## Research Context

This kit is part of a doctoral thesis that documents governance phenomena in AI-assisted production systems during the 2025-2027 period. The research questions:

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
  version = {0.2.0},
  year = {2026},
  publisher = {Universidad Complutense de Madrid},
  url = {https://github.com/jhriaza/praxis-universal-kit}
}
```

## License

CC BY-SA 4.0 — see [LICENSE](LICENSE)

---

*PRAXIS Universal Kit v0.2 — 2026-04-15*
*Doctoral research — Universidad Complutense de Madrid*
