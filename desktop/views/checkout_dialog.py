"""PRAXIS Desktop - Smart session checkout dialog (v0.12.0)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import customtkinter as ctk

from collector.praxis_collector import get_session_checkout_context


class CheckoutDialog(ctk.CTkToplevel):
    """Modal smart checkout popup shown at the end of a passive session."""

    def __init__(self, master, entry):
        # type: (Any, Dict[str, Any]) -> None
        super().__init__(master)
        self._entry = entry
        self.result = None  # type: Optional[Dict[str, str]]
        self._context = get_session_checkout_context(entry)
        self._outcome = ctk.StringVar(value="solved")
        self._governance = ctk.StringVar(value="none")
        self._steering = ctk.IntVar(value=3)
        self._delegation = ctk.IntVar(value=0)
        self._context_effort = ctk.IntVar(value=2)

        self.title("Session Checkout")
        self.geometry("580x780")
        self.minsize(540, 700)
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
                "{} - {} "
                "({} min)\n"
                "{}\n"
                "{}".format(
                    self._context.get("started", "?"),
                    self._context.get("ended", "?"),
                    self._context.get("duration_minutes", 0),
                    self._context.get("platform_label", "Unknown"),
                    self._context.get("git_label", "No repo detected"),
                )
            ),
            justify="left",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=1, column=0, padx=18, pady=(0, 12), sticky="w")

        # Outcome
        ctk.CTkLabel(
            frame,
            text="What happened?",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=2, column=0, padx=18, pady=(2, 8), sticky="w")

        outcome_row = ctk.CTkFrame(frame, fg_color="transparent")
        outcome_row.grid(row=3, column=0, padx=18, pady=(0, 14), sticky="ew")
        for idx, (value, label, color) in enumerate([
            ("solved", "Solved", "#2ecc71"),
            ("partial", "Partially", "#f39c12"),
            ("abandoned", "Abandoned", "#e74c3c"),
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

        # Governance tag
        ctk.CTkLabel(
            frame,
            text="Governance moment? (optional)",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=4, column=0, padx=18, pady=(2, 8), sticky="w")

        tags_frame = ctk.CTkFrame(frame, fg_color="transparent")
        tags_frame.grid(row=5, column=0, padx=18, pady=(0, 14), sticky="ew")
        tag_options = [
            ("context_loss", "Context loss"),
            ("override", "Overrode AI"),
            ("ai_off_track", "AI off track"),
            ("scope_creep", "Scope creep"),
            ("model_switch", "Model switch"),
            ("none", "None"),
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

        # Steering intensity (NEW in v0.12.0)
        ctk.CTkLabel(
            frame,
            text="How much did you steer the AI?",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=6, column=0, padx=18, pady=(2, 8), sticky="w")

        steering_row = ctk.CTkFrame(frame, fg_color="transparent")
        steering_row.grid(row=7, column=0, padx=18, pady=(0, 14), sticky="ew")
        label_map = {1: "1 None", 2: "2 Light", 3: "3 Some", 4: "4 Active", 5: "5 Constant"}
        for idx, val in enumerate([1, 2, 3, 4, 5]):
            steering_row.grid_columnconfigure(idx, weight=1)
            ctk.CTkRadioButton(
                steering_row,
                text=label_map[val],
                variable=self._steering,
                value=val,
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=idx, padx=2, pady=4, sticky="w")

        # Delegation depth (v0.13.0)
        ctk.CTkLabel(
            frame,
            text="Delegation depth?",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=8, column=0, padx=18, pady=(0, 4), sticky="w")

        del_row = ctk.CTkFrame(frame, fg_color="transparent")
        del_row.grid(row=9, column=0, padx=18, pady=(0, 14), sticky="ew")
        for idx, (val, label) in enumerate([(0, "Direct"), (1, "Delegated"), (2, "Multi-hop")]):
            del_row.grid_columnconfigure(idx, weight=1)
            ctk.CTkRadioButton(
                del_row, text=label, variable=self._delegation, value=val,
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=idx, padx=4, pady=4, sticky="w")

        # Context provision effort (v0.13.0)
        ctk.CTkLabel(
            frame,
            text="Context provided upfront? (1=minimal, 5=extensive)",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).grid(row=10, column=0, padx=18, pady=(0, 4), sticky="w")

        ctx_row = ctk.CTkFrame(frame, fg_color="transparent")
        ctx_row.grid(row=11, column=0, padx=18, pady=(0, 14), sticky="ew")
        for idx, val in enumerate([1, 2, 3, 4, 5]):
            ctx_row.grid_columnconfigure(idx, weight=1)
            ctk.CTkRadioButton(
                ctx_row, text=str(val), variable=self._context_effort, value=val,
                font=ctk.CTkFont(size=12),
            ).grid(row=0, column=idx, padx=4, pady=4, sticky="w")

        # Multi-line session notes
        ctk.CTkLabel(
            frame,
            text="Session notes (what happened?)",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=12, column=0, padx=18, pady=(0, 6), sticky="w")

        self._notes_text = ctk.CTkTextbox(frame, height=80)
        self._notes_text.grid(row=13, column=0, padx=18, pady=(0, 18), sticky="ew")

        buttons = ctk.CTkFrame(frame, fg_color="transparent")
        buttons.grid(row=14, column=0, padx=18, pady=(0, 18), sticky="ew")
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

    def _focus(self):
        # type: () -> None
        try:
            self.focus_force()
            self._notes_text.focus_set()
        except Exception:
            pass

    def _save(self):
        # type: () -> None
        notes_text = self._notes_text.get("1.0", "end-1c").strip()
        self.result = {
            "outcome": self._outcome.get() or "solved",
            "governance_tag": self._governance.get() or "none",
            "task": notes_text,
            "steering_intensity": self._steering.get(),
            "delegation_depth": self._delegation.get(),
            "context_provision_effort": self._context_effort.get(),
        }
        self.destroy()

    def _skip(self):
        # type: () -> None
        self.result = None
        self.destroy()

    def show(self):
        # type: () -> Optional[Dict[str, str]]
        self.wait_window()
        return self.result
