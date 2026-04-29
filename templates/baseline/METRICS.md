# PRAXIS Metrics — Task Log

Welcome to the PRAXIS research study.

**Your job is simple:** use `praxis start` when you begin AI-assisted work, and `praxis stop` when you finish. Then run `praxis checkout` to calibrate the captured data.

```bash
praxis start
# ... do your AI-assisted work ...
praxis stop
praxis checkout
```

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `praxis start` | Start passive session capture |
| `praxis stop` | Stop capture and create a draft |
| `praxis checkout` | Calibrate the latest draft (task summary, quality, governance observations) |

### Manual logging (alternative)

```bash
praxis log "what you did" -d <minutes> -m <model> -q <1-5> -i <cycles> -h2 <corrections>
```

| Flag | What it means | Example |
|------|--------------|---------|
| `-d` | Duration in minutes | `-d 45` |
| `-m` | AI model/tool you used | `-m claude` or `-m copilot` |
| `-q` | Output quality, 1–5 | `-q 4` |
| `-i` | How many AI generation cycles | `-i 2` |
| `-h2` | Times you had to correct the AI | `-h2 1` |

**Example:**
```bash
praxis log "Built the login page" -d 60 -m cursor -q 4 -i 3 -h2 2
praxis log "Revised onboarding scene" -d 45 -m claude --iteration-type revision
```

---

## What counts as a "task"?

Log anything significant you did with AI assistance:
- Writing code, fixing bugs, refactoring
- Drafting content, editing, translating
- Analysis, research, summarization
- Design, planning, architecture decisions
- Playtesting, encounter tuning, narrative rewrites, visual exploration
- Any other AI-assisted work that took 10+ minutes

If you forget to log right away, that's okay — log it later with an approximate duration.

---

## Why am I doing this?

PRAXIS observes your AI workflow patterns — what tools you use, how long you work, when you intervene, and what governance moments arise. The research captures these patterns descriptively.

**Data collected:** task description, duration, model used, quality rating, governance observations, platform telemetry.
**Data NOT collected:** your file contents, conversations, project code, personal information.

Check your progress anytime:
```bash
praxis status
```

---

## Other useful commands

```bash
praxis status              # See session count, days active, averages
praxis diagnose            # See your workflow diagnosis
praxis platforms           # See which AI tools were detected
```

---

*PRAXIS observes your workflow — just work normally and calibrate with checkout.*
*This file was created by PRAXIS Universal Kit v0.9.2*
