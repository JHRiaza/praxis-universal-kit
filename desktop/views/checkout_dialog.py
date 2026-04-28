"""PRAXIS Desktop — Smart session checkout dialog."""

from __future__ import annotations

from typing import Any, Dict, Optional

import customtkinter as ctk

from collector.praxis_collector import get_session_checkout_context


class CheckoutDialog(ctk.CTkToplevel):
    """Modal smart checkout popup shown at the end of a passive session."""

    def __init__(self, master: Any, entry: Dict[str, Any]) -> None:
        super().__init__(master)
        self._entry = entry
        self.result: Optional[Dict[str, str]] = None
        self._context = get_session_checkout_context(entry)
        self._outcome = ctk.StringVar(value="solved")
        self._governance = ctk.StringVar(value="none")

        self.title("Session Checkout")
        self.geometry("560x420")
        self.minsize(520, 380)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Session Checkout",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(18, 6), sticky="w")

        ctk.CTkLabel(
            frame,
            text=(
                f"{self._context.get('started', '?')} → {self._context.get('ended', '?')} "
                f"({self._context.get('duration_minutes', 0)} min)\n"
                f"{self._context.get('platform_label', 'Unknown')}\n"
                f"{self._context.get('git_label', 'No repo detected')}"
            ),
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=18, pady=(0, 12), sticky="w")

        ctk.CTkLabel(
            frame,
            text="What happened?",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=2, column=0, padx=18, pady=(2, 8), sticky="w")

        outcome_row = ctk.CTkFrame(frame, fg_color="transparent")
        outcome_row.grid(row=3, column=0, padx=18, pady=(0, 14), sticky="ew")
        for idx, (value, label, color) in enumerate([
            ("solved", "✅ Solved", "#2ecc71"),
            ("partial", "⚠️ Partially", "#f39c12"),
            ("abandoned", "❌ Abandoned", "#e74c3c"),
        ]):
            outcome_row.grid_columnconfigure(idx, weight=1)
            ctk.CTkRadioButton(
                outcome_row,
                text=label,
                variable=self._outcome,
                value=value,
                fg_color=color,
                hover_color=color,
                font=ctk.CTkFont(size=14, weight="bold"),
            ).grid(row=0, column=idx, padx=6, pady=4, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Governance moment? (optional)",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=4, column=0, padx=18, pady=(2, 8), sticky="w")

        tags_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tags_frame.grid(row=5, column=0, padx=18, pady=(0, 14), sticky="ew")
        tag_options = [
            ("context_loss", "🔄 Context loss"),
            ("override", "👤 Overrode AI"),
            ("ai_off_track", "🤔 AI off track"),
            ("scope_creep", "📏 Scope creep"),
            ("model_switch", "🔀 Model switch"),
            ("none", "🚫 None"),
        ]
        for idx, (value, label) in enumerate(tag_options):
            row = idx // 2
            col = idx % 2
            tags_frame.grid_columnconfigure(col, weight=1)
            ctk.CTkRadioButton(
                tags_frame,
                text=label,
                variable=self._governance,
                value=value,
                font=ctk.CTkFont(size=13),
            ).grid(row=row, column=col, padx=6, pady=4, sticky="w")

        ctk.CTkLabel(
            frame,
            text="1-line task summary (optional)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=6, column=0, padx=18, pady=(0, 6), sticky="w")

        self._task_entry = ctk.CTkEntry(frame, height=34, placeholder_text="What were you trying to do?")
        self._task_entry.grid(row=7, column=0, padx=18, pady=(0, 18), sticky="ew")

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.grid(row=8, column=0, padx=18, pady=(0, 18), sticky="ew")
        buttons.grid_columnconfigure(0, weight=1)
        buttons.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            buttons,
            text="Skip",
            fg_color="transparent",
            border_width=1,
            border_color="gray50",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self._skip,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            buttons,
            text="Save",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save,
        ).grid(row=0, column=1, padx=(6, 0), sticky="ew")

        self.protocol("WM_DELETE_WINDOW", self._skip)
        self.after(50, self._focus)

    def _focus(self) -> None:
        try:
            self.focus_force()
            self._task_entry.focus_set()
        except Exception:
            pass

    def _save(self) -> None:
        self.result = {
            "outcome": self._outcome.get() or "solved",
            "governance_tag": self._governance.get() or "none",
            "task": self._task_entry.get().strip(),
        }
        self.destroy()

    def _skip(self) -> None:
        self.result = None
        self.destroy()

    def show(self) -> Optional[Dict[str, str]]:
        self.wait_window()
        return self.result
