# PRAXIS Sprint Protocol

A **sprint** is the atomic unit of work in PRAXIS — a single, well-defined task
executed by an AI agent, validated, and recorded.

This guide shows you how to run PRAXIS sprints in Phase B.

---

## What is a sprint?

A sprint is any AI-assisted task that:
- Has a clear objective ("build X", "write Y", "analyze Z")
- Takes 5–120 minutes
- Produces a measurable output
- Can be validated against acceptance criteria

If a task is too large for 2 hours, decompose it into multiple sprints.

---

## The 8-Step Sprint Cycle

### Step 1: BRIEF

Before you start, write down what you want. Even a rough brief helps.

**Minimum brief:**
```
Task: [What needs to be done]
Scope: [What's in and what's out]
Model: [Which AI tool to use]
Done when: [How you'll know it's complete]
```

**Example:**
```
Task: Add email validation to the signup form
Scope: Frontend only — backend already has validation
Model: Claude Sonnet
Done when: Form shows clear error for invalid emails, passes manual test
```

### Step 2: GATE-IN

Check before executing:
- [ ] All dependencies are ready (files, APIs, context)
- [ ] Brief is clear enough to execute without guessing
- [ ] Model/tool is appropriate for this task type
- [ ] You've loaded relevant context into the AI

### Step 3: EXECUTE

Give the brief to your AI tool and let it work.
Take notes as it runs — what decisions is it making?

### Step 4: VALIDATE

Check the output against your acceptance criteria.
**Do not skip this step.** This is where quality is established.

- Does it do what the brief asked?
- Are there obvious errors?
- Does it fit the rest of your project?

### Step 5: REVIEW

Quick quality assessment (PRAXIS-Q — under 15 seconds):
1. Completeness: 1/2/3
2. Quality: 1/2/3
3. Coherence: 1/2/3
4. Efficiency: 1/2/3
5. Traceability: 1/2/3

The CLI prompts this automatically after `praxis log` in Phase B.

### Step 6: ESCALATE (if needed)

If validation fails twice in a row → **stop and reassess**, don't keep trying.

- Is the brief too vague? Rewrite it.
- Is the scope too large? Decompose it.
- Is the model wrong for this task? Try a different one.
- Is context missing? Add it.

### Step 7: RECORD

```bash
praxis log "Task description" -d <minutes> -m <model> -q <1-5> -i <cycles> -h <corrections> -l <L1-L5>
```

Always record — even partial failures. An unrecorded failure will repeat.

### Step 8: ITERATE (if needed)

If output is good but not great, log what to improve, then start a new sprint
with explicit corrections in the brief. Don't silently iterate — each iteration is its own sprint.

---

## Sprint Quick Reference

```bash
# Log a successful sprint
praxis log "Built auth module" -d 45 -m claude -q 4 -i 1 -h 0 -l L3

# Log a sprint that needed corrections
praxis log "Fixed navigation bug" -d 30 -m copilot -q 3 -i 3 -h 2 -l L3

# Log a governance-heavy sprint (rule creation, planning)
praxis log "Defined delegation policy" -d 20 -m claude -q 5 -i 1 -h 0 -l L1

# Log a governance event
praxis govern "Added rule: always test after each deploy" --type rule_created
praxis govern "Incident: API key was exposed in logs" --type incident
```

---

## PRAXIS Layers — Which one to log?

| Layer | Type of work | Examples |
|-------|-------------|---------|
| L1 | Governance | Creating rules, defining roles, incident response |
| L2 | Orchestration | Planning, decomposing tasks, delegation decisions |
| L3 | Execution | Coding, writing, design, analysis, research |
| L4 | Memory | Documenting lessons, updating knowledge base |
| L5 | Production | Final validation, delivery, quality review |

Most of your day-to-day work will be **L3**. Planning sprints are **L2**.
After an incident, log the fix as **L1**.

---

## Sprint Anti-patterns

| Anti-pattern | Why it's bad | Fix |
|-------------|-------------|-----|
| Brief-less execution | No target = no validation | Write 3 sentences before starting |
| Batch-fixing | Each fix may break something else | Test after EACH fix |
| Silent iteration | Unreported failures repeat | Log every iteration |
| Over-scoped sprints | Large scope = unpredictable output | Break into 30-60 min chunks |
| Accepting without validation | Garbage in production | Always check against criteria |
| Ignoring the escalation threshold | You waste time retrying what won't work | Stop at failure #2 |

---

## Governance Emergence

The most powerful part of PRAXIS is that **rules emerge from practice**.

When a sprint fails, ask: "What rule, if it had existed, would have prevented this?"
Then add that rule to your SOUL.md or AGENTS.md, and log the governance event:

```bash
praxis govern "Added rule: [new rule]" --type rule_created
```

Over time, your governance system becomes a record of your accumulated wisdom.

---

*PRAXIS Universal Kit v0.1 — UCM Doctoral Research*
*Framework reference: PRAXIS v1.0 (Herreros Riaza, 2026)*
