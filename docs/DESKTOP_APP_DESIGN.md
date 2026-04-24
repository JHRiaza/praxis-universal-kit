# PRAXIS Kit Desktop — Design Document

**Created:** 2026-04-24
**Status:** Draft
**Audience:** Javier (review), development reference
**Scope:** MVP desktop app wrapping the existing PRAXIS Universal Kit CLI

---

## 1. Tech Stack Recommendation

### Recommended: **Python + CustomTkinter + PyInstaller**

**Why not the alternatives?**

| Option | Verdict | Reason |
|--------|---------|--------|
| **Tauri + PyInstaller sidecar** | Overkill | Requires Rust toolchain + Node.js + web frontend framework. Tauri sidecar with PyInstaller is viable but documented as finicky (dual-process issues on Windows). Adds 3 tech stacks (Rust, JS/TS, Python) for a 5-20 user tool. |
| **Electron + Python backend** | Rejected | 80-150MB bundle, 150-300MB RAM idle. Unacceptable for a data collection tool researchers run alongside their IDE. Electron is for commercial-scale apps, not PhD research tools. |
| **PyQt/PySide6** | Runner-up | More professional UI, but steeper learning curve, heavier dependency. LGPL licensing is fine but the framework feels "heavy" for what's essentially a form-based data logger. |
| **Python + CustomTkinter + PyInstaller** | **Winner** | Zero external GUI dependencies beyond `customtkinter` (pip install). Modern-looking widgets. PyInstaller produces single-file .exe and .app bundles natively. The collector code has **zero external dependencies** — adding one lightweight GUI library is minimal. |

### Justification

1. **Reuse, don't rewrite.** The collector (`praxis_collector.py`) has zero deps. The CLI (`praxis_cli.py`) imports it directly. The desktop app will import the same `praxis_collector` module and call the same functions — no subprocess, no sidecar, no IPC.
2. **Single language, single build chain.** Python → PyInstaller → .exe/.dmg. No Rust, no Node, no web bundler.
3. **Tiny dependency footprint.** `customtkinter` is the only new dep. Everything else is stdlib.
4. **5-20 users.** This doesn't need a commercial-grade framework. It needs to work reliably on researchers' laptops.
5. **CustomTkinter** provides modern-looking dark-mode widgets out of the box — no "ugly Tkinter" complaints.

### Alternative path (if CustomTkinter proves insufficient)

If the UI needs become more complex (charts, tables, etc.), migrate to PySide6. The architecture is the same — only the view layer changes. Both wrap the same `praxis_collector` backend.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────┐
│               PRAXIS Desktop App                │
│                                                 │
│  ┌───────────────────────────────────────────┐  │
│  │         View Layer (CustomTkinter)        │  │
│  │                                           │  │
│  │  ┌─────────┐ ┌────────┐ ┌─────────────┐  │  │
│  │  │ Dashboard│ │ Log    │ │  Export &    │  │  │
│  │  │ (status) │ │ Sprint │ │  Submit     │  │  │
│  │  └────┬─────┘ └───┬────┘ └──────┬──────┘  │  │
│  │       │           │             │          │  │
│  │  ┌────┴───────────┴─────────────┴──────┐   │  │
│  │  │        ViewModel / Controller       │   │  │
│  │  │  (transforms UI events → collector   │   │  │
│  │  │   calls, formats data for display)  │   │  │
│  │  └──────────────┬──────────────────────┘   │  │
│  └─────────────────┼──────────────────────────┘  │
│                    │                             │
│  ┌─────────────────┴──────────────────────────┐  │
│  │     Model Layer (REUSED — no changes)      │  │
│  │                                            │  │
│  │  praxis_collector.py                       │  │
│  │  ├── find_praxis_dir()                     │  │
│  │  ├── load_state() / save_state()           │  │
│  │  ├── build_metric_entry()                  │  │
│  │  ├── append_metric_entry()                 │  │
│  │  ├── compute_summary()                     │  │
│  │  ├── activate_phase_b()                    │  │
│  │  ├── append_governance_event()             │  │
│  │  ├── append_incident_event()               │  │
│  │  ├── load_all_metrics()                    │  │
│  │  └── generate_participant_id()             │  │
│  │                                            │  │
│  │  export/anonymize.py                       │  │
│  │  └── export_participant_zip()              │  │
│  └────────────────────────────────────────────┘  │
│                                                 │
│  Data: .praxis/ directory (JSONL + JSON)        │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User clicks "Log Sprint" in GUI
  → ViewModel collects form fields (task, duration, model, quality, etc.)
  → Calls build_metric_entry(state, task, duration, model, quality, ...)
  → Calls append_metric_entry(praxis_dir, entry)
  → Entry written to .praxis/metrics.jsonl
  → GUI shows confirmation + updates dashboard stats
