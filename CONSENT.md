# Research Participation Consent Form

## Study Information

**Title:** Methodological Architecture for Autonomous AI-Assisted Systems: A Quasi-Experimental Study of PRAXIS Governance Framework Adoption

**Principal Researcher:** Javier Herreros Riaza
**Institution:** Doctoral Program in Audiovisual Communication and Advertising (CAVP)
**Framework:** PRAXIS v1.1

---

## Purpose of the Study

This research documents what happens when people adopt a governance framework (PRAXIS) for AI-assisted work. The study uses a within-subjects design: you serve as your own control group, first working without governance (Phase A baseline), then with PRAXIS governance active (Phase B treatment).

The study captures metrics from the same person, same projects, same tools — before and after governance adoption — to observe governance phenomena such as rule emergence, relational governance effects, and personality portability across AI models.

---

## What Participation Involves

### Duration
- **Phase A (Baseline):** 1–2 weeks of normal AI-assisted work
- **Phase B (Treatment):** 2+ weeks with PRAXIS governance active
- **Total time commitment:** 3–4 weeks minimum

### What you will do
1. Install the PRAXIS Kit on your computer
2. Complete a pre-study survey (~10 minutes)
3. Log your AI-assisted tasks daily using the `praxis log` command
4. After 7+ days, run `praxis activate` to start Phase B
5. Continue logging tasks during Phase B (with PRAXIS-Q quality rating)
6. Log governance events when you create or modify rules
7. Complete a post-study survey (~12 minutes) after Phase B
8. Export your anonymized data for the researcher

### What is collected

**Collected (with your knowledge):**
- Task metrics: description, duration, quality rating (1-5), AI generation cycles, human corrections
- AI model/tool names you report
- PRAXIS-Q quality scores (Phase B)
- L1-R observations (optional): your perceptions of AI confidence, warmth, trust, and compliance tendency per task
- Governance events: rules you create, incidents, modifications
- Session boundary observations: memory and calibration recovery across sessions
- Survey responses (both pre and post)
- Phase dates and session counts
- Experimental condition assignment (if participating in the 2×2 factorial study)
- External quality evaluation: an independent evaluator may score your anonymized outputs using PRAXIS-Q

**Never collected:**
- The content of your source code, documents, or files
- Your AI conversation logs or prompts
- Personal identifiable information beyond your participant ID
- Anything from outside the `.praxis/` directory

---

## Data Privacy and Security

### Storage
All data is stored **locally** on your computer in a `.praxis/` directory. Nothing is automatically uploaded to any server or cloud service.

### Anonymization
Your participant ID is automatically generated from a hash of anonymous machine characteristics. It does not include your name, email, or any directly identifying information.

When you export data (`praxis export`), the system:
- Strips any potential PII from metric entries
- Uses only your participant ID (format: `PRAXIS-XXXXXXXX`)
- Optionally allows you to redact task descriptions
- Creates a ZIP file suitable for research submission

### Publication
- In all publications, you will appear as "Participant P###" or equivalent
- Your name will not appear in any publication unless you provide separate explicit written consent
- Individual responses may be cited anonymously to illustrate findings

### Data retention
- Your local data remains on your computer under your control
- Submitted data is retained by the researcher for the duration of the doctoral research (estimated completion: 2027)
- You may request deletion of your submitted data at any time

---

## Your Rights

As a research participant, you have the right to:

- **Withdraw** at any time without consequence using `praxis withdraw` (deletes all local data permanently)
- **Review** the data collected about you before submission
- **Redact** task descriptions from your exported data (use `praxis export --redact-tasks`)
- **Refuse** to answer any survey question
- **Request** a copy of the research findings when the study is complete
- **Contact** the researcher with any questions or concerns

---

## Benefits

By participating, you:
- Receive the PRAXIS Kit configured for your specific AI tools
- Gain insight into your own AI workflow patterns from your personal metrics
- Contribute to doctoral research that may benefit the broader AI-using community
- Will be credited in the acknowledgments of the thesis (if you wish)
- Will receive access to final research findings

---

## Risks

- Time commitment of a few minutes per day to log tasks
- Minor adjustment period when adopting governance in Phase B
- No known psychological, physical, or financial risks

---

## Contact

For questions about this research:

**Researcher:** Javier Herreros Riaza
**Institution:**
**Program:** Doctorado CAVP

---

## Consent Declaration

By running the PRAXIS installer and responding "yes" to the consent prompt, you declare that:

- [ ] You have read and understood this consent form
- [ ] You understand what data is collected and how it will be used
- [ ] You understand you can withdraw at any time using `praxis withdraw`
- [ ] You are 18 years of age or older
- [ ] You consent to participate in this research study

Your consent is recorded with a timestamp in `.praxis/state.json` on your local machine.

---

*PRAXIS Universal Kit v0.2*
*Doctoral Research*
*Framework: CC BY-SA 4.0*
