"""PRAXIS Desktop — Export View

Export anonymized ZIP of collected data.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import customtkinter as ctk


class ExportView(ctk.CTkScrollableFrame):
    """Export / data submission view."""

    def __init__(self, master: Any, vm: Any) -> None:
        super().__init__(master)
        self._vm = vm

        self.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="📦 Export & Submission",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Generate an anonymized ZIP, review your diagnosis, and optionally submit to the research inbox.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # --- Data summary ---
        self._add_section_label("Current Data")
        self._summary_label = ctk.CTkLabel(
            self,
            text="No data to export.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=500,
            justify="left",
        )
        self._summary_label.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="w")

        self._diagnosis_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            wraplength=540,
            justify="left",
        )
        self._diagnosis_label.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="w")

        self._submission_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            wraplength=540,
            justify="left",
            text_color="gray",
        )
        self._submission_label.grid(row=5, column=0, padx=20, pady=(0, 16), sticky="w")

        # --- Options ---
        self._redact_var = ctk.BooleanVar(value=False)
        redact_cb = ctk.CTkCheckBox(
            self,
            text="Redact task descriptions (replace with [REDACTED])",
            variable=self._redact_var,
            font=ctk.CTkFont(size=13),
        )
        redact_cb.grid(row=6, column=0, padx=20, pady=(0, 16), sticky="w")

        # --- Export button ---
        self._export_btn = ctk.CTkButton(
            self,
            text="📁 Generate Export ZIP",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._do_export,
        )
        self._export_btn.grid(row=7, column=0, padx=20, pady=(0, 8), sticky="ew")

        self._submit_btn = ctk.CTkButton(
            self,
            text="📬 Generate ZIP + Submit",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._do_submit,
        )
        self._submit_btn.grid(row=8, column=0, padx=20, pady=(0, 8), sticky="ew")

        self._setup_btn = ctk.CTkButton(
            self,
            text="🛠 Create submission config template",
            height=34,
            font=ctk.CTkFont(size=13),
            command=self._write_submission_template,
        )
        self._setup_btn.grid(row=9, column=0, padx=20, pady=(0, 8), sticky="ew")

        # --- Open folder button ---
        self._open_btn = ctk.CTkButton(
            self,
            text="📂 Open File Location",
            height=34,
            font=ctk.CTkFont(size=13),
            command=self._open_location,
            state="disabled",
        )
        self._open_btn.grid(row=10, column=0, padx=20, pady=(0, 8), sticky="ew")

        # Status
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._status_label.grid(row=11, column=0, padx=20, pady=(0, 20), sticky="w")

        self._last_zip_path: Path | None = None

        # Initial refresh
        self.after(200, self.refresh)

    def _add_section_label(self, text: str) -> None:
        lbl = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl.grid(row=2, column=0, padx=20, pady=(8, 4), sticky="w")

    def refresh(self) -> None:
        """Update the data summary."""
        info = self._vm.get_export_info()

        if not info.get("initialized"):
            self._summary_label.configure(
                text="PRAXIS not initialized. Set up a project first.",
                text_color="gray",
            )
            return

        metrics = info.get("metrics_count", 0)
        gov = info.get("governance_count", 0)
        first = info.get("first_entry", "")
        last = info.get("last_entry", "")
        diagnosis = info.get("diagnosis", {}) or {}
        submission = info.get("submission", {}) or {}

        text = f"Metrics entries: {metrics}  |  Governance events: {gov}"
        if first and last:
            text += f"\nDate range: {first[:10]} → {last[:10]}"

        self._summary_label.configure(text=text, text_color="white")
        diag_text = diagnosis.get("headline", "")
        insights = diagnosis.get("insights", [])[:2]
        if insights:
            diag_text += "\n" + "\n".join(f"• {item}" for item in insights)
        self._diagnosis_label.configure(text=diag_text or "Diagnosis will appear after you log work.")

        submission_text = submission.get("reason", "Submission is unavailable.")
        last_submitted = submission.get("last_submitted_at")
        if last_submitted:
            submission_text += f"\nLast submitted: {last_submitted[:19].replace('T', ' ')} UTC"
        submission_text += f"\n30-day submissions: {submission.get('sent_last_30d', 0)}"
        self._submission_label.configure(text=submission_text)
        self._submit_btn.configure(state="normal" if submission.get("allowed") else "disabled")

    def _do_export(self) -> None:
        try:
            zip_path = self._vm.export_zip(redact_tasks=self._redact_var.get())
            self._last_zip_path = zip_path
            self._status_label.configure(
                text=f"✅ ZIP created: {zip_path.name}",
                text_color="#2ecc71",
            )
            self._open_btn.configure(state="normal")
        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}",
                text_color="#e74c3c",
            )

    def _do_submit(self) -> None:
        try:
            result = self._vm.submit_latest_export(redact_tasks=self._redact_var.get())
            self._last_zip_path = result.get("zip_path")
            self._status_label.configure(
                text=f"✅ Submitted to {result['email_to']}: {result['zip_name']}",
                text_color="#2ecc71",
            )
            self._open_btn.configure(state="normal")
            self.refresh()
        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Submission blocked: {exc}",
                text_color="#e74c3c",
            )

    def _write_submission_template(self) -> None:
        try:
            path = self._vm.write_submission_template()
            self._status_label.configure(
                text=f"✅ Template created: {path.name}",
                text_color="#2ecc71",
            )
            self.refresh()
        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}",
                text_color="#e74c3c",
            )

    def _open_location(self) -> None:
        if self._last_zip_path is None:
            return
        folder = str(self._last_zip_path.parent)
        if sys.platform == "win32":
            subprocess.run(["explorer", folder])
        elif sys.platform == "darwin":
            subprocess.run(["open", folder])
        else:
            subprocess.run(["xdg-open", folder])
