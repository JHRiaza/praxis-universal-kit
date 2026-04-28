#!/usr/bin/env python3
"""PRAXIS submission helper.

Exports the participant ZIP, prints the current workflow diagnosis, and sends the
package to the research inbox when submission is enabled and SMTP is configured.
"""

from __future__ import annotations

import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent
for folder in (KIT_ROOT / "collector", KIT_ROOT / "export"):
    path = str(folder)
    if path not in sys.path:
        sys.path.insert(0, path)

from diagnostics import build_user_diagnosis
from praxis_collector import find_praxis_dir, load_all_metrics, load_governance_events, load_state
from anonymize import export_participant_zip
from submission import get_submission_status, submit_export, submission_setup_template


def main() -> int:
    praxis_dir = find_praxis_dir()
    if praxis_dir is None:
        print("PRAXIS not found. Run this from a project directory containing .praxis/.")
        return 1

    state = load_state(praxis_dir)
    entries = load_all_metrics(praxis_dir)
    governance = load_governance_events(praxis_dir)
    diagnosis = build_user_diagnosis(entries, governance, state)

    print("PRAXIS Submission Helper")
    print("=" * 32)
    print(diagnosis.get("headline", ""))
    print(diagnosis.get("summary", ""))

    status = get_submission_status(praxis_dir)
    print(f"Submission status: {status.get('reason', 'Unknown status')}")

    if not (praxis_dir / "submission.json").is_file():
        template_path = praxis_dir / "submission.json"
        template_path.write_text(submission_setup_template(), encoding="utf-8")
        print(f"Created submission template: {template_path}")

    if not status.get("allowed"):
        return 1

    zip_path = export_participant_zip(praxis_dir, output_dir=praxis_dir.parent)
    result = submit_export(
        praxis_dir,
        zip_path,
        state.get("participant_id", "PRAXIS-UNKNOWN"),
        diagnosis,
    )
    print(f"Submitted {result['zip_name']} to {result['email_to']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
