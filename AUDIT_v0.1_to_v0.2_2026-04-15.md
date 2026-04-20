# Universal Kit Audit — Outdated Items (v0.1 → needed v0.2)

**Date:** 2026-04-15
**Kit version on disk:** v0.1 (built 2026-04-06/07)
**Assumption:** Kit is outdated. **Confirmed: correct.**

## What's outdated or missing

### 🔴 Major gaps (framework-level changes)

1. **No L1-R (Relational Governance).** The entire relational governance layer — personality, tone, trust calibration, sycophancy, compliance tendency — doesn't exist in the kit. This is now a core PRAXIS v1.1 component. The kit has no:
   - L1-R variables in governance templates
   - Personality calibration section in SOUL_TEMPLATE
   - Trust/calibration metrics in metrics_schema.json
   - Post-survey questions about perceived AI personality

2. **No P9 (Architecture Independence).** PRAXIS v1.1 added P9: the framework works for single-model and multi-agent. The kit's ARCHITECTURE.md and README only describe multi-agent orchestration. Missing:
   - Single-model self-governance protocols
   - Self-governance templates (auto-monitoring, auto-escalation, self-validation)
   - Instructions for single-model users (Copilot, Aider, generic)

3. **No personality portability concept.** The research note from Apr 9 and H8 candidate are not reflected. The kit should include:
   - A "personality calibration" step where users test their governance config against their model
   - A simple checklist for observing model-specific behavior differences

4. **Descriptive reframe not reflected.** The kit still positions PRAXIS as "measure whether governance improves your workflow" (prescriptive). After the thesis pivot, it should position as "document what governance phenomena emerge when you instrument your AI workflow" (descriptive).

5. **Quasi-experiment design updated.** The kit was designed for a within-subjects AB design (baseline → governance). The revised quasi-experiment (Apr 11) is a 2×2 factorial via Cowork (Model × Structure). The kit needs to support:
   - 4-condition assignment (A1, A2, B1, B2)
   - Cowork-specific adapter (currently has claude_cowork.py but no Cowork session management)
   - PRAXIS-Q external evaluator instructions (not just self-rated)

### 🟡 Moderate gaps (evidence/infrastructure updates)

6. **Metrics schema outdated.** `config/metrics_schema.json` is from PRAXIS v1.0. Needs:
   - L1-R observation fields (perceived confidence, warmth, trust — per sprint)
   - Temporal scoping fields (study_period, conditions)
   - Participant ID linkage for quasi-experiment
   - PRAXIS-Q evaluator ID (for external blind evaluation)

7. **Sprint count references outdated.** README mentions "98 sprints" — now 120+. ARCHITECTURE references v1.0 evidence — should reference v1.1.

8. **No governance incident logging.** The kit has `praxis govern "rule"` for logging new rules, but no structured incident capture (what broke, what was learned, what rule resulted). The GEC cycle should be explicit:
   - `praxis incident "description"` → prompts for: what happened, root cause, new rule proposed

9. **Consent forms may need update.** The quasi-experiment redesign and L1-R study require updated consent language covering:
   - Recording AI personality/trust perceptions
   - Multiple conditions with different models
   - External evaluation of outputs

### 🟢 Minor gaps (nice to have)

10. **No CITATION.cff or Zenodo integration.** Needed for GitHub publication + DOI.

11. **No LICENSE file on disk.** ARCHITECTURE mentions CC BY-SA 4.0 but no actual LICENSE file exists.

12. **Hermes adapter still "TBD."** In the 8 days since kit was built, Hermes hasn't been researched further. Still placeholder.

13. **No CHANGELOG.** Kit has no version history tracking.

## What's still current and good

- Core architecture (within-subjects design, CLI tool, adapter system)
- Platform detection logic (11 adapters, well-structured)
- Bilingual surveys and consent forms
- Sprint protocol template
- Anonymization/export pipeline
- Python 3.8+ stdlib-only approach

## Recommendation

**The kit needs a v0.2 update before GitHub publication.** The changes are mostly additive (L1-R, P9, self-governance, incident logging) not structural. The core architecture holds.

Estimated effort: 2-3 hours to update templates, metrics schema, and README. Then Cowork can do a polish pass.

Priority order for the update:
1. Add L1-R to governance templates + metrics schema
2. Add P9 + self-governance protocols for single-model users
3. Update README + ARCHITECTURE to descriptive framing
4. Add incident logging command
5. Add CITATION.cff + LICENSE
6. Update consent forms for quasi-experiment
