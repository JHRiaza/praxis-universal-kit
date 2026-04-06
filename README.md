# PRAXIS Universal Kit

**Cross-platform research tool for AI-assisted workflow measurement**

PRAXIS Kit lets you measure your AI workflow — before and after adopting governance structure — using a simple command-line tool that works with any AI platform.

**Part of doctoral research at Universidad Complutense de Madrid.**

---

## What is PRAXIS?

PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems) is a governance framework for human-AI workflows. This kit measures whether adding governance structure changes how effectively you work with AI tools.

The research uses a **within-subjects design**: you are your own control group. First you work normally (Phase A, baseline), then you add governance (Phase B, treatment). We compare your own before/after.

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

### 3. Work normally and log your AI tasks

After each significant AI-assisted task:
```bash
praxis log "What you accomplished" -d 45 -m claude -q 4 -i 2 -h2 1
```

| Flag | Meaning | Example |
|------|---------|---------|
| `-d` | Duration in minutes | `-d 45` |
| `-m` | AI model/tool used | `-m claude` `-m copilot` `-m cursor` |
| `-q` | Quality 1-5 | `-q 4` |
| `-i` | AI generation cycles | `-i 2` (2 tries) |
| `-h2` | Human corrections | `-h2 1` (corrected once) |

### 4. After 7+ days, activate PRAXIS governance
```bash
praxis activate
```

This injects governance files into your AI tools (CLAUDE.md, .cursorrules, AGENTS.md, etc.) and starts Phase B.

### 5. Export your data at the end
```bash
praxis export
```

Send the generated ZIP file to the researcher.

---

## Commands

```
praxis status          Show phase, days active, entry count, averages
praxis log "task"      Log a task (interactive if no args given)
praxis activate        Transition Phase A → Phase B (governance on)
praxis govern "rule"   Log a governance event (Phase B)
praxis survey pre      Pre-study baseline survey
praxis survey post     Post-study survey (after Phase B)
praxis export          Generate anonymized data ZIP for researcher
praxis platforms       Show which AI tools were detected
praxis withdraw        Delete all data and withdraw from the study
```

---

## Supported AI Platforms

PRAXIS automatically detects and integrates with:

| Platform | Integration | Governance File |
|----------|------------|-----------------|
| Claude Code | Deep | CLAUDE.md |
| OpenAI Codex | Deep | AGENTS.md |
| Cursor | Deep | .cursor/rules/praxis.md |
| Windsurf | Deep | .windsurfrules |
| GitHub Copilot | Standard | .github/copilot-instructions.md |
| Aider | Standard | CONVENTIONS.md |
| Continue.dev | Standard | .continue/rules/praxis.md |
| Cline | Standard | .clinerules |
| Roo Code | Standard | .roorules |
| Any other AI tool | Generic | PRAXIS_GOVERNANCE.md |

---

## Phase A — Baseline (1-2 weeks)

Work exactly as you do today. No governance, no changes.

Log each AI-assisted task with `praxis log`. This captures your natural workflow metrics: time, quality, iterations, corrections.

Check your progress: `praxis status`

---

## Phase B — PRAXIS Governance (2+ weeks)

After running `praxis activate`:

1. Governance files are injected into your AI tools
2. Customize SOUL.md / AGENTS.md to match your work
3. Continue logging with `praxis log` (PRAXIS-Q quality rubric is added)
4. Log governance events: `praxis govern "Added rule: test after every deploy"`

---

## Privacy

- All data is stored **locally** in `.praxis/` in your project directory
- **No telemetry**, no cloud uploads, no internet required after install
- `praxis export` creates an anonymized ZIP — task descriptions can be redacted
- `praxis withdraw` deletes everything permanently at any time

What is collected:
- Task durations, quality ratings, iteration counts
- AI model names you report
- Survey responses
- Governance rules you log

What is **never** collected:
- File contents or source code
- AI conversation logs
- Personal identifiable information

---

## Requirements

- Python 3.8+
- macOS, Linux, or Windows
- No internet connection required
- No admin/root access required
- No pip dependencies — pure Python stdlib

---

## Research Context

**Title:** "Methodological Architecture for Autonomous AI-Assisted Systems"
**Researcher:** Javier Herreros Riaza
**Institution:** Universidad Complutense de Madrid — Doctoral Program CAVP
**Framework:** PRAXIS v1.0

**License:** CC BY-SA 4.0

Questions? Contact the researcher via the study information document.

---

*PRAXIS Universal Kit v0.1 — 2026*
