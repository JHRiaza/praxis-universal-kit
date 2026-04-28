"""PRAXIS Desktop — Dashboard View (status overview)

Shows participant ID, days active, metrics summary, session status.
Sprint 2: session timer indicator, unreviewed count.
"""

from __future__ import annotations

from typing import Any, Optional

import customtkinter as ctk


class DashboardView(ctk.CTkScrollableFrame):
    """Dashboard / status view."""

    def __init__(self, master: Any, vm: Any) -> None:
        super().__init__(master)
        self._vm = vm
        self._row = 0

        self.grid_columnconfigure((0, 1, 2), weight=1)

        # Title
        title = ctk.CTkLabel(
            self,
            text="📊 Dashboard",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.grid(row=self._next_row(), column=0, columnspan=3, padx=20, pady=(20, 5), sticky="w")

        self._subtitle = ctk.CTkLabel(
            self,
            text="Workflow observability overview",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._subtitle.grid(row=self._next_row(), column=0, columnspan=3, padx=20, pady=(0, 12), sticky="w")

        # --- Session status bar (Sprint 2: shows live timer) ---
        self._session_bar = ctk.CTkFrame(self, height=44)
        self._session_bar.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 8), sticky="ew",
        )
        self._session_bar.grid_propagate(False)

        self._session_dot = ctk.CTkLabel(
            self._session_bar,
            text="● No Session",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="gray",
        )
        self._session_dot.pack(side="left", padx=(16, 0), pady=10)

        self._session_timer = ctk.CTkLabel(
            self._session_bar,
            text="",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="white",
        )
        self._session_timer.pack(side="left", padx=(12, 0), pady=10)

        self._session_msg = ctk.CTkLabel(
            self._session_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._session_msg.pack(side="right", padx=(0, 16), pady=10)

        # --- Recording status bar ---
        self._phase_bar = ctk.CTkFrame(self, height=40)
        self._phase_bar.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 16), sticky="ew",
        )
        self._phase_bar.grid_propagate(False)

        self._phase_label = ctk.CTkLabel(
            self._phase_bar,
            text="🔬 Passive capture active",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2ecc71",
        )
        self._phase_label.pack(side="left", padx=(16, 0), pady=8)

        self._unreviewed_label = ctk.CTkLabel(
            self._phase_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#f39c12",
        )
        self._unreviewed_label.pack(side="right", padx=(0, 16), pady=8)

        # --- Status cards ---
        self._cards: dict[str, ctk.CTkLabel] = {}
        card_data = [
            ("participant_id", "Participant ID", "—"),
            ("days_active", "Days Active", "0"),
            ("total_entries", "Total Entries", "0"),
            ("passive_capture_count", "Passive Captures", "0"),
            ("avg_quality", "Avg Quality", "—"),
            ("avg_reliability", "Avg Reliability", "—"),
            ("avg_duration", "Avg Duration (min)", "—"),
            ("autonomy_rate", "Autonomy Rate", "—"),
        ]

        cards_start_row = self._next_row()
        for i, (key, label_text, default) in enumerate(card_data):
            row = cards_start_row + i // 3
            col = i % 3

            card = ctk.CTkFrame(self, width=200)
            card.grid(row=row, column=col, padx=(20, 10), pady=6, sticky="ew")
            card.grid_propagate(False)

            card_label = ctk.CTkLabel(
                card,
                text=label_text,
                font=ctk.CTkFont(size=12),
                text_color="gray",
            )
            card_label.pack(padx=16, pady=(12, 2), anchor="w")

            value_label = ctk.CTkLabel(
                card,
                text=default,
                font=ctk.CTkFont(size=20, weight="bold"),
            )
            value_label.pack(padx=16, pady=(0, 12), anchor="w")

            self._cards[key] = value_label

        # Advance row counter past cards
        card_rows = (len(card_data) + 2) // 3
        self._row = cards_start_row + card_rows

        # Platforms section
        plat_title = ctk.CTkLabel(
            self,
            text="🖥 Detected Platforms",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        plat_title.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(20, 5), sticky="w",
        )

        self._platforms_label = ctk.CTkLabel(
            self,
            text="Scanning...",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=500,
            justify="left",
        )
        self._platforms_label.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 20), sticky="w",
        )

        diag_title = ctk.CTkLabel(
            self,
            text="🪞 What PRAXIS is showing you",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        diag_title.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 5), sticky="w",
        )

        self._diag_headline = ctk.CTkLabel(
            self,
            text="Log work to unlock your diagnosis.",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=680,
            justify="left",
        )
        self._diag_headline.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 6), sticky="w",
        )

        self._diag_summary = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=680,
            justify="left",
        )
        self._diag_summary.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 6), sticky="w",
        )

        self._diag_insights = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
            wraplength=680,
            justify="left",
        )
        self._diag_insights.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 20), sticky="w",
        )

        # Refresh button
        refresh_btn = ctk.CTkButton(
            self,
            text="↻ Refresh",
            width=100,
            command=self.refresh,
        )
        refresh_btn.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 20), sticky="w",
        )

    def _next_row(self) -> int:
        r = self._row
        self._row += 1
        return r

    def refresh(self) -> None:
        """Reload data from the view model and update all cards."""
        data = self._vm.get_dashboard_data()

        if not data.get("initialized"):
            self._subtitle.configure(text="PRAXIS not initialized")
            return

        passive_count = data.get("passive_capture_count", 0)
        self._subtitle.configure(text=f"Last updated just now · passive captures: {passive_count}")

        # Session status (Sprint 2)
        session_active = data.get("session_active", False)
        session_min = data.get("session_elapsed_min", 0)
        if session_active:
            mins = int(session_min)
            hours = mins // 60
            timer_text = f"{hours}h {mins % 60}m" if hours > 0 else f"{mins} min"
            self._session_dot.configure(text="🟢", text_color="#2ecc71")
            self._session_timer.configure(text=f"Session: {timer_text}")
            self._session_msg.configure(text="Session active")
        else:
            self._session_dot.configure(text="⚫", text_color="gray")
            self._session_timer.configure(text="")
            self._session_msg.configure(text="No active session")

        # Recording indicator
        self._phase_label.configure(
            text="🔬 Passive capture active",
            text_color="#2ecc71",
        )

        # Unreviewed badge (Sprint 2)
        unreviewed = data.get("unreviewed_count", 0)
        if unreviewed > 0:
            self._unreviewed_label.configure(text=f"⚠️ {unreviewed} unreviewed")
        else:
            self._unreviewed_label.configure(text="")

        # Update cards
        mapping = {
            "participant_id": data.get("participant_id", "—"),
            "session_count": str(data.get("session_count", 0)),
            "days_active": str(data.get("days_active", 0)),
            "total_entries": str(data.get("total_entries", 0)),
            "passive_capture_count": str(passive_count),
            "avg_quality": (
                f"{data['avg_quality']:.1f} / 5"
                if data.get("avg_quality") is not None else "—"
            ),
            "avg_reliability": (
                f"{data['diagnosis']['metrics']['avg_reliability']:.0%}"
                if data.get("diagnosis", {}).get("metrics", {}).get("avg_reliability") is not None else "—"
            ),
            "avg_duration": (
                f"{data['avg_duration']:.1f} min"
                if data.get("avg_duration") is not None else "—"
            ),
            "autonomy_rate": (
                f"{data['autonomy_rate']:.0%}"
                if data.get("autonomy_rate") is not None else "—"
            ),
        }

        for key, value in mapping.items():
            if key in self._cards:
                self._cards[key].configure(text=value)

        # Platforms
        platforms = data.get("platforms", [])
        if platforms:
            self._platforms_label.configure(
                text=", ".join(platforms),
                text_color="white",
            )
        else:
            self._platforms_label.configure(
                text="No platforms detected.",
                text_color="gray",
            )

        diagnosis = data.get("diagnosis", {}) or {}
        self._diag_headline.configure(text=diagnosis.get("headline", "Log work to unlock your diagnosis."))
        self._diag_summary.configure(text=diagnosis.get("summary", ""))
        insights = diagnosis.get("insights", [])[:3]
        if insights:
            self._diag_insights.configure(text="\n".join(f"• {item}" for item in insights), text_color="white")
        else:
            self._diag_insights.configure(text="", text_color="gray")

    def timer_refresh(self) -> None:
        """Called by the app's UI timer to refresh session indicator."""
        self.refresh()
