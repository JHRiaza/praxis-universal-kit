# AGENTS_TEMPLATE.md — Operational Procedures

> This file defines HOW your AI system operates. Rules, procedures, quality gates.
> Part of PRAXIS Universal Kit v0.2. Customize everything below.

## Operational Rules

[Add rules specific to your workflow. Start minimal — rules will emerge from practice.]

### Current Rules

| # | Rule | Origin | Since |
|---|------|--------|-------|
| 1 | Test after EACH fix, never batch-fix | [Preset] | Day 1 |
| 2 | Research first if technology is <6 months old | [Preset] | Day 1 |
| 3 | 2 consecutive failures → stop and ask the human | [Preset] | Day 1 |
| 4 | Never present unverified information as fact | [Preset] | Day 1 |

### Rule Emergence Log

Use `praxis incident "description"` to log new governance events. Each entry captures:
- What happened (the incident)
- Root cause analysis
- New rule proposed
- Rule integrated: Y/N

---

## Quality Gates

### Pre-delivery checklist
- [ ] Output meets all requirements from the brief
- [ ] Output is technically correct (verified, not assumed)
- [ ] Output is internally consistent
- [ ] Output can be traced (how and why it was produced is documented)
- [ ] Uncertainties are explicitly flagged

### Self-governance protocol (for single-model setups)

If you're using a single AI model without an external orchestrator, the model must self-govern:

1. **Self-monitor:** Periodically check if rules are accumulating beyond budget
2. **Self-escalate:** If confidence is low or 2 attempts fail, stop and ask the human
3. **Self-validate:** After producing output, list assumptions made and identify the weakest point
4. **Self-calibrate:** Express uncertainty when uncertain. Don't project more confidence than warranted.

---

## Delegation Policy

[For multi-model setups. Define which tasks go to which model/tier.]

| Task Type | Delegate To | Why |
|-----------|------------|-----|
| Research / search | [e.g., Cheaper model or web search] | No need for top-tier |
| Code writing | [e.g., Primary coding model] | Needs code competence |
| Review / decisions | [e.g., Most capable model OR human] | High-stakes |
| Creative work | [e.g., Capable model with creative instructions] | Needs judgment |
| Final validation | [e.g., Human] | Irreversible |

**For single-model setups:** The model handles all task types. Use the quality gates above instead of delegation.

---

## Memory Protocol

### Daily logging
- Log significant tasks with `praxis log`
- Note what worked, what broke, what was learned
- Store in daily memory file if your platform supports it

### Weekly review
- Check rule budget: are we over limit?
- Prune stale rules (not applied in 30+ days)
- Review governance emergence log: any patterns?

### Hardened facts
[Separate verified knowledge from inferred knowledge. Mark facts that should NEVER change.]

| Fact | Source | Verified |
|------|--------|----------|
| [e.g., "API endpoint is /v2/xxx"] | [Documentation] | ✅ |
| [e.g., "Client prefers dark theme"] | [Direct communication] | ✅ |

---

*This template is part of PRAXIS Universal Kit v0.2.*
*PRAXIS (Protocol for Rule Architecture in eXtended Intelligent Systems)*
*Doctoral research — Universidad Complutense de Madrid*
