# macOS Distribution Strategy — PRAXIS Kit

## The Problem

PyInstaller bundles on macOS trigger a "git not found" → Command Line Tools install prompt. If CLT can't be reached (server issues, outdated macOS), the app is dead in the water. This is NOT a PRAXIS bug — it's a Python/tkinter dependency chain issue.

**Root cause:** Python's `git` integration (via gitpython or subprocess) tries to call system `git`. On fresh macOS, git comes from CLT. No CLT = no git = app crashes or stalls.

## Options (ranked by effort vs impact)

### Option 1: Pre-flight Check + Graceful Degradation (1-2 days)
**What:** App detects missing git on startup, shows friendly message, disables git-tracking features gracefully.
**Pros:** Quick, no new toolchain, works with current PyInstaller pipeline.
**Cons:** Git tracking features disabled for users without CLT.
**Effort:** LOW

### Option 2: Bundle `git` with PyInstaller (1-2 days)
**What:** Include a static git binary in the macOS build. PyInstaller can bundle it.
**Pros:** No CLT dependency, git tracking works everywhere.
**Cons:** Increases binary size (~30MB → ~60MB), licensing (GPL), need to maintain per-architecture builds.
**Effort:** LOW-MEDIUM

### Option 3: Rewrite CLI in Rust/Go, Keep Desktop as Electron/Tauri (2-4 weeks)
**What:** Replace Python backend with compiled binary. Desktop becomes Tauri (Rust + web UI) or Electron.
**Pros:** No Python dependency at all, single binary, native performance, smaller size.
**Cons:** Major rewrite, new toolchain, ongoing maintenance.
**Effort:** HIGH

### Option 4: Swift + C++ Native App (1-3 months)
**What:** Full native macOS app in Swift with C++ core for cross-platform logic.
**Pros:** Best macOS experience, App Store distribution, code signing, no dependency issues.
**Cons:** Massive rewrite, macOS-only, requires Apple Developer account ($99/yr), Xcode, code signing certificates.
**Effort:** VERY HIGH
**NOTE:** Only makes sense for a "final" commercial product, not research tooling.

## Recommendation

**For PRAXIS thesis timeline (now → Sep 2026): Option 1 + Option 2**

1. **Immediate (v0.9.5):** Add pre-flight check — if no git, show warning, degrade gracefully
2. **Short-term (v0.9.6):** Bundle static git binary in macOS PyInstaller build via GitHub Actions
3. **Post-thesis:** Evaluate Option 3 (Rust/Tauri) for commercial version

**Option 4 (Swift/C++) is overkill for a research tool.** Save it for a commercial pivot if PRAXIS Kit becomes a product.

### Apple Developer Account
- **Not needed** for Options 1-3 (distribute via GitHub Releases, users right-click → Open)
- **Needed** for Option 4 (App Store, notarized distribution, no Gatekeeper warnings)
- **Cost:** $99/year
- **Recommendation:** Don't buy it until you're doing Option 4

---

*Assessment date: 2026-04-30*
*Context: PRAXIS Kit v0.9.4 macOS testing failure*
