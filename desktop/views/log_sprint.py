"""PRAXIS Desktop — Log Sprint View (form for logging a sprint)

Fields: task, duration, model, quality, iterations, interventions.
Extra creative fields if project is creative: iteration_type, design_quality.
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk


MODEL_OPTIONS = [
    "claude",
    "copilot",
    "cursor",
    "codex",
    "openclaw",
    "aider",
    "windsurf",
    "other",
]

ITERATION_TYPE_OPTIONS = [
    "implementation",
    "debug",
    "refactor",
    "research",
    "design_cycle",
    "playtest",
    "revision",
    "refinement",
]


class LogSprintView(ctk.CTkScrollableFrame):
    """Sprint logging form."""

    def __init__(self, master: Any, vm: Any) -> None:
        super().__init__(master)
        self._vm = vm
        self._row = 0

        self.grid_columnconfigure(0, weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="⚡ Log Sprint",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=self._next_row(), column=0, padx=20, pady=(20, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Record an AI-assisted coding sprint.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.grid(row=self._next_row(), column=0, padx=20, pady=(0, 20), sticky="w")

        # --- Task Description ---
        self._add_section_label("Task Description")
        self._task_entry = ctk.CTkTextbox(self, height=80, wrap="word")
        self._task_entry.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="ew",
        )

        # --- Duration ---
        self._add_section_label("Duration")
        dur_frame = ctk.CTkFrame(self, fg_color="transparent")
        dur_frame.grid(row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="ew")

        self._duration_var = ctk.StringVar(value="30")
        dur_entry = ctk.CTkEntry(
            dur_frame, textvariable=self._duration_var, width=100, height=34,
        )
        dur_entry.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(dur_frame, text="minutes", text_color="gray").pack(side="left")

        # --- Model ---
        self._add_section_label("AI Model / Platform")
        self._model_var = ctk.StringVar(value="claude")
        model_menu = ctk.CTkOptionMenu(
            self,
            values=MODEL_OPTIONS,
            variable=self._model_var,
            height=34,
        )
        model_menu.grid(row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="w")

        # --- Quality slider ---
        self._add_section_label("Quality Rating")
        self._quality_var = ctk.IntVar(value=3)
        self._quality_label = ctk.CTkLabel(
            self, text="3 / 5", font=ctk.CTkFont(size=13, weight="bold"),
        )

        q_frame = ctk.CTkFrame(self, fg_color="transparent")
        q_frame.grid(row=self._next_row(), column=0, padx=20, pady=(0, 4), sticky="ew")
        q_frame.grid_columnconfigure(0, weight=1)

        quality_slider = ctk.CTkSlider(
            q_frame,
            from_=1,
            to=5,
            number_of_steps=4,
            variable=self._quality_var,
            command=self._on_quality_change,
            height=20,
        )
        quality_slider.pack(fill="x", side="left", expand=True)
        self._quality_label.pack(side="left", padx=(12, 0))

        # --- Iterations ---
        self._add_section_label("Iterations (AI generation cycles)")
        iter_frame = ctk.CTkFrame(self, fg_color="transparent")
        iter_frame.grid(row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="ew")

        self._iterations_var = ctk.StringVar(value="1")
        ctk.CTkEntry(
            iter_frame, textvariable=self._iterations_var, width=80, height=34,
        ).pack(side="left")

        # --- Human Interventions ---
        self._add_section_label("Human Corrections / Interventions")
        int_frame = ctk.CTkFrame(self, fg_color="transparent")
        int_frame.grid(row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="ew")

        self._interventions_var = ctk.StringVar(value="0")
        ctk.CTkEntry(
            int_frame, textvariable=self._interventions_var, width=80, height=34,
        ).pack(side="left")

        # --- Notes (optional) ---
        self._add_section_label("Notes (optional)")
        self._notes_entry = ctk.CTkTextbox(self, height=60, wrap="word")
        self._notes_entry.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="ew",
        )

        # --- Creative extension fields (conditionally shown) ---
        self._creative_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._creative_visible = False

        # Iteration type
        self._add_section_label("Iteration Type (creative)", parent=self._creative_frame)
        self._iter_type_var = ctk.StringVar(value="design_cycle")
        ctk.CTkOptionMenu(
            self._creative_frame,
            values=ITERATION_TYPE_OPTIONS,
            variable=self._iter_type_var,
            height=34,
        ).pack(padx=20, pady=(0, 12), anchor="w")

        # Design quality sub-metrics
        self._add_section_label("Design Quality Sub-Metrics", parent=self._creative_frame)
        self._design_sliders: dict[str, ctk.IntVar] = {}
        for metric in ("clarity", "tension", "balance", "elegance"):
            dq_frame = ctk.CTkFrame(self._creative_frame, fg_color="transparent")
            dq_frame.pack(fill="x", padx=20, pady=(0, 6))

            ctk.CTkLabel(dq_frame, text=metric.capitalize(), width=80).pack(side="left")

            var = ctk.IntVar(value=3)
            self._design_sliders[metric] = var

            lbl = ctk.CTkLabel(dq_frame, text="3", width=25)
            lbl.pack(side="right")

            slider = ctk.CTkSlider(
                dq_frame,
                from_=1, to=5, number_of_steps=4,
                variable=var,
                height=18,
                command=lambda val, l=lbl: l.configure(text=str(int(float(val)))),
            )
            slider.pack(side="left", fill="x", expand=True, padx=(8, 8))

        # --- Submit button ---
        self._submit_btn = ctk.CTkButton(
            self,
            text="✓ Log Sprint",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._submit,
        )
        self._submit_btn.grid(
            row=self._next_row(), column=0, padx=20, pady=(16, 5), sticky="ew",
        )

        # Status
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._status_label.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 20), sticky="w",
        )

        # Check creative on first show
        self.after(200, self._check_creative)

    def _next_row(self) -> int:
        r = self._row
        self._row += 1
        return r

    def _add_section_label(self, text: str, parent: Optional[Any] = None) -> None:
        target = parent or self
        lbl = ctk.CTkLabel(
            target,
            text=text,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        if parent:
            lbl.pack(padx=20, pady=(12, 4), anchor="w")
        else:
            lbl.grid(row=self._next_row(), column=0, padx=20, pady=(8, 4), sticky="w")

    def _on_quality_change(self, value: float) -> None:
        self._quality_label.configure(text=f"{int(value)} / 5")

    def _check_creative(self) -> None:
        """Show extra creative fields if this is a creative project."""
        if self._vm.is_creative_project() and not self._creative_visible:
            self._creative_frame.grid(
                row=self._row - 2,  # before submit button
                column=0,
                sticky="ew",
            )
            self._creative_visible = True

    def _submit(self) -> None:
        """Validate and submit the sprint log."""
        # Gather values
        task = self._task_entry.get("1.0", "end").strip()
        if not task:
            self._status_label.configure(
                text="⚠ Task description is required.",
                text_color="#e74c3c",
            )
            return

        try:
            duration = int(self._duration_var.get())
        except ValueError:
            self._status_label.configure(
                text="⚠ Duration must be a number.",
                text_color="#e74c3c",
            )
            return

        model = self._model_var.get()
        quality = self._quality_var.get()

        try:
            iterations = int(self._iterations_var.get())
        except ValueError:
            self._status_label.configure(
                text="⚠ Iterations must be a number.",
                text_color="#e74c3c",
            )
            return

        try:
            interventions = int(self._interventions_var.get())
        except ValueError:
            self._status_label.configure(
                text="⚠ Interventions must be a number.",
                text_color="#e74c3c",
            )
            return

        notes_text = self._notes_entry.get("1.0", "end").strip() or None

        # Optional creative fields
        iteration_type = None
        design_quality = None
        if self._creative_visible:
            iteration_type = self._iter_type_var.get()
            design_quality = {
                k: v.get() for k, v in self._design_sliders.items()
            }

        try:
            entry = self._vm.log_sprint(
                task=task,
                duration=duration,
                model=model,
                quality=quality,
                iterations=iterations,
                interventions=interventions,
                iteration_type=iteration_type,
                design_quality=design_quality,
                notes=notes_text,
            )
            eid = entry.get("id", "unknown")
            self._status_label.configure(
                text=f"✅ Logged! Entry: {eid}",
                text_color="#2ecc71",
            )
            self._clear_form()

        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}",
                text_color="#e74c3c",
            )

    def _clear_form(self) -> None:
        """Reset form fields after successful submission."""
        self._task_entry.delete("1.0", "end")
        self._duration_var.set("30")
        self._quality_var.set(3)
        self._quality_label.configure(text="3 / 5")
        self._iterations_var.set("1")
        self._interventions_var.set("0")
        self._notes_entry.delete("1.0", "end")
        if self._creative_visible:
            self._iter_type_var.set("design_cycle")
            for var in self._design_sliders.values():
                var.set(3)
