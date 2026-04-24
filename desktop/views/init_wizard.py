"""PRAXIS Desktop — Init Wizard View (first-run setup)

Shows consent text, generates participant ID, initializes PRAXIS state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

import customtkinter as ctk


class InitWizardView(ctk.CTkFrame):
    """First-run initialization wizard."""

    def __init__(
        self,
        master: Any,
        vm: Any,  # PraxisViewModel
        on_complete: Callable[[], None],
    ) -> None:
        super().__init__(master)
        self._vm = vm
        self._on_complete = on_complete

        self.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="🧪 PRAXIS Kit — Setup",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, padx=40, pady=(40, 10), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Initialize PRAXIS data collection in your project folder.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.grid(row=1, column=0, padx=40, pady=(0, 30), sticky="w")

        # Consent section
        consent_title = ctk.CTkLabel(
            self,
            text="Research Consent",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        consent_title.grid(row=2, column=0, padx=40, pady=(0, 10), sticky="w")

        consent_text = ctk.CTkTextbox(
            self,
            height=140,
            wrap="word",
            font=ctk.CTkFont(size=12),
        )
        consent_text.grid(row=3, column=0, padx=40, pady=(0, 10), sticky="ew")
        consent_text.insert(
            "1.0",
            "By participating in the PRAXIS research study, you consent to the "
            "anonymous collection of AI-assisted development metrics. Your data "
            "includes: task descriptions (optional), duration, quality self-ratings, "
            "AI model used, iteration count, and human intervention count.\n\n"
            "No personal identifiers, file contents, or conversation logs are "
            "collected. Data is stored locally in .praxis/ and shared only when you "
            "explicitly export it. You may withdraw and delete all data at any time.",
        )
        consent_text.configure(state="disabled")

        # Consent checkbox
        self._consent_var = ctk.BooleanVar(value=False)
        consent_cb = ctk.CTkCheckBox(
            self,
            text="I have read and agree to participate in this research study.",
            variable=self._consent_var,
            font=ctk.CTkFont(size=13),
            command=self._update_button_state,
        )
        consent_cb.grid(row=4, column=0, padx=40, pady=(0, 20), sticky="w")

        # Project directory
        dir_label = ctk.CTkLabel(
            self,
            text="Project Directory",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        dir_label.grid(row=5, column=0, padx=40, pady=(0, 5), sticky="w")

        dir_hint = ctk.CTkLabel(
            self,
            text="Select the folder where you want PRAXIS to track your work.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        dir_hint.grid(row=6, column=0, padx=40, pady=(0, 10), sticky="w")

        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.grid(row=7, column=0, padx=40, pady=(0, 5), sticky="ew")
        dir_frame.grid_columnconfigure(0, weight=1)

        self._dir_var = ctk.StringVar(value=str(Path.cwd()))
        self._dir_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self._dir_var,
            placeholder_text="Path to your project folder…",
            height=38,
        )
        self._dir_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        browse_btn = ctk.CTkButton(
            dir_frame,
            text="Browse",
            width=90,
            command=self._browse_dir,
        )
        browse_btn.grid(row=0, column=1)

        # Initialize button
        self._init_btn = ctk.CTkButton(
            self,
            text="Initialize PRAXIS",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._do_init,
            state="disabled",
        )
        self._init_btn.grid(row=8, column=0, padx=40, pady=(20, 10), sticky="ew")

        # Status label
        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._status_label.grid(row=9, column=0, padx=40, pady=(0, 40), sticky="w")

    def _update_button_state(self) -> None:
        if self._consent_var.get():
            self._init_btn.configure(state="normal")
        else:
            self._init_btn.configure(state="disabled")

    def _browse_dir(self) -> None:
        from tkinter import filedialog
        selected = filedialog.askdirectory(
            title="Select Project Directory",
            initialdir=self._dir_var.get(),
        )
        if selected:
            self._dir_var.set(selected)

    def _do_init(self) -> None:
        project_dir = Path(self._dir_var.get().strip())
        if not project_dir.is_dir():
            self._status_label.configure(
                text="⚠ Invalid directory path.",
                text_color="#e74c3c",
            )
            return

        try:
            state = self._vm.initialize(
                project_dir=project_dir,
                consent_given=self._consent_var.get(),
            )
            pid = state.get("participant_id", "N/A")
            self._status_label.configure(
                text=f"✅ Initialized! Participant ID: {pid}",
                text_color="#2ecc71",
            )
            self._init_btn.configure(state="disabled")
            # Notify parent to switch to main tabs
            self.after(800, self._on_complete)

        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}",
                text_color="#e74c3c",
            )
