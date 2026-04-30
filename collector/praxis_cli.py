#!/usr/bin/env python3
"""
PRAXIS Universal Kit — CLI Entry Point
=======================================
Commands: status, log, diagnose, activate, govern, survey, export, submit, platforms, withdraw

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
    VALID_GOVERNANCE_TAGS,
    VALID_GOVERNANCE_TYPES,
    VALID_INCIDENT_CATEGORIES,
    VALID_ITERATION_TYPES,
    VALID_LAYERS,
    PraxisError,
    StateNotFoundError,
    ValidationError,
    append_incident_event,
    append_governance_event,
    append_metric_entry,
    apply_smart_checkout,
    build_auto_session_entry,
    build_metric_entry,
    compute_summary,
    detect_platforms,
    estimate_reliability,
    find_praxis_dir,
    generate_participant_id,
    get_open_session_record,
    get_or_create_praxis_dir,
    initialize_state,
    load_all_metrics,
    load_governance_events,
    load_session_records,
    load_state,
    load_survey_responses,
    get_session_checkout_context,
    save_state,
    save_survey_response,
    start_passive_session,
    finish_passive_session,
    touch_last_active,
    update_metric_entry,
    withdraw_participant,
)
from diagnostics import build_user_diagnosis

_EXPORT_DIR = _HERE.parent / "export"
sys.path.insert(0, str(_EXPORT_DIR))
from anonymize import export_participant_zip
from submission import get_submission_status, submit_export, submission_setup_template


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
    B_MAGENTA = "\033[95m" if _COLOR else ""
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


def ask_choice(prompt: str, options: List[Tuple[str, str]], default: Optional[str] = None) -> str:
    """Prompt for a single choice from a list of (key, label)."""
    option_map = {str(key).strip().lower(): label for key, label in options}
    while True:
        print()
        print(f"  {_c(prompt, C.BOLD)}")
        for key, label in options:
            marker = " (default)" if default and key == default else ""
            print(f"    {_c(str(key), C.B_CYAN)} {label}{marker}")
        try:
            raw = input(f"\n  {_c('?', C.B_CYAN)} Choose: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return default or options[0][0]
        if not raw and default is not None:
            return default
        if raw in option_map:
            return raw
        print_warn("Please choose one of the listed options.")


def _latest_unreviewed_entry(praxis_dir: Path) -> Optional[Dict[str, Any]]:
    entries = load_all_metrics(praxis_dir)
    for entry in reversed(entries):
        if entry.get("type", "sprint") == "sprint" and not entry.get("reviewed", True):
            return entry
    return None


def _write_checkout(praxis_dir: Path, entry: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    if any(getattr(args, name, None) is not None for name in ("quality", "rework", "trust", "model")) or getattr(args, "corrected", False):
        return _write_checkout_legacy(praxis_dir, entry, args)

    context = get_session_checkout_context(entry)
    print()
    print(f"  {_c('═══ Micro Checkout ═══', C.BOLD)}")
    print()
    print_info(
        f"Session: {context.get('started', '?')} → {context.get('ended', '?')} "
        f"({context.get('duration_minutes', 0)} min)"
    )
    print_info(f"Platform: {context.get('platform_label', 'Unknown')}")
    print_info(f"Git: {context.get('git_label', 'No repo detected')}")

    outcome = ask_choice(
        "What happened?",
        [
            ("1", "✅ Solved — moved on"),
            ("2", "⚠️ Partially — accepted a compromise"),
            ("3", "❌ Abandoned — gave up or switched approach"),
        ],
        default="1",
    )
    outcome_map = {"1": "solved", "2": "partial", "3": "abandoned"}

    governance = ask_choice(
        "Governance moment? (optional)",
        [
            ("1", "🔄 Context loss — had to repeat/re-explain"),
            ("2", "👤 Overrode the AI"),
            ("3", "🤔 AI went off track"),
            ("4", "📏 Scope creep — task expanded"),
            ("5", "🔀 Model switch — changed tool mid-session"),
            ("0", "🚫 None"),
        ],
        default="0",
    )
    governance_map = {
        "1": "context_loss",
        "2": "override",
        "3": "ai_off_track",
        "4": "scope_creep",
        "5": "model_switch",
        "0": "none",
    }
    task = getattr(args, "task", None) or ask("1-line task summary (optional)", "")
    updated = apply_smart_checkout(
        entry,
        outcome=outcome_map.get(outcome, "solved"),
        governance_tag=governance_map.get(governance, "none"),
        task=task,
    )
    saved = update_metric_entry(praxis_dir, str(entry.get("id")), updated)
    if saved is None:
        raise PraxisError("Could not update the selected session draft.")
    return saved


def _write_checkout_legacy(praxis_dir: Path, entry: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    task = getattr(args, "task", None) or ask("Short task summary", "")
    if not task:
        task = "Reviewed auto-captured session"
    quality = getattr(args, "quality", None)
    if quality is None:
        quality = ask_int("Overall usefulness / quality", 1, 5, 3)
    rework = getattr(args, "rework", None) or ask("Rework level (low/med/high)", "med")
    rework = str(rework).strip().lower()
    rework_map = {"low": 1, "med": 2, "medium": 2, "high": 4}
    iterations = rework_map.get(rework, 2)
    corrected = getattr(args, "corrected", None)
    if corrected is None:
        corrected = ask_yn("Did you have to heavily correct or override the AI?", False)
    trust = getattr(args, "trust", None)
    if trust is None:
        trust = ask_int("How much would you trust this output without verifying?", 1, 7, 4)
    model = getattr(args, "model", None) or ask("Model/tool if known (optional)", entry.get("model", "unknown"))

    provenance = dict(entry.get("field_provenance") or {})
    provenance.update({
        "task": "manual_micro_checkout",
        "quality": "manual_micro_checkout",
        "interventions": "manual_micro_checkout",
        "trust": "manual_micro_checkout",
    })
    if model and model != "unknown":
        provenance["model"] = "manual_micro_checkout"

    l1r = dict(entry.get("l1r_observations") or {})
    l1r["trust_willingness"] = trust
    l1r["skepticism_activation"] = max(1, 8 - trust)

    updated = dict(entry)
    updated.update({
        "task": task,
        "quality_self": quality,
        "quality": quality,
        "iterations": iterations,
        "first_attempt": iterations == 1,
        "human_interventions": 1 if corrected else 0,
        "interventions": 1 if corrected else 0,
        "autonomous": not corrected,
        "model": model or entry.get("model", "unknown"),
        "model_executor": model or entry.get("model_executor", "unknown"),
        "reviewed": True,
        "capture_mode": "micro_checkout",
        "checkout_rework_level": rework,
        "l1r_observations": l1r,
        "field_provenance": provenance,
    })
    updated["reliability_score"] = estimate_reliability(updated)
    saved = update_metric_entry(praxis_dir, str(entry.get("id")), updated)
    if saved is None:
        raise PraxisError("Could not update the selected session draft.")
    return saved


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
    sessions = load_session_records(praxis_dir)
    open_session = get_open_session_record(praxis_dir)
    summary = compute_summary(entries)

    phase = state.get("phase", "obs")
    phase_label = "Observational (continuous capture)"

    print_header("Status")
    print_field("Participant ID",   state["participant_id"], C.B_CYAN)
    print_field("Mode",            phase_label)
    print_field("Kit version",      state.get("kit_version", "?"))
    print_field("Installed",        _fmt_date(state.get("installed_at", "")))

    print()
    print(f"  {_c('Metrics', C.BOLD)}")
    print_field("Total entries",    str(summary["total_entries"]))
    print_field("Total sprints",    str(summary.get("total_sprints", 0)))
    print_field("Passive captures", str(len(sessions)))
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
        if summary.get("mean_reliability") is not None:
            print_field("Mean reliability", f"{round(float(summary['mean_reliability']) * 100)}%")

    if phase == "B" and gov_events:
        print()
        print_field("Governance events", str(len(gov_events)))

    print()
    print(f"  {_c('Data location', C.DIM)} {praxis_dir}")

    if open_session is not None:
        print()
        print_ok("Passive capture session is currently open.")
        print_info("Run: praxis stop  → then praxis checkout")

    if phase == "obs":
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


def cmd_diagnose(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    entries = load_all_metrics(praxis_dir)
    governance = load_governance_events(praxis_dir)
    diagnosis = build_user_diagnosis(entries, governance, state)

    print_header("Workflow Diagnosis")
    print_info(diagnosis.get("headline", ""))
    print()
    print_field("Summary", diagnosis.get("summary", ""))

    metrics = diagnosis.get("metrics", {})
    if metrics:
        print()
        print(f"  {_c('Signals', C.BOLD)}")
        if metrics.get("avg_quality") is not None:
            print_field("Avg quality", f"{metrics['avg_quality']}/5")
        if metrics.get("avg_iterations") is not None:
            print_field("Avg iterations", str(metrics["avg_iterations"]))
        if metrics.get("autonomy_rate") is not None:
            print_field("Autonomy rate", f"{round(metrics['autonomy_rate'] * 100)}%")
        if metrics.get("governance_events") is not None:
            print_field("Governance events", str(metrics["governance_events"]))
        if metrics.get("degraded_boundaries") is not None:
            print_field("Degraded boundaries", str(metrics["degraded_boundaries"]))

    insights = diagnosis.get("insights", [])
    if insights:
        print()
        print(f"  {_c('What PRAXIS is showing you', C.BOLD)}")
        for item in insights:
            print(f"  {_c('•', C.B_CYAN)} {item}")

    user_value = diagnosis.get("user_value", [])
    if user_value:
        print()
        print(f"  {_c('What you get back as a participant', C.BOLD)}")
        for item in user_value:
            print(f"  {_c('•', C.B_GREEN)} {item}")

    return 0


def cmd_start(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1
    try:
        state = load_state(praxis_dir)
        record = start_passive_session(praxis_dir, state, praxis_dir.parent)
    except PraxisError as exc:
        print_err(str(exc))
        return 1

    print_header("Passive Capture Started")
    print_ok("Session capture is running.")
    print_info(f"Started: {str(record.get('started_at', ''))[:19].replace('T', ' ')} UTC")
    platforms = record.get("platform_ids", [])
    if platforms:
        print_info(f"Detected platforms: {', '.join(platforms)}")
    print_info("When you finish, run: praxis stop")
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1
    try:
        state = load_state(praxis_dir)
        session = finish_passive_session(praxis_dir, state, praxis_dir.parent)
        if session is None:
            print_warn("No active passive session found.")
            return 0
        entry = build_auto_session_entry(state, session, praxis_dir.parent)
        append_metric_entry(praxis_dir, entry)
        touch_last_active(praxis_dir)
    except (PraxisError, ValidationError) as exc:
        print_err(str(exc))
        return 1

    print_header("Passive Capture Stopped")
    print_ok(f"Draft session captured ({entry.get('duration_minutes')} min).")
    print_info(f"Reliability: {round(float(entry.get('reliability_score', 0)) * 100)}%")
    print_info("Next step: run 'praxis checkout' for a 10-second human calibration.")
    return 0


def cmd_checkout(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    entry = None
    target_id = getattr(args, "id", None)
    if target_id:
        for row in load_all_metrics(praxis_dir):
            if row.get("id") == target_id:
                entry = row
                break
    else:
        entry = _latest_unreviewed_entry(praxis_dir)

    if entry is None:
        print_warn("No unreviewed session draft found.")
        return 0

    print_header("Micro Checkout")
    print_info("This is the lightweight path: keep passive capture, add just enough human calibration to make the data stronger.")
    try:
        saved = _write_checkout(praxis_dir, entry, args)
        touch_last_active(praxis_dir)
    except (PraxisError, ValidationError) as exc:
        print_err(str(exc))
        return 1

    print_ok("Checkout saved.")
    print_info(f"Task: {saved.get('task', '')}")
    print_info(f"Reliability: {round(float(saved.get('reliability_score', 0)) * 100)}%")
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

    # Layer and PRAXIS-Q
    layer = getattr(args, "layer", None)
    praxis_q = None

    if not layer:
        print()
        print_info("PRAXIS layer (L1=Governance, L1-R=Relational, L2=Orchestration, L3=Execution, L4=Memory, L5=Production)")
        layer_input = ask("Layer (L1/L1-R/L2-L5, or skip)", "")
        if layer_input.upper() in VALID_LAYERS:
            layer = layer_input.upper()

    # PRAXIS-Q prompt
    if ask_yn("Rate this task with PRAXIS-Q? (<15 seconds)", True):
        praxis_q = _collect_praxis_q(lang=getattr(args, "lang", "en"))

    l1r_observations = None
    if getattr(args, "l1r", False):
        l1r_observations = _collect_l1r_observations(lang=getattr(args, "lang", "en"))
        if not layer:
            layer = "L1-R"

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
            l1r_observations=l1r_observations,
            iteration_type=getattr(args, "iteration_type", None),
            design_quality=_parse_design_quality(getattr(args, "design_quality", None)),
            reviewer_feedback=_build_reviewer_feedback(
                getattr(args, "reviewer_feedback", None),
                getattr(args, "reviewer_id", None),
                getattr(args, "reviewer_source", None),
            ),
            project=getattr(args, "project", None),
            notes=notes,
        )
        entry["capture_mode"] = "manual"
        entry["reviewed"] = True
        entry["field_provenance"] = {
            "task": "manual",
            "duration": "manual",
            "model": "manual",
            "quality": "manual",
            "interventions": "manual",
        }
        entry["reliability_score"] = estimate_reliability(entry)
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
    if l1r_observations:
        print_info("L1-R observations captured")

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

def _collect_l1r_observations(lang: str = "en") -> Dict[str, Any]:
    """Interactive L1-R relational governance collection."""
    prompts = [
        ("perceived_confidence", "How confident did the AI seem?", "¿Qué tan seguro parecía el AI?"),
        ("perceived_warmth", "How warm/supportive did the AI feel?", "¿Qué tan cálido o colaborativo se sintió el AI?"),
        ("trust_willingness", "Would you follow this AI's advice without verifying?", "¿Seguirías el consejo del AI sin verificarlo?"),
        ("skepticism_activation", "Did you feel the need to verify independently?", "¿Sentiste necesidad de verificar independientemente?"),
        ("perceived_authority", "How expert did the AI seem?", "¿Qué tan experto parecía el AI?"),
    ]

    print()
    print(f"  {_c('L1-R', C.BOLD, C.B_MAGENTA)}  {_c('Relational governance observations | 1=low, 7=high', C.DIM)}")

    observations: Dict[str, Any] = {}
    for field, prompt_en, prompt_es in prompts:
        prompt = prompt_es if lang == "es" else prompt_en
        observations[field] = ask_int(f"  {prompt}", 1, 7, 4)

    observations["compliance_tendency"] = ask_yn(
        "Did you accept the AI output without questioning?", False
    )
    observations["personality_mismatch"] = ask_yn(
        "Did the AI behavior differ from what SOUL_TEMPLATE specified?", False
    )
    if observations["personality_mismatch"]:
        notes = ask("Describe the personality mismatch", "")
        if notes:
            observations["personality_mismatch_notes"] = notes

    return observations


# ---------------------------------------------------------------------------
# Command: activate
# ---------------------------------------------------------------------------

def cmd_activate(args: argparse.Namespace) -> int:
    """No-op: PRAXIS operates in continuous observational mode."""
    print_header("Observation Mode")
    print()
    print_info("PRAXIS operates in continuous observational mode. No activation needed.")
    print_info("Just start working — passive capture runs automatically.")
    print_info("Use 'praxis checkout' to review and tag your session.")
    print_info("Use 'praxis govern' to log a governance event at any time.")
    return 0


def _inject_governance(praxis_dir: Path, state: Dict[str, Any]) -> None:
    """
    Inject governance templates for all detected platforms.
    Handles both function-based adapters (legacy) and class-based adapters
    (new, inherit from base.PraxisAdapter).
    """
    templates_dir = _HERE.parent / "templates"
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
    except (PraxisError, ValidationError) as exc:
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

    category = getattr(args, "category", None)
    if not category:
        print_info(
            "Incident category: OPS=operations, GOV=governance, COM=communication, "
            "PRD=product, RES=research, DES=design."
        )
        category_input = ask("  Category (optional)", "").upper()
        category = category_input or None

    try:
        incident = append_incident_event(
            praxis_dir=praxis_dir,
            state=state,
            description=description,
            category=category,
            root_cause=root_cause or None,
            new_rule=new_rule or None,
        )
    except (PraxisError, ValidationError) as exc:
        print_err(str(exc))
        return 1

    print()
    print_ok(f"Incident logged: {_c('incident', C.B_RED)}")
    if category:
        print_info(f"  Category:      {category}")
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
        # Surveys available at any time in observational mode
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

    if survey_type == "pre":
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

    try:
        output_path = export_participant_zip(
            praxis_dir=praxis_dir,
            redact_tasks=getattr(args, "redact_tasks", False),
            output_dir=Path(getattr(args, "output", None) or Path.cwd()),
        )
        diagnosis = build_user_diagnosis(
            load_all_metrics(praxis_dir),
            load_governance_events(praxis_dir),
            load_state(praxis_dir),
        )
        print()
        print_ok(f"Export complete: {_c(str(output_path), C.B_CYAN)}")
        print_info("This ZIP contains only anonymous metrics — no personal data.")
        print_info(f"Diagnosis: {diagnosis.get('headline', '')}")
        print_info("Run 'praxis submit' to send it automatically when submission is enabled.")
    except Exception as exc:
        print_err(f"Export failed: {exc}")
        return 1

    return 0


def cmd_submit(args: argparse.Namespace) -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print_err("PRAXIS not found. Run from your project directory.")
        return 1

    try:
        state = load_state(praxis_dir)
        zip_path = export_participant_zip(
            praxis_dir=praxis_dir,
            redact_tasks=getattr(args, "redact_tasks", False),
            output_dir=Path(getattr(args, "output", None) or Path.cwd()),
        )
        diagnosis = build_user_diagnosis(
            load_all_metrics(praxis_dir),
            load_governance_events(praxis_dir),
            state,
        )
        result = submit_export(
            praxis_dir,
            zip_path,
            state.get("participant_id", "PRAXIS-UNKNOWN"),
            diagnosis,
        )
        print()
        print_ok(f"Submission sent: {_c(result['zip_name'], C.B_CYAN)}")
        print_info(f"Destination: {result['email_to']}")
        return 0
    except Exception as exc:
        print_err(f"Submission failed: {exc}")
        status = get_submission_status(praxis_dir)
        print_info(status.get("reason", ""))
        if not (praxis_dir / "submission.json").is_file():
            template_path = praxis_dir / "submission.json"
            template_path.write_text(submission_setup_template(), encoding="utf-8")
            print_info(f"Created setup template: {template_path}")
        return 1


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
    print_info("2. Default flow:             praxis start  →  praxis stop  →  praxis checkout")
    print_info("3. Manual logging optional:  praxis log 'what you did' -d <min> -m <model>")
    print_info("4. After 7+ days, activate:  praxis activate")
    print_info("5. Check your progress:      praxis status")
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
    """Calculate unique days with recorded data."""
    dates = set()
    for e in entries:
        ts = e.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            dates.add(dt.date())
        except (ValueError, TypeError):
            pass
    return len(dates)


def _parse_design_quality(raw: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        raise ValidationError(
            "--design-quality must contain four comma-separated scores: clarity,tension,balance,elegance"
        )

    metrics = ("clarity", "tension", "balance", "elegance")
    values: Dict[str, Any] = {}
    for metric, part in zip(metrics, parts):
        try:
            score = int(part)
        except ValueError as exc:
            raise ValidationError(
                f"Invalid {metric} score '{part}'. Must be an integer 1-5."
            ) from exc
        if not (1 <= score <= 5):
            raise ValidationError(f"Invalid {metric} score '{score}'. Must be between 1 and 5.")
        values[metric] = score
    return values


def _build_reviewer_feedback(
    summary: Optional[str],
    reviewer_id: Optional[str],
    reviewer_source: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not any([summary, reviewer_id, reviewer_source]):
        return None
    feedback: Dict[str, Any] = {}
    if reviewer_id:
        feedback["reviewer_id"] = reviewer_id.strip()
    if reviewer_source:
        feedback["source"] = reviewer_source.strip()
    if summary:
        feedback["summary"] = summary.strip()
    return feedback


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="praxis",
        description=textwrap.dedent("""\
            PRAXIS — workflow observability kit for human-AI production.
            Captures time, quality, rework, trust, and continuity patterns.
        """),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              praxis status
              praxis start
              praxis stop
              praxis checkout
              praxis diagnose
              praxis log "Built auth module" -d 45 -m claude -q 4 -i 2 -h 1
              praxis activate
              praxis govern "Added rule: always test after deploy"
              praxis survey pre
              praxis survey post --lang es
              praxis export
              praxis submit
              praxis platforms
              praxis withdraw
        """),
    )
    parser.add_argument("--version", action="version", version="PRAXIS Kit 0.9.4")
    parser.add_argument("--lang", choices=["en", "es"], default="en",
                        help="Language for interactive prompts (default: en)")

    sub = parser.add_subparsers(dest="command", metavar="command")

    # status
    p_status = sub.add_parser("status", help="Show current phase, days active, metrics count")

    # diagnose
    sub.add_parser("diagnose", help="Show your workflow diagnosis")

    # passive capture
    sub.add_parser("start", help="Start passive session capture")
    sub.add_parser("stop", help="Stop passive session capture and create a draft entry")
    p_checkout = sub.add_parser("checkout", help="10-second review for the latest passive draft")
    p_checkout.add_argument("--id", type=str, help="Specific draft entry id")
    p_checkout.add_argument("--task", type=str, help="Short task summary")
    p_checkout.add_argument("--quality", type=int, choices=range(1, 6), metavar="1-5",
                            help="Usefulness / quality rating")
    p_checkout.add_argument("--rework", choices=["low", "med", "medium", "high"],
                            help="How much rework the AI created")
    p_checkout.add_argument("--corrected", action="store_true",
                            help="Mark that you had to heavily correct or override the AI")
    p_checkout.add_argument("--trust", type=int, choices=range(1, 8), metavar="1-7",
                            help="How much you would trust the output without verifying")
    p_checkout.add_argument("--model", type=str, metavar="MODEL",
                            help="Model/tool if known")

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
    p_log.add_argument("--iteration-type", choices=list(VALID_ITERATION_TYPES), metavar="TYPE",
                       help="Iteration type for software or creative/design work")
    p_log.add_argument("--design-quality", type=str, metavar="C,T,B,E",
                       help="Creative scores as clarity,tension,balance,elegance (1-5)")
    p_log.add_argument("--reviewer-feedback", type=str, metavar="TEXT",
                       help="External reviewer summary for creative/design outputs")
    p_log.add_argument("--reviewer-id", type=str, metavar="ID",
                       help="External reviewer identifier")
    p_log.add_argument("--reviewer-source", type=str, metavar="SOURCE",
                       help="Feedback source, e.g. playtest, editor, art director")
    p_log.add_argument("-l", "--layer", choices=list(VALID_LAYERS), metavar="LAYER",
                       help="PRAXIS sprint checkout with L1-R observations")
    p_log.add_argument("--l1r", action="store_true",
                       help="Log L1-R relational governance observations")
    p_log.add_argument("-p", "--project", type=str, help="Project name")
    p_log.add_argument("-n", "--notes", type=str, help="Optional notes")

    # activate
    p_act = sub.add_parser("activate", help="Observation mode status")

    # govern
    p_gov = sub.add_parser("govern", help="Log a governance event")
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
    p_inc.add_argument("-c", "--category", choices=list(VALID_INCIDENT_CATEGORIES),
                       help="Incident category: OPS, GOV, COM, PRD, RES, DES")

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

    # submit
    p_submit = sub.add_parser("submit", help="Export and submit data to the research inbox")
    p_submit.add_argument("--redact-tasks", action="store_true",
                          help="Replace task descriptions with [REDACTED]")
    p_submit.add_argument("-o", "--output", type=str, metavar="DIR",
                          help="Output directory for generated ZIP (default: current directory)")

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
    "start":     cmd_start,
    "stop":      cmd_stop,
    "checkout":  cmd_checkout,
    "log":       cmd_log,
    "diagnose":  cmd_diagnose,
    "activate":  cmd_activate,
    "govern":    cmd_govern,
    "incident":  cmd_incident,
    "survey":    cmd_survey,
    "export":    cmd_export,
    "submit":    cmd_submit,
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
