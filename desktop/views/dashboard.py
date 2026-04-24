"""PRAXIS Desktop — Dashboard View (status overview)

Shows phase, participant ID, days active, metrics summary, session status.
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
            text="PRAXIS status overview",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._subtitle.grid(row=self._next_row(), column=0, columnspan=3, padx=20, pady=(0, 12), sticky="w")

        # --- Session status bar ---
        self._session_bar = ctk.CTkFrame(self, height=44)
        self._session_bar.grid(
            row=self._next_row(), column=0, columnspan=3,
            padx=20, pady=(0, 16), sticky="ew",
        )
        self._session_bar.grid_propagate(False)

        self._session_dot = ctk.CTkLabel(
            self._session_bar,
            text="● Active",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2ecc71",
        )
        self._session_dot.pack(side="left", padx=(16, 0), pady=10)

        self._session_msg = ctk.CTkLabel(
            self._session_bar,
            text="Logging is active",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._session_msg.pack(side="left", padx=(8, 0), pady=10)

        # --- Status cards ---
        self._cards: dict[str, ctk.CTkLabel] = {}
        card_data = [
            ("participant_id", "Participant ID", "—"),
            ("phase", "Phase", "—"),
            ("days_active", "Days Active", "0"),
            ("total_entries", "Total Entries", "0"),
            ("avg_quality", "Avg Quality", "—"),
            ("avg_duration", "Avg Duration (min)", "—"),
            ("autonomy_rate", "Autonomy Rate", "—"),
            ("total_duration", "Total Duration (min)", "0"),
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

        self._subtitle.configure(text="Last updated just now")

        # Session status
        logging_active = data.get("logging_active", True)
        if logging_active:
            self._session_dot.configure(text="● Active", text_color="#2ecc71")
            self._session_msg.configure(text="Logging is active")
        else:
            self._session_dot.configure(text="● Paused", text_color="#e74c3c")
            self._session_msg.configure(text="Logging is paused")

        # Update cards
        mapping = {
            "participant_id": data.get("participant_id", "—"),
            "phase": f"Phase {data.get('phase', '—')}",
            "days_active": str(data.get("days_active", 0)),
            "total_entries": str(data.get("total_entries", 0)),
            "avg_quality": (
                f"{data['avg_quality']:.1f} / 5"
                if data.get("avg_quality") is not None else "—"
            ),
            "avg_duration": (
                f"{data['avg_duration']:.1f} min"
                if data.get("avg_duration") is not None else "—"
            ),
            "autonomy_rate": (
                f"{data['autonomy_rate']:.0%}"
                if data.get("autonomy_rate") is not None else "—"
            ),
            "total_duration": f"{data.get('total_duration', 0)} min",
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
