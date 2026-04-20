# GitHub Repo Preparation — praxis-universal-kit

**Date:** 2026-04-20
**Status:** Ready for Javier to create repo

## Steps for Javier

1. Go to github.com/jhriaza and create new repo: `praxis-universal-kit`
   - Description: "Cross-platform research tool for observing governance phenomena in AI-assisted workflows — PRAXIS Universal Kit v0.2"
   - Public
   - NO initialize with README (we already have one)
   - License: CC-BY-SA-4.0 (already in repo)
   - .gitignore: Python

2. Give Suzanne access (or use a deploy key)

3. Once repo exists, I will:
   - Initialize git in D:\PRAXIS\universal-kit\
   - Add remote
   - Push all 41 files
   - Then: Zenodo archive for DOI

## Files to include (41 files, 293.7 KB)

All files in `D:\PRAXIS\universal-kit\` are ready. Key files:
- README.md (v0.2, descriptive framing)
- README_ES.md (Spanish, Cowork-polished)
- ARCHITECTURE.md (Cowork-polished)
- CHANGELOG.md
- CITATION.cff
- LICENSE
- All templates, adapters, config, collector scripts, surveys, consent forms

## Files to EXCLUDE (.gitignore)
- __pycache__/
- *.pyc
- .praxis/ (local data)
- *.jsonl (participant data)
- .DS_Store
