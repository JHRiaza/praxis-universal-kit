# PRAXIS Kit v1.0 — Formal Definition & Roadmap

**Created:** 2026-04-29
**Source:** Recovered from Apr 28 Discord #phd conversation (lost during context compaction, recovered via message search)
**Status:** Agreed by Javier

---

## v1.0 Definition

**PRAXIS Kit v1.0 = Local Observer Model (auto-classification)**

A tiny (1-3B parameter) quantized model that watches adapter telemetry and auto-classifies governance events during AI-assisted work sessions. The human only validates when the model is uncertain. Most sessions require zero human input beyond passive capture.

---

## What the Observer Does

- **Detects context loss** — flags when AI loses track of earlier instructions mid-sprint
- **Flags overrides** — identifies when the human corrected/rejected AI output
- **Spots scope creep** — recognizes when a task expanded beyond its original brief
- **Identifies iteration loops** — detects when the AI is cycling without converging
- **Classifies incident categories** — auto-tags as OPS/GOV/COM/PRD/RES/DES

---

## Technical Architecture

1. **Training data:** 54 existing governance incidents + 20+ calibrated sessions (positive + negative examples)
2. **Base model:** Qwen2.5-1.5B or similar (small enough for GGUF quantization)
3. **Export format:** GGUF (Q4_K_M quantization, ~1.2GB)
4. **Distribution:** HuggingFace — download on first use, not bundled
5. **Runtime:** `llama-cpp-python` (bundled in exe, ~5MB) or `ollama` (if installed)
6. **Command:** `praxis observe --setup` downloads model, then runs automatically during sessions

---

## Prerequisite Chain (Honest Sequencing)

The observer cannot be trained on ghost data. Each step depends on the previous:

### Pre-Admission (Now → Oct 2026)

| Step | What | Status | Why it blocks |
|------|------|--------|---------------|
| 1 | Fix model detection in adapters | ❌ `model: unknown` | Can't classify what model did if we don't know the model |
| 2 | Complete L1-R (5/5 dimensions) in checkout | ⚠️ 2/5 | Incomplete relational governance data = incomplete training labels |
| 3 | Auto-close orphan sessions on export | ❌ Missing | Corrupts duration data |
| 4 | Collect 20+ calibrated sessions across 2+ platforms | ⏳ 2 done | Need enough labeled data to train a classifier |
| 5 | Label 54 incidents + 20 sessions into structured training set | ⏳ Incidents exist | Need both positive (governance event) and negative (normal session) examples |

### Post-Admission (Oct 2026+)

| Step | What | Depends on |
|------|------|-----------|
| 6 | Fine-tune Qwen2.5-1.5B classifier | Steps 4-5 complete |
| 7 | Export to GGUF, test on GTX 1080 | Step 6 |
| 8 | Build `praxis observe` command | Step 7 |
| 9 | Code signing (exe + dmg) | Greenlight from Javier |
| 10 | EU AI Act compliance matrix | Can start anytime |
| 11 | OSF pre-registration template | Before first external participant |
| 12 | Ethics submission package | Before external data collection |
| 13 | Randomized assignment + task stimulus set | Before controlled study |
| 14 | Blinded evaluation rubric + statistical analysis scripts | Before controlled study |

---

## Why v1.0 = Observer Model

The observer is what makes PRAXIS citable and novel:

- **Without it:** PRAXIS is a logging tool with smart checkout — useful, but not a research contribution
- **With it:** PRAXIS is "a tool that watches your AI workflow and auto-detects governance events" — that's a novel instrument
- The Cowork thesis review scored current work 7.5/10 ceiling. The observer model + controlled study data is what could push toward 8.7
- It solves the #1 practical problem: participants won't fill forms, but an auto-classifier needs zero effort

---

## VRAM Considerations

- Qwen2.5-1.5B in Q4_K_M quantization: ~1.2GB VRAM
- Anyone running Codex, Claude Cowork, or OpenClaw already has hardware that exceeds this
- Fallback: CPU inference via `llama-cpp-python` (slower but works on any machine)
- GTX 1080 8GB can run this alongside existing workloads

---

## Version Progression (Confirmed)

| Version | Feature | Status |
|---------|---------|--------|
| v0.7 | Passive capture + human checkout | ✅ Shipped |
| v0.8 | Smart contextual checkout | ✅ Shipped |
| v0.9.0 | Thin platform adapters (OpenClaw + Codex) | ✅ Shipped |
| v0.9.1 | Cowork/Claude bridge telemetry adapter | ✅ Shipped |
| v0.9.2 | Plugin adapter system (drop-in custom adapters) | ✅ Shipped |
| v0.9.3 | Fix model detection + complete L1-R + auto-close | 🔜 Next |
| v0.9.x | 20+ calibrated sessions collected | ⏳ Pre-admission |
| **v1.0** | **Local observer model (auto-classification)** | 🎯 Post-admission |

---

*This document is the single source of truth for PRAXIS Kit v1.0. Update when milestones change.*
