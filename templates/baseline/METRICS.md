# PRAXIS Metrics — Task Log

Welcome to Phase A of the PRAXIS research study.

**Your job is simple:** after each significant AI-assisted task, run one command:

```bash
praxis log "what you did" -d <minutes> -m <model> -q <1-5> -i <cycles> -h2 <corrections>
```

---

## Quick Reference

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

This is **Phase A (Baseline)**. You're working normally, without any governance framework.
After 7+ days, you'll run `praxis activate` to start Phase B, where PRAXIS governance
is added to your AI workflow. The research measures what changes.

**Data collected:** task description, duration, model used, quality rating, iteration count, and optional creative cycle metadata such as `iteration_type`.
**Data NOT collected:** your file contents, conversations, project code, personal information.

Check your progress anytime:
```bash
praxis status
```

---

## Other useful commands

```bash
praxis status              # See how many days/entries you have
praxis survey pre          # Complete the pre-study survey (5 minutes)
praxis platforms           # See which AI tools were detected
```

---

*Phase A — no governance, natural workflow. Just log what you do.*
*This file was created by PRAXIS Universal Kit v0.2*
