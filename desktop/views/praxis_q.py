"""PRAXIS Desktop — PRAXIS-Q Survey View

Interactive 5-dimension sprint quality rubric (3-point scale).
Dimensions: Completeness, Quality, Coherence, Efficiency, Traceability.
Based on surveys/praxis_q.json.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import customtkinter as ctk


# PRAXIS-Q dimensions (from surveys/praxis_q.json)
DIMENSIONS = [
    {
        "id": "completeness",
        "name": "Completeness",
        "question": "How complete is the work?",
        "labels": {1: "Incomplete", 2: "Mostly Complete", 3: "Fully Complete"},
    },
    {
        "id": "quality",
        "name": "Quality",
        "question": "What is the quality of the output?",
        "labels": {1: "Needs Rework", 2: "Acceptable", 3: "Excellent"},
    },
    {
        "id": "coherence",
        "name": "Coherence",
        "question": "How well does this fit with the overall project?",
        "labels": {1: "Doesn't Fit", 2: "Mostly Fits", 3: "Fits Perfectly"},
    },
    {
        "id": "efficiency",
        "name": "Efficiency",
        "question": "How efficient was the time invested?",
        "labels": {1: "Too Slow", 2: "On Time", 3: "Faster Than Expected"},
    },
    {
        "id": "traceability",
        "name": "Traceability",
        "question": "How well can you explain how this result was produced?",
        "labels": {1: "Can't Explain", 2: "Partially Traceable", 3: "Fully Documented"},
    },
]


class PraxisQView(ctk.CTkScrollableFrame):
    """PRAXIS-Q sprint quality survey."""

    def __init__(self, master: Any, vm: Any) -> None:
        super().__init__(master)
        self._vm = vm
        self._row = 0
        self._phase = None

        self.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="📝 PRAXIS-Q",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=self._next_row(), column=0, padx=20, pady=(20, 5), sticky="w")

        self._subtitle = ctk.CTkLabel(
            self,
            text="Sprint quality self-assessment (3-point scale)",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._subtitle.grid(row=self._next_row(), column=0, padx=20, pady=(0, 20), sticky="w")

        # Phase check overlay
        self._phase_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._phase_frame.grid(row=self._next_row(), column=0, sticky="nsew")

        self._form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._form_frame.grid(row=self._next_row(), column=0, sticky="nsew")
        self._form_frame.grid_columnconfigure(0, weight=1)

        # Dimension sliders and notes
        self._score_vars: Dict[str, ctk.IntVar] = {}
        self._score_labels: Dict[str, ctk.CTkLabel] = {}
        self._notes_entries: Dict[str, ctk.CTkTextbox] = {}

        for dim in DIMENSIONS:
            dim_id = dim["id"]
            dim_name = dim["name"]
            question = dim["question"]

            # Section label
            lbl = ctk.CTkLabel(
                self._form_frame,
                text=f"{dim_name}",
                font=ctk.CTkFont(size=14, weight="bold"),
            )
            lbl.grid(
                row=len(self._score_vars) * 3,
                column=0, padx=20, pady=(12, 2), sticky="w",
            )

            # Question text
            q_lbl = ctk.CTkLabel(
                self._form_frame,
                text=question,
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            q_lbl.grid(
                row=len(self._score_vars) * 3 + 1,
                column=0, padx=20, pady=(0, 4), sticky="w",
            )

            # Slider + label row
            slider_frame = ctk.CTkFrame(self._form_frame, fg_color="transparent")
            slider_frame.grid(
                row=len(self._score_vars) * 3 + 2,
                column=0, padx=20, pady=(0, 4), sticky="ew",
            )
            slider_frame.grid_columnconfigure(0, weight=1)

            var = ctk.IntVar(value=2)
            self._score_vars[dim_id] = var

            score_label = ctk.CTkLabel(
                slider_frame,
                text="Acceptable",
                font=ctk.CTkFont(size=13, weight="bold"),
                width=150,
            )
            score_label.pack(side="right", padx=(8, 0))
            self._score_labels[dim_id] = score_label

            slider = ctk.CTkSlider(
                slider_frame,
                from_=1,
                to=3,
                number_of_steps=2,
                variable=var,
                height=20,
                command=lambda val, did=dim_id: self._on_score_change(did, val),
            )
            slider.pack(fill="x", side="left", expand=True)

            # Notes field
            notes_entry = ctk.CTkTextbox(
                self._form_frame, height=40, wrap="word",
                font=ctk.CTkFont(size=12),
            )
            notes_entry.grid(
                row=len(self._score_vars) * 3 + 2,
                column=0, padx=(20, 20), pady=(0, 8), sticky="ew",
            )
            # Place it after the slider row
            notes_entry.grid(
                row=len(self._score_vars) * 3 + 2 + 1,
                column=0, padx=20, pady=(0, 8), sticky="ew",
            )
            self._notes_entries[dim_id] = notes_entry

        # Average score display
        avg_frame = ctk.CTkFrame(self._form_frame, fg_color="transparent")
        avg_frame.grid(
            row=len(DIMENSIONS) * 3,
            column=0, padx=20, pady=(16, 4), sticky="ew",
        )

        ctk.CTkLabel(
            avg_frame,
            text="Average Score:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        self._avg_label = ctk.CTkLabel(
            avg_frame,
            text="2.0 / 3.0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f1c40f",
        )
        self._avg_label.pack(side="left", padx=(12, 0))

        self._zone_label = ctk.CTkLabel(
            self._form_frame,
            text="Yellow Zone — Acceptable sprint",
            font=ctk.CTkFont(size=13),
            text_color="#f1c40f",
        )
        self._zone_label.grid(
            row=len(DIMENSIONS) * 3 + 1,
            column=0, padx=20, pady=(0, 8), sticky="w",
        )

        # Submit button
        self._submit_btn = ctk.CTkButton(
            self._form_frame,
            text="✓ Submit PRAXIS-Q",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._submit,
        )
        self._submit_btn.grid(
            row=len(DIMENSIONS) * 3 + 2,
            column=0, padx=20, pady=(12, 5), sticky="ew",
        )

        # Status
        self._status_label = ctk.CTkLabel(
            self._form_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._status_label.grid(
            row=len(DIMENSIONS) * 3 + 3,
            column=0, padx=20, pady=(0, 20), sticky="w",
        )

        # Check phase on show
        self.after(200, self._check_phase)

    def _next_row(self) -> int:
        r = self._row
        self._row += 1
        return r

    def _on_score_change(self, dim_id: str, value: float) -> None:
        """Update the label for a dimension slider."""
        dim = next(d for d in DIMENSIONS if d["id"] == dim_id)
        int_val = int(value)
        label_text = dim["labels"].get(int_val, str(int_val))
        self._score_labels[dim_id].configure(text=label_text)
        self._update_average()

    def _update_average(self) -> None:
        """Recalculate and display the average score."""
        values = [v.get() for v in self._score_vars.values()]
        avg = sum(values) / len(values) if values else 0
        self._avg_label.configure(text=f"{avg:.1f} / 3.0")

        if avg <= 1.6:
            self._avg_label.configure(text_color="#e74c3c")
            self._zone_label.configure(
                text="🔴 Red Zone — Problematic sprint. Review what went wrong.",
                text_color="#e74c3c",
            )
        elif avg <= 2.3:
            self._avg_label.configure(text_color="#f1c40f")
            self._zone_label.configure(
                text="🟡 Yellow Zone — Acceptable sprint. Focus on lowest dimension.",
                text_color="#f1c40f",
            )
        else:
            self._avg_label.configure(text_color="#2ecc71")
            self._zone_label.configure(
                text="🟢 Green Zone — Successful sprint!",
                text_color="#2ecc71",
            )

    def _check_phase(self) -> None:
        """Check if Phase B is active. If Phase A, show message."""
        if not self._vm.is_initialized():
            self._form_frame.grid_remove()
            self._subtitle.configure(
                text="⚠ PRAXIS not initialized. Set up a project first.",
                text_color="#e74c3c",
            )
            return

        state = self._vm.state or {}
        self._phase = state.get("phase", "A")

        if self._phase == "A":
            # Grayed out - show message
            self._form_frame.grid_remove()
            self._subtitle.configure(
                text="🔒 PRAXIS-Q is available in Phase B. Keep logging sprints to qualify.",
                text_color="#f39c12",
            )
        else:
            # Phase B - show the form
            self._subtitle.configure(
                text="✅ Phase B active — Rate your sprint quality below.",
                text_color="#2ecc71",
            )

    def _submit(self) -> None:
        """Submit the PRAXIS-Q survey."""
        scores = {dim_id: var.get() for dim_id, var in self._score_vars.items()}
        notes = {}
        for dim_id, entry in self._notes_entries.items():
            text = entry.get("1.0", "end").strip()
            if text:
                notes[dim_id] = text

        try:
            result = self._vm.save_praxis_q(scores=scores, notes=notes or None)
            avg = result.get("average", 0)
            self._status_label.configure(
                text=f"✅ Saved! Average: {avg:.1f}/3.0 — Entry: {result.get('id', 'ok')}",
                text_color="#2ecc71",
            )
            self._clear_form()
        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}",
                text_color="#e74c3c",
            )

    def _clear_form(self) -> None:
        """Reset form after submission."""
        for var in self._score_vars.values():
            var.set(2)
        for dim_id, label in self._score_labels.items():
            dim = next(d for d in DIMENSIONS if d["id"] == dim_id)
            label.configure(text=dim["labels"][2])
        for entry in self._notes_entries.values():
            entry.delete("1.0", "end")
        self._update_average()