```

No subprocess, no CLI parsing. The GUI calls the same Python functions the CLI calls.

---

## 3. Feature List

### MVP (Sprint 1-3)

| Feature | Priority | Sprint |
|---------|----------|--------|
| **Init / Setup wizard** | P0 | 1 |
| **Dashboard (status view)** — phase, participant ID, metrics summary, days of data | P0 | 1 |
| **Log Sprint** — form with task, duration, model, quality (slider), iterations, interventions | P0 | 1 |
| **PRAXIS-Q quick rating** — 5 sliders (1-3) after logging in Phase B | P0 | 2 |
| **Log Governance Event** — simple form (description + type dropdown) | P0 | 2 |
| **Log Incident** — description, category, optional root cause / new rule | P1 | 2 |
| **Export & Submit** — one-click anonymized ZIP + email/HTTP upload | P0 | 2 |
| **Activate Phase B** — guided activation with consent confirmation | P1 | 3 |
| **Platform detection display** — show detected AI platforms | P2 | 3 |
| **Pre/Post Survey** — render survey questions in GUI instead of terminal | P1 | 3 |
| **Withdraw** — with confirmation dialog | P1 | 3 |

### Future (Post-MVP)

| Feature | Notes |
|---------|-------|
| **Auto-update** | Check GitHub Releases for new versions, prompt to download |
| **System tray mode** | Quick-log from system tray without opening full window |
| **Timeline view** | Visual timeline of logged sprints |
| **Charts** | Quality over time, autonomy rate trend, PRAXIS-Q heatmap |
| **Multi-project support** | Switch between multiple .praxis directories |
| **Offline-first sync** | Queue exports for later submission when offline |
| **Localization** | Spanish UI (currently only EN surveys exist) |
| **Accessibility** | Screen reader support, keyboard navigation |

---

## 4. Sprint Breakdown

### Sprint 1: Core Shell + Log + Status (5-7 days)

**Goal:** A usable app that can initialize PRAXIS, log sprints, and show status.

**Deliverables:**
- App skeleton with CustomTkinter, tab-based navigation
- **Init wizard** — consent + participant ID generation (calls `initialize_state()`)
- **Dashboard tab** — reads state + computes summary (calls `load_state()`, `compute_summary()`)
- **Log Sprint tab** — form with all P0 fields, writes to `.praxis/metrics.jsonl`
- Basic .exe build via PyInstaller
- Symlink or copy of `praxis_collector.py` accessible to the desktop app

**Exit criteria:** Researcher can download .exe, initialize PRAXIS in a project folder, log a sprint, and see it on the dashboard.

### Sprint 2: Governance + Incidents + Export (5-7 days)

**Goal:** Full Phase B support + data submission.

**Deliverables:**
- **Governance tab** — log governance events (calls `append_governance_event()`)
- **Incident tab** — structured incident capture with category, root cause, proposed rule
- **PRAXIS-Q panel** — 5-dimension slider widget, shown after logging in Phase B
- **Export & Submit tab** — one-click ZIP generation + upload mechanism (see §7)
- **Activate Phase B** flow — consent dialog + governance injection
- macOS .app build tested

**Exit criteria:** Researcher can go through full Phase A → Activate → Phase B → Export cycle entirely in the GUI.

### Sprint 3: Surveys + Polish + Distribution (3-5 days)

**Goal:** Feature-complete MVP with installers.

**Deliverables:**
- **Survey renderer** — reads `surveys/*.json`, renders questions as GUI widgets
- **Platforms display** — show detected platforms with tier info
- **Withdraw flow** — confirmation dialog + data deletion
- **Windows installer** (.exe with NSIS or Inno Setup)
- **macOS disk image** (.dmg)
- **README for desktop app** — installation + usage guide
- Basic auto-update check (HTTP HEAD to GitHub Releases, notify if newer version)

**Exit criteria:** Both .exe and .dmg installers produced. A new researcher can install, set up, and use the app without touching the CLI.

---

## 5. File Structure

```
D:\PRAXIS\universal-kit\
├── collector/                    # EXISTING — unchanged
│   ├── praxis_cli.py             # CLI entry point (unchanged)
│   ├── praxis_collector.py       # Core data layer (unchanged)
│   └── requirements.txt          # (empty — zero deps)
│
├── desktop/                      # NEW — desktop app
│   ├── main.py                   # Entry point for desktop app
│   ├── app.py                    # App class, window setup, tab controller
│   ├── views/
│   │   ├── __init__.py
│   │   ├── dashboard.py          # Status/dashboard tab
│   │   ├── log_sprint.py         # Sprint logging form
│   │   ├── governance.py         # Governance event form
│   │   ├── incident.py           # Incident logging form
│   │   ├── export_submit.py      # Export + upload tab
│   │   ├── survey.py             # Survey renderer
│   │   ├── activate.py           # Phase B activation flow
│   │   ├── platforms.py          # Platform detection display
│   │   └── withdraw.py           # Withdraw confirmation
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── praxis_q_slider.py    # PRAXIS-Q 5-dimension rating widget
│   │   ├── quality_slider.py     # Quality 1-5 slider
│   │   └── form_fields.py        # Reusable form components
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── app_controller.py     # Business logic, bridges views ↔ collector
│   └── requirements.txt          # customtkinter + any desktop-only deps
│
├── export/                       # EXISTING — unchanged
│   └── anonymize.py              # ZIP export logic (called by desktop app)
│
├── build/                        # NEW — build scripts
│   ├── build_windows.py          # PyInstaller build script for Windows
│   ├── build_macos.sh            # PyInstaller build script for macOS
│   ├── praxis_desktop.spec       # PyInstaller spec file
│   └── installer/
│       ├── windows.nsi           # NSIS installer script (or Inno Setup)
│       └── create_dmg.sh         # DMG creation script for macOS
│
├── surveys/                      # EXISTING — unchanged
├── templates/                    # EXISTING — unchanged
├── config/                       # EXISTING — unchanged
├── adapters/                     # EXISTING — unchanged
└── docs/
    └── DESKTOP_APP_DESIGN.md     # This document
```

### Key design decision

The `desktop/` directory is a sibling to `collector/`. The desktop app imports from `collector.praxis_collector` using a relative import or sys.path manipulation (same pattern the CLI already uses). No code duplication.

```python
# desktop/controllers/app_controller.py
import sys
from pathlib import Path

# Add parent dir to path (same pattern as praxis_cli.py)
_kit_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_kit_root / "collector"))

from praxis_collector import (
    find_praxis_dir,
    load_state,
    build_metric_entry,
    append_metric_entry,
    compute_summary,
    ...
)
```

---

## 6. Build & Distribution Pipeline

### Windows (.exe)

```
1. PyInstaller builds single-file executable:
   pyinstaller --onefile --windowed --name "PRAXIS Kit" desktop/main.py

2. Optional: NSIS or Inno Setup wraps it into an installer:
   - Installs to %LOCALAPPDATA%\PRAXIS Kit\
   - Creates Start Menu shortcut
   - Creates Desktop shortcut
   - Adds to PATH (optional, for CLI coexistence)

3. Distribute via GitHub Releases (praxis-universal-kit repo)
```

**Bundle size estimate:** ~15-25MB (Python interpreter + stdlib + customtkinter + tk). The collector has zero deps so this stays lean.

### macOS (.dmg)

```
1. PyInstaller builds .app bundle (must build on macOS):
   pyinstaller --windowed --name "PRAXIS Kit" desktop/main.py

2. Package into DMG:
   create-dmg --volname "PRAXIS Kit" --app-drop-link 250 50 \
     "PRAXIS-Kit-0.3.dmg" "dist/PRAXIS Kit.app"

3. Code signing: self-signed is fine for 5-20 users.
   For broader distribution: Apple Developer cert ($99/year) — NOT needed for MVP.

4. Distribute via GitHub Releases.
```

### CI/CD (Future, not MVP)

```
GitHub Actions:
  - on tag v*: build Windows (.exe) + macOS (.dmg)
  - Upload to GitHub Releases
  - Update latest.json for auto-update checks
```

For MVP, manual builds are fine. Javier builds Windows on his machine. macOS can be built on a GitHub Actions runner (free for public repos) or on a borrowed Mac.

### PyInstaller Spec Highlights

```python
# build/praxis_desktop.spec
a = Analysis(
    ['../desktop/main.py'],
    pathex=['../collector'],  # Include collector module
    datas=[
        ('../surveys', 'surveys'),       # Bundle survey JSON files
        ('../templates', 'templates'),   # Bundle templates
        ('../config', 'config'),         # Bundle platform config
        ('../CONSENT.md', '.'),          # Bundle consent form
        ('../CONSENTIMIENTO.md', '.'),
    ],
    hiddenimports=['customtkinter'],
)
```

---

## 7. Data Upload Mechanism

### Current state (CLI)

The CLI's `export` command creates a ZIP and tells the user to email it or upload manually. `submit.py` starts a local HTTP server and opens a browser page with a mailto: link. This is clunky.

### Desktop App: One-Click Upload

**Primary mechanism: HTTP POST to a receiving endpoint.**

```
┌──────────────┐         ┌──────────────────────┐
│ PRAXIS       │  HTTPS  │ Receiving Endpoint    │
│ Desktop App  │ ──────→ │ (simple, TBD)         │
│              │  POST   │                      │
│ 1. Generate  │  ZIP    │ Options:              │
│    ZIP       │        │ - Google Form + file   │
│ 2. POST to   │        │ - Supabase Storage     │
│    endpoint  │        │ - S3 presigned URL     │
│ 3. Show      │        │ - Email via API        │
│    success   │        │   (Resend/SendGrid)    │
└──────────────┘         └──────────────────────┘
```

**Recommended endpoint: Google Form with file upload**

Simplest approach for 5-20 users:
1. Create a Google Form with a file upload question
2. Desktop app opens the form URL in the default browser after generating the ZIP
3. User drags the ZIP onto the form

**Alternative: Direct email via Resend API (no SMTP client needed)**

```python
import requests

def submit_data(zip_path, participant_id):
    """Upload ZIP to researcher via email API."""
    files = {'attachment': open(zip_path, 'rb')}
    data = {
        'from': 'praxis@javierherreros.xyz',
        'to': 'hello@javierherreros.xyz',
        'subject': f'PRAXIS data submission [{participant_id}]',
        'text': f'Automated submission from PRAXIS Desktop Kit.\nParticipant: {participant_id}'
    }
    # Resend API (free tier: 100 emails/day)
    requests.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {RESEND_API_KEY}'},
        files=files,
        data=data
    )
```

**For MVP:** Use the existing `submit.py` approach (local HTTP server + mailto link), adapted to the GUI. The app generates the ZIP, opens the user's email client with the address pre-filled, and tells them to attach the file. This requires zero infrastructure.

**Post-MVP:** Add a proper upload endpoint (Supabase Storage is free tier friendly, or a simple Cloudflare Worker that receives files).

### Upload flow in the GUI

```
Export & Submit tab:
┌─────────────────────────────────────────────┐
│  Export PRAXIS Data                          │
│                                              │
│  ☐ Redact task descriptions                 │
│                                              │
│  [ Generate Export ZIP ]                     │
│                                              │
│  ─── After generating ───                    │
│                                              │
│  ✓ ZIP created: praxis_ABC_2026-04-24.zip   │
│    Files: 42 metrics, 7 governance events    │
│                                              │
│  [ 📧 Open Email to Submit ]                 │
│  [ 📁 Open File Location ]                   │
│                                              │
│  Or submit directly (requires internet):     │
│  [ ☁️ Upload to Research Server ]            │
└─────────────────────────────────────────────┘
```

---

## 8. Estimated Effort

| Sprint | Scope | Effort | Notes |
|--------|-------|--------|-------|
| **Sprint 1** | Core shell + Log + Dashboard | 5-7 days | Most new code. Setting up CustomTkinter, learning the framework, building the log form. |
| **Sprint 2** | Governance + Incidents + Export + PRAXIS-Q | 4-5 days | Simpler forms. Export is mostly wiring existing `anonymize.py`. PRAXIS-Q is a custom slider widget. |
| **Sprint 3** | Surveys + Build pipeline + Installers + Polish | 3-5 days | Survey renderer is the tricky part. Build pipeline is mostly config. |
| **Total** | Full MVP | **12-17 days** | Single developer. Parallelizable if split by view. |

### Effort breakdown by component

| Component | Lines (est.) | Time |
|-----------|-------------|------|
| App shell + navigation | ~150 | 1 day |
| Dashboard view | ~200 | 1 day |
| Log Sprint form | ~300 | 1.5 days |
| PRAXIS-Q widget | ~100 | 0.5 day |
| Governance form | ~100 | 0.5 day |
| Incident form | ~150 | 0.5 day |
| Export & Submit view | ~200 | 1 day |
| Activate flow | ~150 | 0.5 day |
| Survey renderer | ~300 | 1.5 days |
| Withdraw flow | ~80 | 0.5 day |
| Platform detection view | ~80 | 0.5 day |
| Controller layer | ~250 | 1 day |
| PyInstaller config + testing | — | 1 day |
| Installers (.exe, .dmg) | — | 1 day |
| Testing + bug fixes | — | 2 days |
| **Total** | ~2,060 | **14 days** |

---

## 9. Kill Conditions

**Abandon this approach if:**

1. **CustomTkinter can't render the survey JSON dynamically.** The survey system has `single_choice`, `multi_choice`, `likert_5`, `likert_7`, `numeric`, and `open_text` question types. If building a dynamic form renderer in CustomTkinter becomes a nightmare (unlikely but possible), fall back to: (a) rendering surveys in an embedded HTML view, or (b) keeping surveys CLI-only.

2. **PyInstaller bundle exceeds 50MB.** For a data collection tool, this is too heavy. The zero-dep collector should keep this well under 30MB. If customtkinter pulls in something unexpected, switch to vanilla tkinter (built into Python — zero additional size).

3. **macOS build requires Apple Developer certificate.** If macOS Gatekeeper blocks the app and researchers can't open it without terminal workarounds (`xattr -cr`), and we can't afford the $99/year cert, we may need to: (a) distribute as a Python package (`pip install praxis-desktop`), or (b) tell Mac users to use the CLI.

4. **More than 2 weeks spent on Sprint 1 without a usable log form.** If the GUI framework fights us on basic form layouts, the ROI isn't there. Cut losses, improve the CLI experience instead (better prompts, colors, maybe a TUI with `textual`).

5. **Researchers prefer the CLI.** If during user testing (even informal), researchers say "actually the terminal is fine," stop building the GUI. This is a convenience tool, not a product. If the convenience isn't wanted, don't build it.

6. **CustomTkinter is abandoned or breaks on Python 3.13+.** Check PyPI release dates. If the last release is >12 months old and there are open issues for current Python, switch to PySide6 or vanilla tkinter.

### Pivot options if killed

- **Option A:** Invest in a better TUI instead (Python `textual` — beautiful terminal UIs). Zero packaging issues.
- **Option B:** Web app (Flask/FastAPI + simple HTML). Researchers open `localhost:8080`. The `submit.py` already does this pattern.
- **Option C:** VS Code extension. Most researchers use VS Code. An extension panel that calls the collector functions would integrate naturally.

---

## Appendix A: Dependency Analysis

The existing PRAXIS kit has these dependencies:

```
collector/praxis_collector.py  → Python stdlib only (zero deps)
collector/praxis_cli.py        → Python stdlib only (zero deps)
export/anonymize.py            → Python stdlib only (zero deps)
collector/submit.py            → Python stdlib only (zero deps)
```

The desktop app adds:

```
customtkinter >= 5.2           ~2MB, actively maintained (2025+)
tkinter                        Bundled with Python on Windows/macOS
```

That's it. One new dependency. If customtkinter is rejected, vanilla tkinter is already available.

## Appendix B: How It Differs from CLI

| Aspect | CLI | Desktop |
|--------|-----|---------|
| Entry point | `python praxis_cli.py <command>` | Double-click app icon |
| Data input | Terminal prompts + argparse flags | GUI forms with sliders, dropdowns |
| PRAXIS-Q | Terminal `ask_int()` per dimension | Visual sliders with labels |
| Survey | Terminal-based, line by line | GUI form with radio buttons, text areas |
| Export | Creates ZIP, prints instructions | Creates ZIP + one-click email/upload |
| Status | Text output in terminal | Dashboard with numbers + progress |
| Install | Python + kit clone | Download .exe/.dmg, run |
| Target user | Developers comfortable with terminal | Anyone (including non-developers) |

The CLI remains fully functional and supported. The desktop app is an alternative interface for the same data and the same `.praxis/` directory. Both can be used interchangeably on the same project.

## Appendix C: PRAXIS-Q Slider Widget Design

```
PRAXIS-Q Quick Rating
─────────────────────
Completeness        [━━━━━●━━━━] 2/3 — Acceptable
Quality             [━━━━━━━●━━] 3/3 — Excellent
Coherence           [━━━━━●━━━━] 2/3 — Acceptable
Efficiency          [━━━━●━━━━━] 1/3 — Needs work
Traceability        [━━━━━━━●━━] 3/3 — Excellent

Total: 2.2 / 3.0  (⚠ Acceptable zone)
```

Each dimension is a horizontal slider (1-3) with a label. The total updates in real-time. Color coding: green ≥ 2.4, yellow ≥ 1.7, red < 1.7 — matching the CLI's zone colors.

---

*End of design document. Next step: Javier reviews, approves/modifies, then Sprint 1 begins.*
