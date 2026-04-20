#!/usr/bin/env python3
"""
PRAXIS Universal Kit — CLI Entry Point
=======================================
Commands: status, log, activate, govern, survey, export, platforms, withdraw

Usage:
    python praxis_cli.py <command> [options]
    praxis <command> [options]   (after install)

Python 3.8+ compatible. Zero external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

# Ensure UTF-8 output on Windows (box-drawing chars, etc.)
if sys.platform == "win32":
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        if _stream and hasattr(_stream, "reconfigure"):
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent dir to path when running directly
_HERE = Path(__file__).parent.resolve()
sys.path.insert(0, str(_HERE))

from praxis_collector import (
    GOVERNANCE_FILE,
    METRICS_FILE,
    VALID_GOVERNANCE_TYPES,
    VALID_LAYERS,
    PraxisError,
    InvalidPhaseError,
    StateNotFoundError,
    ValidationError,
    activate_phase_b,
    append_governance_event,
    append_metric_entry,
    build_metric_entry,
    compute_summary,
    detect_platforms,
    find_praxis_dir,
    generate_participant_id,
    get_or_create_praxis_dir,
    initialize_state,
    load_all_metrics,
    load_governance_events,
    load_state,
    load_survey_responses,
    save_state,
    save_survey_response,
    touch_last_active,
    withdraw_participant,
)


# ---------------------------------------------------------------------------
# Terminal colors (no external deps — pure ANSI)
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    """Check if the terminal supports ANSI colors."""
    if os.environ.get("NO_COLOR") or os.environ.get("PRAXIS_NO_COLOR"):
        return False
    try:
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            # Allow color in Windows Terminal / CI that sets TERM
            return bool(os.environ.get("COLORTERM") or os.environ.get("TERM"))
        return True
    except OSError:
        return False


_COLOR = _supports_color()


class C:
    """ANSI color codes."""
    RESET   = "\033[0m"  if _COLOR else ""
    BOLD    = "\033[1m"  if _COLOR else ""
    DIM     = "\033[2m"  if _COLOR else ""
    RED     = "\033[31m" if _COLOR else ""
    GREEN   = "\033[32m" if _COLOR else ""
    YELLOW  = "\033[33m" if _COLOR else ""
    BLUE    = "\033[34m" if _COLOR else ""
    MAGENTA = "\033[35m" if _COLOR else ""
    CYAN    = "\033[36m" if _COLOR else ""
    WHITE   = "\033[37m" if _COLOR else ""
    B_RED     = "\033[91m" if _COLOR else ""
    B_GREEN   = "\033[92m" if _COLOR else ""
    B_YELLOW  = "\033[93m" if _COLOR else ""
    B_BLUE    = "\033[94m" if _COLOR else ""
    B_CYAN    = "\033[96m" if _COLOR else ""


def _c(text: str, *codes: str) -> str:
    if not _COLOR or not codes:
        return text
    return "".join(codes) + text + C.RESET


def print_header(title: str) -> None:
    try:
        width = min(os.get_terminal_size().columns, 72)
    except Exception:
        width = 72
    line = "─" * width
    print(f"\n{_c(line, C.DIM)}")
    print(f"  {_c('PRAXIS', C.BOLD, C.B_CYAN)} {_c(title, C.BOLD)}")
    print(f"{_c(line, C.DIM)}")


def print_ok(msg: str) -> None:
    print(f"  {_c('✓', C.B_GREEN)} {msg}")


def print_warn(msg: str) -> None:
    print(f"  {_c('!', C.B_YELLOW)} {_c(msg, C.YELLOW)}")


def print_err(msg: str) -> None:
    print(f"  {_c('✗', C.B_RED)} {_c(msg, C.RED)}", file=sys.stderr)


def print_info(msg: str) -> None:
    print(f"  {_c('·', C.DIM)} {msg}")


def print_field(label: str, value: str, color: str = "") -> None:
    label_str = _c(f"{label:<22}", C.DIM)
    val_str = _c(str(value), color) if color else str(value)
    print(f"  {label_str} {val_str}")


def ask(prompt: str, default: str = "") -> str:
    """Prompt user for input. Returns stripped response."""
    try:
        suffix = f" [{default}]" if default else ""
        response = input(f"\n  {_c('?', C.B_CYAN)} {prompt}{suffix}: ").strip()
        return response or default
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def ask_yn(prompt: str, default: bool = True) -> bool:
    """Ask yes/no question."""
    default_str = "Y/n" if default else "y/N"
    try:
        response = input(f"\n  {_c('?', C.B_CYAN)} {prompt} [{default_str}]: ").strip().lower()
        if not response:
            return default
        return response in ("y", "yes", "s", "si", "sí")
    except (EOFError, KeyboardInterrupt):
        print()
        return default


def ask_int(prompt: str, min_val: int, max_val: int, default: Optional[int] = None) -> int:
    """Ask for an integer in range."""
    default_str = f" [{default}]" if default is not None else ""
    while True:
        try:
            raw = input(f"\n  {_c('?', C.B_CYAN)} {prompt} ({min_val}–{max_val}){default_str}: ").strip()
            if not raw and default is not None:
                return default
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print_warn(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print_warn("Please enter a valid number.")
        except (EOFError, KeyboardInterrupt):
            print()
            return default if default is not None else min_val


# ---------------------------------------------------------------------------
# Survey runner (interactive terminal)
# ---------------------------------------------------------------------------

def _load_survey_json(survey_id: str) -> Optional[Dict[str, Any]]:
    """Load a survey JSON file from the surveys/ directory."""
    # Look relative to this script, then relative to cwd
    candidates = [
        _HERE.parent / "surveys" / f"{survey_id}.json",
        Path.cwd() / "surveys" / f"{survey_id}.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (json.JSONDecodeError, OSError):
                pass
    return None


def _run_survey_interactive(
    survey_data: Dict[str, Any],
    lang: str = "en",
) -> Dict[str, Any]:
    """
    Run a survey interactively in the terminal.
    Returns dict of {question_id: response}.
    """
    meta = survey_data.get("_meta", {})
    questions = survey_data.get("questions", [])
    lang_suffix = f"_{lang}"

    title_key = f"title{lang_suffix}"
    title = meta.get(title_key, meta.get("title_en", "Survey"))
    print_header(title)

    est = meta.get("estimated_minutes")
    if est:
        print_info(f"Estimated time: ~{est} minutes")
    print()

    responses: Dict[str, Any] = {}
    current_section = None

    for q in questions:
        qid = q.get("id", "")
        section = q.get("section", "")
        qtype = q.get("type", "")
        text_key = f"text{lang_suffix}"
        text = q.get(text_key, q.get("text_en", f"Question {qid}"))
        required = q.get("required", False)

        # Print section header when section changes
        if section != current_section:
            current_section = section
            section_label = section.replace("_", " ").title()
            print(f"\n  {_c('[ ' + section_label + ' ]', C.BOLD, C.B_BLUE)}\n")

        print(f"  {_c(qid, C.DIM, C.BOLD)} {_c(text, C.WHITE)}")

        if qtype == "single_choice":
            options_key = f"options{lang_suffix}"
            options = q.get(options_key, q.get("options_en", []))
            for i, opt in enumerate(options, 1):
                print(f"     {_c(str(i), C.CYAN)}. {opt}")
            choice = ask_int(f"Select option", 1, len(options))
            responses[qid] = {"index": choice, "value": options[choice - 1]}

        elif qtype == "multi_choice":
            options_key = f"options{lang_suffix}"
            options = q.get(options_key, q.get("options_en", []))
            for i, opt in enumerate(options, 1):
                print(f"     {_c(str(i), C.CYAN)}. {opt}")
            raw = ask(f"Select (comma-separated, e.g. 1,3,5)")
            selected_indices = []
            selected_values = []
            for part in raw.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(options):
                        selected_indices.append(idx)
                        selected_values.append(options[idx - 1])
            responses[qid] = {
                "indices": selected_indices,
                "values": selected_values,
            }

        elif qtype in ("likert_5", "likert_7"):
            scale_key = f"scale{lang_suffix}"
            scale = q.get(scale_key, q.get("scale_en", []))
            max_val = len(scale) if scale else (5 if qtype == "likert_5" else 7)
            if scale:
                for i, label in enumerate(scale, 1):
                    print(f"     {_c(str(i), C.CYAN)} = {label}")
            choice = ask_int("Your rating", 1, max_val)
            responses[qid] = {
                "value": choice,
                "label": scale[choice - 1] if scale and choice <= len(scale) else str(choice),
            }

        elif qtype == "numeric":
            min_val = q.get("min", 0)
            max_val = q.get("max", 100)
            val = ask_int("Enter number", min_val, max_val)
            responses[qid] = {"value": val}

        elif qtype == "open_text":
            max_words = q.get("max_words", 500)
            print_info(f"  (max ~{max_words} words, press Enter twice when done)")
            lines = []
            try:
                while True:
                    line = input("  > ")
                    if line == "" and lines and lines[-1] == "":
                        break
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                pass
            text_response = "\n".join(lines).strip()
            responses[qid] = {"value": text_response}

        else:
            # Unknown type — free text fallback
            val = ask(f"Response")
            responses[qid] = {"value": val}

    return responses


# ---------------------------------------------------------------------------
# Command: status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_header("Status")
        print_warn("PRAXIS not initialized in this directory (or any parent).")
        print_info("Run the installer (install.sh / install.ps1) to get started.")
        print_info("Or: python praxis_cli.py init")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    entries = load_all_metrics(praxis_dir)
    gov_events = load_governance_events(praxis_dir)
    summary = compute_summary(entries)

    phase = state["phase"]
    phase_color = C.B_GREEN if phase == "B" else C.B_YELLOW
    phase_label = (
        f"B (PRAXIS ACTIVE)" if phase == "B" else "A (Baseline)"
    )

    print_header("Status")
    print_field("Participant ID",   state["participant_id"], C.B_CYAN)
    print_field("Phase",            _c(phase_label, phase_color))
    print_field("Kit version",      state.get("kit_version", "?"))
    print_field("Installed",        _fmt_date(state.get("installed_at", "")))
    if state.get("activated_at"):
        print_field("Activated (B)", _fmt_date(state["activated_at"]))

    print()
    print(f"  {_c('Metrics', C.BOLD)}")
    print_field("Total entries",    str(summary["total_entries"]))
    print_field("Phase A entries",  str(summary["phase_a_count"]))
    print_field("Phase B entries",  str(summary["phase_b_count"]))
    print_field("Total time logged",f"{summary['total_duration_minutes']} min")

    if summary["total_entries"] > 0:
        print()
        print(f"  {_c('Averages', C.BOLD)}")
        if summary["mean_quality"] is not None:
            _bar = _quality_bar(summary["mean_quality"])
            print_field("Mean quality",   f"{summary['mean_quality']}/5 {_bar}")
        if summary["mean_iterations"] is not None:
            print_field("Mean iterations", str(summary["mean_iterations"]))
        if summary["autonomy_rate"] is not None:
            pct = round(summary["autonomy_rate"] * 100)
            ar_color = C.B_GREEN if pct >= 80 else C.B_YELLOW
            print_field("Autonomy rate",  _c(f"{pct}%", ar_color))
        if summary["mean_duration"] is not None:
            print_field("Mean duration",  f"{summary['mean_duration']} min")
        if summary["praxis_q_mean"] is not None:
            print_field("Mean PRAXIS-Q",  f"{summary['praxis_q_mean']}/3")

    if phase == "B" and gov_events:
        print()
        print_field("Governance events", str(len(gov_events)))

    print()
    print(f"  {_c('Data location', C.DIM)} {praxis_dir}")

    if phase == "A":
        days_data = _days_of_data(entries)
        print()
        if days_data >= 7:
            print_ok(f"{days_data} days of baseline data. Ready to activate PRAXIS.")
            print_info("Run: praxis activate")
        else:
            remaining = 7 - days_data
            print_warn(f"{days_data}/7 days of baseline data collected.")
            print_info(f"Keep logging for ~{remaining} more day(s), then run: praxis activate")

    return 0


# ---------------------------------------------------------------------------
# Command: log
# ---------------------------------------------------------------------------

def cmd_log(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    # Interactive mode if task not provided
    task = args.task
    if not task:
        print_header("Log Task")
        task = ask("What did you accomplish?")
        if not task:
            print_err("Task description is required.")
            return 1

    # Get duration
    duration = getattr(args, "duration", None)
    if duration is None:
        try:
            duration = int(ask("Duration (minutes)", "30"))
        except ValueError:
            duration = 30

    # Get model
    model = getattr(args, "model", None) or ""
    if not model:
        model = ask("AI model/tool used", "claude")

    # Get quality
    quality = getattr(args, "quality", None)
    if quality is None:
        quality = ask_int("Output quality (1=poor, 3=ok, 5=excellent)", 1, 5, 3)

    # Get iterations
    iterations = getattr(args, "iterations", None)
    if iterations is None:
        iterations = ask_int("AI generation cycles (1=first try worked)", 1, 20, 1)

    # Get interventions
    interventions = getattr(args, "interventions", None)
    if interventions is None:
        interventions = ask_int("Human corrections/overrides", 0, 50, 0)

    # Phase B extras
    layer = getattr(args, "layer", None)
    praxis_q = None

    if state["phase"] == "B":
        if not layer:
            print()
            print_info("PRAXIS layer (L1=Governance, L2=Orchestration, L3=Execution, L4=Memory, L5=Production)")
            layer_input = ask("Layer (L1-L5, or skip)", "")
            if layer_input.upper() in VALID_LAYERS:
                layer = layer_input.upper()

        # PRAXIS-Q prompt
        if ask_yn("Rate this task with PRAXIS-Q? (<15 seconds)", True):
            praxis_q = _collect_praxis_q(lang=getattr(args, "lang", "en"))

    notes = getattr(args, "notes", None)

    try:
        entry = build_metric_entry(
            state=state,
            task=task,
            duration=duration,
            model=model,
            quality=quality,
            iterations=iterations,
            interventions=interventions,
            layer=layer,
            praxis_q=praxis_q,
            project=getattr(args, "project", None),
            notes=notes,
        )
        append_metric_entry(praxis_dir, entry)
    except (PraxisError, ValidationError) as exc:
        print_err(str(exc))
        return 1

    print()
    print_ok(f"Logged: {_c(task[:60], C.WHITE)}")
    print_info(f"Duration: {duration} min | Model: {model} | Quality: {quality}/5")
    if entry.get("autonomous"):
        print_ok("Autonomous (zero interventions)")
    if praxis_q:
        total = entry["praxis_q"]["total"]
        zone_color = C.B_GREEN if total >= 2.4 else (C.B_YELLOW if total >= 1.7 else C.B_RED)
        print_info(f"PRAXIS-Q: {_c(str(total), zone_color)}/3.0")

    # Phase A progress reminder
    if state["phase"] == "A":
        all_entries = load_all_metrics(praxis_dir)
        days = _days_of_data(all_entries)
        remaining = max(0, 7 - days)
        if remaining > 0:
            print()
            print_info(f"Phase A: {len(all_entries)} entries | {days}/7 days | {remaining} days until activation-ready")

    return 0


def _collect_praxis_q(lang: str = "en") -> Dict[str, int]:
    """Interactive PRAXIS-Q collection. Returns dict of scores."""
    dims = [
        ("completeness", "Completeness — How complete is the work?",
         "Completitud — ¿Qué tan completo está el trabajo?"),
        ("quality",      "Quality — Quality of the output?",
         "Calidad — ¿Cuál es la calidad del trabajo?"),
        ("coherence",    "Coherence — How well does it fit the project?",
         "Coherencia — ¿Se integra bien con el proyecto?"),
        ("efficiency",   "Efficiency — How efficient was the process?",
         "Eficiencia — ¿Qué tan eficiente fue el proceso?"),
        ("traceability", "Traceability — Can you explain how it was made?",
         "Trazabilidad — ¿Puede explicar cómo se produjo?"),
    ]
    labels_en = ["1=Needs work", "2=Acceptable", "3=Excellent"]
    labels_es = ["1=Necesita trabajo", "2=Aceptable", "3=Excelente"]
    labels = labels_es if lang == "es" else labels_en

    print()
    print(f"  {_c('PRAXIS-Q', C.BOLD, C.B_MAGENTA)}  {_c(' | '.join(labels), C.DIM)}")

    scores: Dict[str, int] = {}
    for dim_id, prompt_en, prompt_es in dims:
        prompt = prompt_es if lang == "es" else prompt_en
        scores[dim_id] = ask_int(f"  {prompt}", 1, 3, 2)

    return scores


# ---------------------------------------------------------------------------
# Command: activate
# ---------------------------------------------------------------------------

def cmd_activate(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    if state["phase"] == "B":
        print_warn("PRAXIS is already activated (Phase B).")
        return 0

    print_header("Activate PRAXIS Governance")
    print()
    print_info("This will transition you from Phase A (baseline) to Phase B (PRAXIS governance).")
    print_info("This action cannot be undone.")
    print()

    # Consent reminder
    print(f"  {_c('Consent reminder:', C.BOLD)}")
    print_info("By activating, you continue to consent to data collection for")
    print_info("PhD research at Universidad Complutense de Madrid.")
    print_info("You can withdraw at any time with: praxis withdraw")
    print()

    if not ask_yn("Proceed with activation?", True):
        print_info("Activation cancelled.")
        return 0

    force = getattr(args, "force", False)
    try:
        updated_state, warnings = activate_phase_b(praxis_dir, state, force=force)
    except (PraxisError, InvalidPhaseError) as exc:
        print_err(str(exc))
        return 1

    if warnings:
        for w in warnings:
            print_warn(w)
        if not force:
            print_info("Run with --force to override minimum data requirements.")
            return 0

    print()
    print_ok("PRAXIS activated. Phase B has begun.")
    print()

    # Inject governance files
    _inject_governance(praxis_dir, updated_state)

    print()
    print_ok("Your AI systems now have governance structure.")
    print_info("New commands available:")
    print_info("  praxis govern 'Added rule: ...'  — log a governance event")
    print_info("  praxis log                       — PRAXIS-Q will be prompted automatically")
    print_info("  praxis survey post               — post-survey (after Phase B ends)")

    return 0


def _inject_governance(praxis_dir: Path, state: Dict[str, Any]) -> None:
    """
    Inject governance templates for all detected platforms.
    Handles both function-based adapters (legacy) and class-based adapters
    (new, inherit from base.PraxisAdapter).
    """
    templates_dir = _HERE.parent / "templates" / "governance"
    workspace_dir = praxis_dir.parent  # project root

    detected = detect_platforms(workspace_dir)
    if not detected:
        detected = ["generic"]

    print()
    print(f"  {_c('Detected platforms:', C.BOLD)} {', '.join(detected)}")
    print()

    for platform_id in detected:
        try:
            files = _call_inject_governance(platform_id, templates_dir, workspace_dir)
            if files:
                for f in files:
                    print_ok(f"Injected \u2192 {f}")
                platforms = state.get("platform_ids", [])
                if platform_id not in platforms:
                    platforms.append(platform_id)
                state["platform_ids"] = platforms
                save_state(praxis_dir, state)
            else:
                print_info(f"{platform_id}: governance already present or no files to inject")
        except Exception as exc:
            print_warn(f"Could not inject for {platform_id}: {exc}")


def _call_inject_governance(
    platform_id: str,
    templates_dir: Path,
    workspace_dir: Path,
) -> List[str]:
    """
    Load an adapter by platform_id and call inject_governance.
    Uses the adapters package ADAPTER_MAP for O(1) class lookup.
    Falls back to dynamic module loading if package import fails.
    """
    import importlib
    import sys

    kit_root = str(_HERE.parent)
    if kit_root not in sys.path:
        sys.path.insert(0, kit_root)

    # Fast path: use pre-built ADAPTER_MAP from adapters/__init__.py
    try:
        adapters_pkg = importlib.import_module("adapters")
        adapter_map = getattr(adapters_pkg, "ADAPTER_MAP", {})
        if platform_id in adapter_map:
            adapter_cls = adapter_map[platform_id]
            instance = adapter_cls()
            return instance.inject_governance(templates_dir, workspace_dir)
    except (ImportError, Exception):
        pass

    # Slow path: dynamic module load (handles stale sys.modules gracefully)
    try:
        import inspect
        module_name = f"adapters.{platform_id}"
        if module_name in sys.modules:
            del sys.modules[module_name]
        module = importlib.import_module(module_name)

        # Try class-based adapter
        try:
            base_module = importlib.import_module("adapters.base")
            PraxisAdapterClass = getattr(base_module, "PraxisAdapter", None)
            if PraxisAdapterClass is not None:
                for _name, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj is not PraxisAdapterClass
                            and issubclass(obj, PraxisAdapterClass)
                            and hasattr(obj, "inject_governance")):
                        return obj().inject_governance(templates_dir, workspace_dir)
        except Exception:
            pass

        # Legacy function-based adapter
        inject_fn = getattr(module, "inject_governance", None)
        if callable(inject_fn):
            return inject_fn(templates_dir)
    except Exception:
        pass

    return []


def _load_adapter(platform_id: str) -> Optional[Any]:
    """Dynamically load an adapter module (legacy — use _call_inject_governance instead)."""
    import importlib.util
    adapter_path = _HERE.parent / "adapters" / f"{platform_id}.py"
    if not adapter_path.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(platform_id, adapter_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        return module
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Command: govern
# ---------------------------------------------------------------------------

def cmd_govern(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    description = " ".join(args.description) if isinstance(args.description, list) else args.description
    if not description:
        print_header("Log Governance Event")
        description = ask("Describe the governance event")
        if not description:
            print_err("Description is required.")
            return 1

    event_type = getattr(args, "type", "rule_created") or "rule_created"

    try:
        event = append_governance_event(praxis_dir, event_type, description, state)
    except (PraxisError, InvalidPhaseError, ValidationError) as exc:
        print_err(str(exc))
        return 1

    print()
    print_ok(f"Governance event logged: {_c(event_type, C.B_MAGENTA)}")
    print_info(f"  {description[:80]}")
    print_info(f"  ID: {event['id']}")
    return 0


def cmd_incident(args: argparse.Namespace) -> int:
    """Log a governance emergence incident with structured capture."""
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    description = " ".join(args.description) if isinstance(args.description, list) else args.description
    if not description:
        print_header("Log Governance Emergence Incident")
        description = ask("What happened? (describe the incident)")
        if not description:
            print_err("Description is required.")
            return 1

    print_info("Root cause analysis (optional, press Enter to skip):")
    root_cause = ask("  What caused this?")

    print_info("New rule proposal (optional, press Enter to skip):")
    new_rule = ask("  What rule should prevent this?")

    # Build incident entry
    incident = {
        "id": generate_participant_id()[:8] + "-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "incident",
        "incident": description,
        "root_cause": root_cause or None,
        "new_rule_proposed": new_rule or None,
        "rule_integrated": False,
        "phase": state.get("phase", "unknown"),
    }

    # Append to governance events file
    gov_file = praxis_dir / "governance_events.jsonl"
    with open(gov_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(incident, ensure_ascii=False) + "\n")

    print()
    print_ok(f"Incident logged: {_c('incident', C.B_RED)}")
    print_info(f"  What happened: {description[:80]}")
    if root_cause:
        print_info(f"  Root cause:    {root_cause[:80]}")
    if new_rule:
        print_info(f"  New rule:      {new_rule[:80]}")
    print_info(f"  ID: {incident['id']}")
    print()
    print_info("Use 'praxis govern \"rule text\"' once the rule is formally integrated.")
    return 0


# ---------------------------------------------------------------------------
# Command: survey
# ---------------------------------------------------------------------------

def cmd_survey(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    survey_type = getattr(args, "type", "pre")
    lang = getattr(args, "lang", "en")

    if survey_type == "pre":
        survey_id = "pre_survey"
        if state.get("pre_survey_completed"):
            if not ask_yn("Pre-survey already completed. Take it again?", False):
                return 0
    elif survey_type == "post":
        survey_id = "post_survey"
        if state["phase"] != "B":
            print_warn("Post-survey is intended for Phase B participants.")
            print_info("Complete Phase A and activate PRAXIS first, then return.")
            if not ask_yn("Take post-survey anyway?", False):
                return 0
    else:
        print_err(f"Unknown survey type: '{survey_type}'. Use 'pre' or 'post'.")
        return 1

    survey_data = _load_survey_json(survey_id)
    if survey_data is None:
        print_err(f"Survey file not found: {survey_id}.json")
        print_info("Make sure you're running from the PRAXIS kit directory.")
        return 1

    try:
        responses = _run_survey_interactive(survey_data, lang=lang)
        survey_path = save_survey_response(praxis_dir, survey_id, responses, state)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    # Update state flags
    if survey_type == "pre":
        state["pre_survey_completed"] = True
    elif survey_type == "post":
        state["post_survey_completed"] = True
    save_state(praxis_dir, state)

    print()
    print_ok("Survey completed. Thank you!")
    print_info(f"Saved to: {survey_path.name}")

    if survey_type == "pre" and state["phase"] == "A":
        print()
        print_info("Next step: start using your AI tools naturally and log tasks with:")
        print_info("  praxis log 'What you accomplished' -d <minutes> -m <model> -q <1-5>")

    return 0


# ---------------------------------------------------------------------------
# Command: export
# ---------------------------------------------------------------------------

def cmd_export(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    # Delegate to export/anonymize.py
    anonymize_path = _HERE.parent / "export" / "anonymize.py"
    if not anonymize_path.is_file():
        print_err("Export module not found. Ensure the kit is fully installed.")
        return 1

    import importlib.util
    spec = importlib.util.spec_from_file_location("anonymize", anonymize_path)
    if spec is None or spec.loader is None:
        print_err("Could not load export module.")
        return 1

    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore
        output_path = module.export_participant_zip(
            praxis_dir=praxis_dir,
            redact_tasks=getattr(args, "redact_tasks", False),
            output_dir=Path(getattr(args, "output", None) or Path.cwd()),
        )
        print()
        print_ok(f"Export complete: {_c(str(output_path), C.B_CYAN)}")
        print_info("Send this ZIP to the researcher. It contains only anonymous metrics.")
    except Exception as exc:
        print_err(f"Export failed: {exc}")
        return 1

    return 0


# ---------------------------------------------------------------------------
# Command: platforms
# ---------------------------------------------------------------------------

def cmd_platforms(args: argparse.Namespace) -> int:
    print_header("Detected AI Platforms")

    detected = detect_platforms()

    if not detected:
        print_warn("No AI platforms detected in this directory.")
        print_info("PRAXIS will use the generic adapter (plain markdown).")
        return 0

    # Load platform info from config
    config_path = _HERE.parent / "config" / "platforms.json"
    platform_info: Dict[str, Any] = {}
    if config_path.is_file():
        try:
            with config_path.open("r", encoding="utf-8") as fh:
                cfg = json.load(fh)
            for p in cfg.get("platforms", []):
                platform_info[p["id"]] = p
        except Exception:
            pass

    print()
    tier_labels = {1: "Deep", 2: "Medium", 3: "Light", 4: "Generic"}
    for pid in detected:
        info = platform_info.get(pid, {})
        name = info.get("name", pid)
        tier = info.get("tier", "?")
        tier_label = tier_labels.get(tier, str(tier))
        tier_color = {1: C.B_GREEN, 2: C.B_CYAN, 3: C.B_YELLOW, 4: C.DIM}.get(tier, "")
        gov_files = info.get("governance_files", {})
        primary = gov_files.get("primary", "—")

        print(f"  {_c('●', C.B_GREEN)} {_c(name, C.BOLD)}")
        print_info(f"Tier {tier} ({_c(tier_label, tier_color)}) | Governance file: {primary}")

    print()
    not_detected = [
        pid for pid in platform_info
        if pid not in detected and pid != "generic"
    ]
    if not_detected:
        print(f"  {_c('Not detected:', C.DIM)} {', '.join(not_detected)}")

    return 0


# ---------------------------------------------------------------------------
# Command: withdraw
# ---------------------------------------------------------------------------

def cmd_withdraw(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Nothing to withdraw.")
        return 0

    print_header("Withdraw from Study")
    print()
    print_warn("This will permanently delete ALL collected data:")
    print_info("  - metrics.jsonl (all logged tasks)")
    print_info("  - governance.jsonl (all governance events)")
    print_info("  - survey responses")
    print_info("  - state.json")
    print()
    print_warn("This action CANNOT be undone.")
    print()

    confirm = ask("Type 'withdraw' to confirm, or press Enter to cancel", "")
    if confirm.lower() != "withdraw":
        print_info("Withdrawal cancelled. Your data is safe.")
        return 0

    deleted = withdraw_participant(praxis_dir)
    print()
    print_ok("All PRAXIS data has been deleted.")
    for path in deleted:
        print_info(f"  Deleted: {path}")
    print()
    print_info("You have been withdrawn from the study. Thank you for participating.")
    return 0


# ---------------------------------------------------------------------------
# Command: init (first-time setup, called by installer)
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> int:
    project_dir = Path(getattr(args, "dir", None) or Path.cwd()).resolve()
    praxis_dir = get_or_create_praxis_dir(project_dir)

    # Check if already initialized
    if (praxis_dir / "state.json").is_file():
        print_warn("PRAXIS already initialized. Use 'praxis status' to check.")
        return 0

    print_header("PRAXIS Kit Setup")
    print()
    print_info("Setting up PRAXIS research kit...")
    print_info("This will create a .praxis/ directory in your project.")
    print()

    # Consent
    consent_path = _HERE.parent / "CONSENT.md"
    if consent_path.is_file():
        lang = getattr(args, "lang", "en")
        if lang == "es":
            consent_path_es = _HERE.parent / "CONSENTIMIENTO.md"
            if consent_path_es.is_file():
                consent_path = consent_path_es

        print(f"  {_c('Please read the consent form at:', C.BOLD)}")
        print(f"  {consent_path}")
        print()

    consent = ask_yn("Do you consent to participate in this research?", False)
    if not consent:
        print_warn("Consent required to participate. Exiting.")
        print_info("Read CONSENT.md for full details about the research.")
        return 1

    participant_id = generate_participant_id()
    print()
    print_ok(f"Participant ID assigned: {_c(participant_id, C.B_CYAN)}")
    print_info("Keep this ID — it identifies your anonymous dataset.")

    try:
        state = initialize_state(praxis_dir, participant_id, consent_given=True)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    # Create empty metrics file
    metrics_path = praxis_dir / METRICS_FILE
    if not metrics_path.is_file():
        metrics_path.touch()

    # Create baseline METRICS.md in project root
    baseline_metrics = _HERE.parent / "templates" / "baseline" / "METRICS.md"
    dest_metrics = project_dir / "METRICS.md"
    if baseline_metrics.is_file() and not dest_metrics.is_file():
        import shutil
        shutil.copy2(str(baseline_metrics), str(dest_metrics))
        print_ok(f"Created METRICS.md in your project")

    print()
    print_ok("PRAXIS initialized successfully.")
    print()
    print(f"  {_c('Next steps:', C.BOLD)}")
    print_info("1. Complete the pre-survey:  praxis survey pre")
    print_info("2. Log your AI tasks daily:  praxis log 'what you did' -d <min> -m <model>")
    print_info("3. After 7+ days, activate:  praxis activate")
    print_info("4. Check your progress:      praxis status")
    print()
    print_info(f"Data stored in: {praxis_dir}")

    return 0


# ---------------------------------------------------------------------------
# Helper formatting functions
# ---------------------------------------------------------------------------

def _fmt_date(iso_str: str) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return iso_str


def _quality_bar(quality: float) -> str:
    """Render a small bar for quality score 1-5."""
    filled = round(quality)
    bar = "█" * filled + "░" * (5 - filled)
    if filled >= 4:
        color = C.B_GREEN
    elif filled >= 3:
        color = C.B_YELLOW
    else:
        color = C.B_RED
    return _c(bar, color)


def _days_of_data(entries: List[Dict[str, Any]]) -> int:
    """Calculate unique days with Phase A data."""
    dates = set()
    for e in entries:
        if e.get("phase") == "A":
            ts = e.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                dates.add(dt.date())
            except (ValueError, TypeError):
                pass
    return len(dates)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="praxis",
        description=textwrap.dedent("""\
            PRAXIS Universal Kit — AI workflow research tool.
            Collects metrics for before/after PRAXIS governance comparison.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              praxis status
              praxis log "Built auth module" -d 45 -m claude -q 4 -i 2 -h 1
              praxis activate
              praxis govern "Added rule: always test after deploy"
              praxis survey pre
              praxis survey post --lang es
              praxis export
              praxis platforms
              praxis withdraw
        """),
    )
    parser.add_argument("--version", action="version", version="PRAXIS Kit 0.1")
    parser.add_argument("--lang", choices=["en", "es"], default="en",
                        help="Language for interactive prompts (default: en)")

    sub = parser.add_subparsers(dest="command", metavar="command")

    # status
    p_status = sub.add_parser("status", help="Show current phase, days active, metrics count")

    # log
    p_log = sub.add_parser("log", help="Log a task/sprint with metrics")
    p_log.add_argument("task", nargs="?", default="",
                       help="Task description (interactive if omitted)")
    p_log.add_argument("-d", "--duration", type=int, metavar="MIN",
                       help="Duration in minutes")
    p_log.add_argument("-m", "--model", type=str, metavar="MODEL",
                       help="AI model used (e.g. claude, gpt-4o, copilot)")
    p_log.add_argument("-q", "--quality", type=int, choices=range(1, 6),
                       metavar="1-5", help="Self-rated output quality")
    p_log.add_argument("-i", "--iterations", type=int, metavar="N",
                       help="AI generation cycles (1=first try worked)")
    p_log.add_argument("-h2", "--interventions", type=int, dest="interventions", metavar="N",
                       help="Human corrections/overrides")
    p_log.add_argument("-l", "--layer", choices=list(VALID_LAYERS), metavar="L1-L5",
                       help="PRAXIS layer (Phase B only)")
    p_log.add_argument("-p", "--project", type=str, help="Project name")
    p_log.add_argument("-n", "--notes", type=str, help="Optional notes")

    # activate
    p_act = sub.add_parser("activate", help="Transition from Phase A to Phase B")
    p_act.add_argument("--force", action="store_true",
                       help="Override minimum data requirements")

    # govern
    p_gov = sub.add_parser("govern", help="Log a governance event (Phase B)")
    p_gov.add_argument("description", nargs="*",
                       help="Governance event description")
    p_gov.add_argument("-t", "--type",
                       choices=list(VALID_GOVERNANCE_TYPES),
                       default="rule_created",
                       help="Event type (default: rule_created)")

    # incident
    p_inc = sub.add_parser("incident", help="Log a governance emergence incident")
    p_inc.add_argument("description", nargs="*",
                       help="What happened (the incident)")

    # survey
    p_surv = sub.add_parser("survey", help="Launch pre or post survey")
    p_surv.add_argument("type", choices=["pre", "post"],
                        help="Survey to run")
    p_surv.add_argument("--lang", choices=["en", "es"], default="en",
                        help="Language for survey questions")

    # export
    p_exp = sub.add_parser("export", help="Generate anonymized data ZIP for researcher")
    p_exp.add_argument("--redact-tasks", action="store_true",
                       help="Replace task descriptions with [REDACTED]")
    p_exp.add_argument("-o", "--output", type=str, metavar="DIR",
                       help="Output directory (default: current directory)")

    # platforms
    p_plat = sub.add_parser("platforms", help="Show detected AI platforms")

    # withdraw
    p_with = sub.add_parser("withdraw", help="Delete all collected data and withdraw from study")

    # init (usually called by installer, not directly)
    p_init = sub.add_parser("init", help="Initialize PRAXIS in current directory")
    p_init.add_argument("--dir", type=str, help="Project directory (default: cwd)")
    p_init.add_argument("--lang", choices=["en", "es"], default="en")

    return parser


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "status":    cmd_status,
    "log":       cmd_log,
    "activate":  cmd_activate,
    "govern":    cmd_govern,
    "incident":  cmd_incident,
    "survey":    cmd_survey,
    "export":    cmd_export,
    "platforms": cmd_platforms,
    "withdraw":  cmd_withdraw,
    "init":      cmd_init,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    handler = COMMAND_MAP.get(args.command)
    if handler is None:
        print_err(f"Unknown command: '{args.command}'")
        parser.print_help()
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print("\n\n  Cancelled.")
        return 130
    except Exception as exc:
        print_err(f"Unexpected error: {exc}")
        if os.environ.get("PRAXIS_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
