"""PRAXIS Desktop — Sessions View (Sprint 2: Review/Edit + Timer)

Replaces the old Log Sprint form with:
- Top: Current session timer (live)
- Middle: Recent sessions (review/edit unreviewed)
- Bottom: Quick log (manually add a past session)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import customtkinter as ctk

from collector.praxis_collector import apply_smart_checkout

from .checkout_dialog import CheckoutDialog


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


class LogSprintView(ctk.CTkScrollableFrame):
    """Sessions management view — timer, review, quick log."""

    def __init__(self, master: Any, vm: Any, app: Any = None) -> None:
        super().__init__(master)
        self._vm = vm
        self._app = app
        self._row = 0
        self._expanded_entry_id: Optional[str] = None
        self._quick_log_visible: bool = False

        self.grid_columnconfigure(0, weight=1)

        # ==================================================================
        # TOP: Current Session
        # ==================================================================
        title = ctk.CTkLabel(
            self,
            text="📋 Sessions",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=self._next_row(), column=0, padx=20, pady=(20, 5), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="Track, review, and edit your development sessions.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.grid(row=self._next_row(), column=0, padx=20, pady=(0, 12), sticky="w")

        # Current session frame
        self._current_frame = ctk.CTkFrame(self, corner_radius=8)
        self._current_frame.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 16), sticky="ew",
        )
        self._current_frame.grid_columnconfigure(1, weight=1)

        self._session_indicator = ctk.CTkLabel(
            self._current_frame,
            text="🟢 Session Active",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2ecc71",
        )
        self._session_indicator.grid(row=0, column=0, padx=(16, 8), pady=(12, 4), sticky="w")

        self._timer_label = ctk.CTkLabel(
            self._current_frame,
            text="0 min",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        )
        self._timer_label.grid(row=0, column=1, padx=(0, 16), pady=(12, 4), sticky="e")

        self._session_status = ctk.CTkLabel(
            self._current_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._session_status.grid(row=1, column=0, columnspan=2, padx=16, pady=(0, 4), sticky="w")

        btn_frame = ctk.CTkFrame(self._current_frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, padx=16, pady=(4, 12), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self._end_btn = ctk.CTkButton(
            btn_frame,
            text="⏹ End Session",
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._end_session,
        )
        self._end_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self._discard_btn = ctk.CTkButton(
            btn_frame,
            text="✕ Discard",
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            border_width=1,
            border_color="gray50",
            command=self._discard_session,
        )
        self._discard_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # ==================================================================
        # MIDDLE: Recent Sessions
        # ==================================================================
        sessions_title = ctk.CTkLabel(
            self,
            text="Recent Sessions",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        sessions_title.grid(
            row=self._next_row(), column=0, padx=20, pady=(4, 8), sticky="w",
        )

        self._sessions_container = ctk.CTkFrame(self, fg_color="transparent")
        self._sessions_container.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 16), sticky="ew",
        )
        self._sessions_container.grid_columnconfigure(0, weight=1)

        # Placeholder
        self._sessions_placeholder = ctk.CTkLabel(
            self._sessions_container,
            text="No sessions yet. Start working!",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._sessions_placeholder.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        # ==================================================================
        # BOTTOM: Quick Log (collapsible)
        # ==================================================================
        self._quicklog_toggle = ctk.CTkButton(
            self,
            text="▶ Quick Log — Add Past Session",
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_quick_log,
        )
        self._quicklog_toggle.grid(
            row=self._next_row(), column=0, padx=20, pady=(8, 4), sticky="ew",
        )

        self._quicklog_frame = ctk.CTkFrame(self, corner_radius=8)
        self._quicklog_frame.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 20), sticky="ew",
        )
        self._quicklog_frame.grid_remove()  # collapsed by default
        self._quicklog_frame.grid_columnconfigure(1, weight=1)

        self._build_quick_log_form()

        # Status label
        self._status_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=13), text_color="gray",
        )
        self._status_label.grid(
            row=self._next_row(), column=0, padx=20, pady=(0, 20), sticky="w",
        )

        # Load initial data
        self.after(200, self._refresh_sessions)
        self.after(300, self.timer_refresh)

    def _next_row(self) -> int:
        r = self._row
        self._row += 1
        return r

    # ------------------------------------------------------------------
    # Current session controls
    # ------------------------------------------------------------------

    def _end_session(self) -> None:
        """End current session and save it."""
        entry = self._vm.end_session()
        if entry:
            dialog = CheckoutDialog(self.winfo_toplevel(), entry)
            result = dialog.show()
            if result and entry.get("id"):
                try:
                    updated = apply_smart_checkout(
                        entry,
                        outcome=result.get("outcome", "solved"),
                        governance_tag=result.get("governance_tag", "none"),
                        task=result.get("task", ""),
                    )
                    self._vm.update_session_entry(str(entry.get("id")), updated)
                    dur = updated.get("duration_minutes") or updated.get("duration") or 0
                    self._status_label.configure(
                        text=f"✅ Session saved ({dur} min) — reviewed",
                        text_color="#2ecc71",
                    )
                except Exception as exc:
                    self._status_label.configure(
                        text=f"⚠ Checkout save failed: {exc}",
                        text_color="#e74c3c",
                    )
            else:
                dur = entry.get("duration_minutes") or entry.get("duration") or 0
                self._status_label.configure(
                    text=f"✅ Session saved ({dur} min) — unreviewed",
                    text_color="#2ecc71",
                )
        # Start a new session immediately
        self._vm.start_session()
        self._refresh_sessions()
        self.timer_refresh()

    def _discard_session(self) -> None:
        """Discard current session without saving."""
        self._vm.discard_session()
        self._vm.start_session()  # Start fresh
        self.timer_refresh()

    def timer_refresh(self) -> None:
        """Called periodically to update timer display."""
        if self._vm.is_session_active():
            elapsed = self._vm.get_session_elapsed_minutes()
            mins = int(elapsed)
            hours = mins // 60
            if hours > 0:
                self._timer_label.configure(text=f"{hours}h {mins % 60}m")
            else:
                self._timer_label.configure(text=f"{mins} min")
            self._session_indicator.configure(
                text="🟢 Session Active", text_color="#2ecc71"
            )
            self._end_btn.configure(state="normal")
            self._discard_btn.configure(state="normal")
            start = self._vm.get_session_start()
            if start:
                local_ts = start.strftime("%H:%M")
                self._session_status.configure(
                    text=f"Started at {local_ts}"
                )
        else:
            self._session_indicator.configure(
                text="⚫ No Active Session", text_color="gray"
            )
            self._timer_label.configure(text="—")
            self._session_status.configure(text="Start a new session from the dashboard.")
            self._end_btn.configure(state="disabled")
            self._discard_btn.configure(state="disabled")

    # ------------------------------------------------------------------
    # Recent sessions list
    # ------------------------------------------------------------------

    def _refresh_sessions(self) -> None:
        """Reload and display recent sessions."""
        # Clear existing session widgets
        for widget in self._sessions_container.winfo_children():
            widget.destroy()

        sessions = self._vm.get_recent_sessions(limit=20)

        if not sessions:
            self._sessions_placeholder = ctk.CTkLabel(
                self._sessions_container,
                text="No sessions yet. Start working!",
                font=ctk.CTkFont(size=13),
                text_color="gray",
            )
            self._sessions_placeholder.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for i, session in enumerate(sessions):
            self._create_session_row(i, session)

    def _create_session_row(self, index: int, session: dict) -> None:
        """Create a single session row in the list."""
        entry_id = session.get("id", "")
        reviewed = session.get("reviewed", True)
        duration = session.get("duration_min", 0)
        model = session.get("model")
        timestamp = session.get("timestamp", "")
        task = session.get("task")

        # Parse timestamp
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            date_str = ts.strftime("%Y-%m-%d %H:%M")
        except Exception:
            date_str = timestamp[:16]

        # Row frame
        border_color = "#f39c12" if not reviewed else "#333333"
        row_frame = ctk.CTkFrame(
            self._sessions_container,
            corner_radius=6,
            border_width=1 if not reviewed else 0,
            border_color=border_color,
        )
        row_frame.grid(row=index * 2, column=0, padx=0, pady=(4, 2), sticky="ew")
        row_frame.grid_columnconfigure(1, weight=1)

        # Status icon
        if reviewed:
            icon = "✅"
        else:
            icon = "⚠️"

        icon_label = ctk.CTkLabel(
            row_frame, text=icon, font=ctk.CTkFont(size=14), width=30,
        )
        icon_label.grid(row=0, column=0, padx=(8, 4), pady=8)

        # Info
        # Use detected platforms if available
        platforms = session.get("platform_ids", [])
        platform_str = ", ".join(platforms) if platforms else ""
        model_text = model if model else platform_str if platform_str else ("Unreviewed" if not reviewed else "N/A")
        task_text = task if task else "—"

        info_label = ctk.CTkLabel(
            row_frame, text=info_text, font=ctk.CTkFont(size=12),
        )
        info_label.grid(row=0, column=1, padx=4, pady=8, sticky="w")

        # Task preview
        if task:
            task_label = ctk.CTkLabel(
                row_frame,
                text=task[:60] + ("..." if len(task) > 60 else ""),
                font=ctk.CTkFont(size=11),
                text_color="gray",
            )
            task_label.grid(row=1, column=1, padx=4, pady=(0, 8), sticky="w")

        # Edit button
        edit_btn = ctk.CTkButton(
            row_frame, text="Edit", width=50, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            border_width=1,
            border_color="gray50",
            command=lambda eid=entry_id: self._toggle_edit(eid),
        )
        edit_btn.grid(row=0, column=2, padx=(4, 4), pady=8)

        # Discard button
        discard_btn = ctk.CTkButton(
            row_frame, text="✕ Discard", width=60, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            border_width=1,
            border_color="gray50",
            command=lambda eid=entry_id: self._discard_entry(eid),
        )
        discard_btn.grid(row=0, column=3, padx=(0, 8), pady=8)

        # Edit form (hidden by default)
        if self._expanded_entry_id == entry_id:
            edit_frame = self._build_edit_form(row_frame, session, entry_id)
            edit_frame.grid(row=2, column=0, columnspan=3, padx=8, pady=(0, 8), sticky="ew")

    def _toggle_edit(self, entry_id: str) -> None:
        """Toggle the edit form for a session entry."""
        if self._expanded_entry_id == entry_id:
            self._expanded_entry_id = None
        else:
            self._expanded_entry_id = entry_id
        self._refresh_sessions()

    def _build_edit_form(self, parent: Any, session: dict, entry_id: str) -> ctk.CTkFrame:
        """Build an edit form for a session entry."""
        frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        frame.grid_columnconfigure(1, weight=1)

        fields: list[tuple[str, Any]] = []

        # Task
        ctk.CTkLabel(frame, text="Task:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        task_var = ctk.StringVar(value=session.get("task") or "")
        ctk.CTkEntry(frame, textvariable=task_var, height=30).grid(
            row=len(fields), column=1, padx=(0, 12), pady=4, sticky="ew",
        )
        fields.append(("task", task_var))

        # Model
        ctk.CTkLabel(frame, text="Model:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        # Auto-fill model from detected platforms if not set
        detected_model = session.get("model") or ""
        if not detected_model:
            detected_platforms = session.get("platform_ids", [])
            if detected_platforms:
                detected_model = detected_platforms[0]
        model_var = ctk.StringVar(value=detected_model or "claude")
        ctk.CTkOptionMenu(
            frame, values=MODEL_OPTIONS, variable=model_var, height=30,
        ).grid(row=len(fields), column=1, padx=(0, 12), pady=4, sticky="ew")
        fields.append(("model", model_var))

        # Quality
        ctk.CTkLabel(frame, text="Quality:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        q_frame = ctk.CTkFrame(frame, fg_color="transparent")
        q_frame.grid(row=len(fields), column=1, padx=(0, 12), pady=4, sticky="ew")
        q_frame.grid_columnconfigure(0, weight=1)

        quality_val = session.get("quality")
        q_var = ctk.IntVar(value=quality_val if quality_val is not None else 3)
        q_lbl = ctk.CTkLabel(q_frame, text=f"{q_var.get()} / 5", width=40)
        q_lbl.pack(side="right")

        def _on_q(val, lbl=q_lbl):
            lbl.configure(text=f"{int(float(val))} / 5")

        ctk.CTkSlider(
            q_frame, from_=1, to=5, number_of_steps=4,
            variable=q_var, height=18, command=_on_q,
        ).pack(fill="x", side="left", expand=True)
        fields.append(("quality", q_var))

        # Iterations
        ctk.CTkLabel(frame, text="Iterations:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        iter_val = session.get("iterations")
        iter_var = ctk.StringVar(value=str(iter_val if iter_val is not None else 1))
        ctk.CTkEntry(frame, textvariable=iter_var, width=80, height=30).grid(
            row=len(fields), column=1, padx=(0, 12), pady=4, sticky="w",
        )
        fields.append(("iterations", iter_var))

        # Interventions
        ctk.CTkLabel(frame, text="Interventions:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        int_val = session.get("interventions")
        int_var = ctk.StringVar(value=str(int_val if int_val is not None else 0))
        ctk.CTkEntry(frame, textvariable=int_var, width=80, height=30).grid(
            row=len(fields), column=1, padx=(0, 12), pady=4, sticky="w",
        )
        fields.append(("interventions", int_var))

        # Notes
        ctk.CTkLabel(frame, text="Notes:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=len(fields), column=0, padx=(12, 8), pady=4, sticky="w",
        )
        notes_var = ctk.StringVar(value=session.get("notes") or "")
        ctk.CTkEntry(frame, textvariable=notes_var, height=30).grid(
            row=len(fields), column=1, padx=(0, 12), pady=4, sticky="ew",
        )
        fields.append(("notes", notes_var))

        # Save button
        def _save():
            updates = {}
            for key, var in fields:
                val = var.get()
                if isinstance(val, str):
                    val = val.strip() or None
                updates[key] = val
            # Convert numeric strings
            for k in ("quality", "iterations", "interventions"):
                if updates.get(k) is not None:
                    try:
                        updates[k] = int(updates[k])
                    except (ValueError, TypeError):
                        pass
            # Keep quality_self in sync with quality
            if "quality" in updates and isinstance(updates["quality"], int):
                updates["quality_self"] = updates["quality"]
            # Keep duration_minutes in sync
            if "duration_min" in updates:
                updates["duration_minutes"] = updates["duration_min"]

            ok = self._vm.update_session_entry(entry_id, updates)
            if ok:
                self._status_label.configure(
                    text="✅ Session updated!", text_color="#2ecc71"
                )
                self._expanded_entry_id = None
                self._refresh_sessions()
                # Check auto-transition
            else:
                self._status_label.configure(
                    text="⚠️ Session not found.", text_color="#e74c3c"
                )

        ctk.CTkButton(
            frame, text="💾 Save", height=32, width=80,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=_save,
        ).grid(row=len(fields), column=0, columnspan=2, padx=12, pady=(8, 12), sticky="ew")

        return frame

    # ------------------------------------------------------------------
    # Quick Log
    # ------------------------------------------------------------------

    def _toggle_quick_log(self) -> None:
        """Toggle quick log form visibility."""
        self._quick_log_visible = not self._quick_log_visible
        if self._quick_log_visible:
            self._quicklog_frame.grid()
            self._quicklog_toggle.configure(text="▼ Quick Log — Add Past Session")
        else:
            self._quicklog_frame.grid_remove()
            self._quicklog_toggle.configure(text="▶ Quick Log — Add Past Session")

    def _build_quick_log_form(self) -> None:
        """Build the quick log form inside _quicklog_frame."""
        frame = self._quicklog_frame
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame, text="Manually add a past session",
            font=ctk.CTkFont(size=12), text_color="gray",
        ).grid(row=0, column=0, columnspan=2, padx=12, pady=(8, 8), sticky="w")

        row = 1

        # Task
        ctk.CTkLabel(frame, text="Task:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_task = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self._ql_task, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="ew",
        )
        row += 1

        # Duration
        ctk.CTkLabel(frame, text="Duration (min):", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_duration = ctk.StringVar(value="30")
        ctk.CTkEntry(frame, textvariable=self._ql_duration, width=80, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="w",
        )
        row += 1

        # Date/Time
        ctk.CTkLabel(frame, text="Date (YYYY-MM-DD):", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        today = datetime.now().strftime("%Y-%m-%d")
        self._ql_date = ctk.StringVar(value=today)
        ctk.CTkEntry(frame, textvariable=self._ql_date, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="ew",
        )
        row += 1

        # Model
        ctk.CTkLabel(frame, text="Model:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_model = ctk.StringVar(value="claude")
        ctk.CTkOptionMenu(
            frame, values=MODEL_OPTIONS, variable=self._ql_model, height=30,
        ).grid(row=row, column=1, padx=(0, 12), pady=4, sticky="ew")
        row += 1

        # Quality
        ctk.CTkLabel(frame, text="Quality:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        ql_q_frame = ctk.CTkFrame(frame, fg_color="transparent")
        ql_q_frame.grid(row=row, column=1, padx=(0, 12), pady=4, sticky="ew")
        ql_q_frame.grid_columnconfigure(0, weight=1)

        self._ql_quality = ctk.IntVar(value=3)
        ql_q_lbl = ctk.CTkLabel(ql_q_frame, text="3 / 5", width=40)
        ql_q_lbl.pack(side="right")

        ctk.CTkSlider(
            ql_q_frame, from_=1, to=5, number_of_steps=4,
            variable=self._ql_quality, height=18,
            command=lambda val: ql_q_lbl.configure(text=f"{int(float(val))} / 5"),
        ).pack(fill="x", side="left", expand=True)
        row += 1

        # Iterations
        ctk.CTkLabel(frame, text="Iterations:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_iterations = ctk.StringVar(value="1")
        ctk.CTkEntry(frame, textvariable=self._ql_iterations, width=80, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="w",
        )
        row += 1

        # Interventions
        ctk.CTkLabel(frame, text="Interventions:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_interventions = ctk.StringVar(value="0")
        ctk.CTkEntry(frame, textvariable=self._ql_interventions, width=80, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="w",
        )
        row += 1

        # Notes
        ctk.CTkLabel(frame, text="Notes:", font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=row, column=0, padx=(12, 8), pady=4, sticky="w",
        )
        self._ql_notes = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self._ql_notes, height=30).grid(
            row=row, column=1, padx=(0, 12), pady=4, sticky="ew",
        )
        row += 1

        # Submit
        ctk.CTkButton(
            frame, text="✓ Add Session", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._submit_quick_log,
        ).grid(row=row, column=0, columnspan=2, padx=12, pady=(8, 12), sticky="ew")

    def _submit_quick_log(self) -> None:
        """Submit a manually entered past session."""
        task = self._ql_task.get().strip()
        if not task:
            self._status_label.configure(text="⚠ Task is required.", text_color="#e74c3c")
            return

        try:
            duration = int(self._ql_duration.get())
        except ValueError:
            self._status_label.configure(text="⚠ Invalid duration.", text_color="#e74c3c")
            return

        date_str = self._ql_date.get().strip()
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            from datetime import timezone as _tz
            timestamp = date_obj.replace(tzinfo=_tz.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            self._status_label.configure(text="⚠ Invalid date format.", text_color="#e74c3c")
            return

        try:
            iterations = int(self._ql_iterations.get())
            interventions = int(self._ql_interventions.get())
        except ValueError:
            self._status_label.configure(text="⚠ Invalid number.", text_color="#e74c3c")
            return

        model = self._ql_model.get()
        quality = self._ql_quality.get()
        notes = self._ql_notes.get().strip() or None

        try:
            entry = self._vm.log_sprint(
                task=task,
                duration=duration,
                model=model,
                quality=quality,
                iterations=iterations,
                interventions=interventions,
                notes=notes,
            )
            # Override timestamp to the specified date
            if self._vm._praxis_dir:
                self._vm.update_session_entry(
                    entry.get("id"),
                    {"timestamp": timestamp, "reviewed": True},
                )

            self._status_label.configure(
                text=f"✅ Session added for {date_str}!",
                text_color="#2ecc71",
            )
            self._clear_quick_log()
            self._refresh_sessions()
        except Exception as exc:
            self._status_label.configure(
                text=f"⚠ Error: {exc}", text_color="#e74c3c",
            )

    def _clear_quick_log(self) -> None:
        """Reset quick log form."""
        self._ql_task.set("")
        self._ql_duration.set("30")
        today = datetime.now().strftime("%Y-%m-%d")
        self._ql_date.set(today)
        self._ql_model.set("claude")
        self._ql_quality.set(3)
        self._ql_iterations.set("1")
        self._ql_interventions.set("0")
        self._ql_notes.set("")

    # ------------------------------------------------------------------
    # Auto-transition check
    # ------------------------------------------------------------------


    def _discard_entry(self, entry_id: str) -> None:
        """Discard/delete a specific session entry."""
        if self._vm._praxis_dir:
            from praxis_collector import delete_metric_entry
            ok = delete_metric_entry(self._vm._praxis_dir, entry_id)
            if ok:
                self._status_label.configure(
                    text="✅ Session discarded.", text_color="#2ecc71"
                )
                self._refresh_sessions()
            else:
                self._status_label.configure(
                    text="⚠️ Session not found.", text_color="#e74c3c"
                )

        def _activate():
            self._vm.activate_phase_b()
            dialog.destroy()
            self._status_label.configure(
                text="✅ Phase B activated!", text_color="#2ecc71"
            )
            self._refresh_sessions()

        ctk.CTkButton(
            btn_frame, text="Activate Phase B", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2ecc71", hover_color="#27ae60",
            command=_activate,
        ).grid(row=0, column=0, padx=4, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="Remind Me Later", height=36,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            border_width=1,
            border_color="gray50",
            command=dialog.destroy,
        ).grid(row=0, column=1, padx=4, sticky="ew")
