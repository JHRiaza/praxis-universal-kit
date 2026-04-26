"""PRAXIS Desktop — Protocol Management View.

Shows which AI platforms are detected, injection status, and toggle controls.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Any, Callable, Optional


class ProtocolView(ctk.CTkScrollableFrame):
    """Governance protocol injection management."""

    def __init__(
        self,
        master: Any,
        vm: Any,
        on_change: Optional[Callable] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self._vm = vm
        self._on_change = on_change
        self._platform_widgets: dict = {}

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # Header
        ctk.CTkLabel(
            self,
            text="🛡️ Governance Protocol",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        # Status line
        self._status_label = ctk.CTkLabel(
            self,
            text="Loading...",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._status_label.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

        # Explanation
        ctk.CTkLabel(
            self,
            text=(
                "PRAXIS injects governance rules into your AI tools' config files.\n"
                "When ON, every platform responds to \"PRAXIS?\" with its status.\n"
                "Phase A = no injection (baseline). Phase B = governance active."
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
        ).grid(row=2, column=0, padx=20, pady=(0, 16), sticky="w")

        # Master toggle
        toggle_frame = ctk.CTkFrame(self, fg_color=("#e8e8e8", "#2a2a2a"))
        toggle_frame.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")
        toggle_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            toggle_frame,
            text="⚡ Activate PRAXIS Protocol",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self._master_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="",
            command=self._on_master_toggle,
            width=50,
            height=26,
        )
        self._master_toggle.grid(row=0, column=1, padx=16, pady=12, sticky="e")

        # Platform cards
        self._cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._cards_frame.grid(row=4, column=0, padx=20, pady=(0, 12), sticky="ew")
        self._cards_frame.grid_columnconfigure(0, weight=1)

        # Refresh button
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, padx=20, pady=(0, 16), sticky="w")

        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            width=100,
            height=32,
            font=ctk.CTkFont(size=12),
            command=self.refresh,
        ).pack(side="left", padx=(0, 8))

        # Rules preview
        ctk.CTkLabel(
            self,
            text="📋 Governance Rules (injected when ON):",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=6, column=0, padx=20, pady=(8, 4), sticky="w")

        from collector.protocol import GOVERNANCE_RULES
        for i, rule in enumerate(GOVERNANCE_RULES):
            checkpoint = " 🔒" if rule.get("checkpoint") else ""
            row_frame = ctk.CTkFrame(self, fg_color="transparent")
            row_frame.grid(row=7 + i, column=0, padx=20, pady=1, sticky="ew")
            row_frame.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row_frame,
                text=f"{rule['id']}",
                font=ctk.CTkFont(size=11, weight="bold"),
                width=35,
            ).grid(row=0, column=0, padx=(0, 4), sticky="w")
            ctk.CTkLabel(
                row_frame,
                text=f"{rule['title']}{checkpoint}",
                font=ctk.CTkFont(size=11),
            ).grid(row=0, column=1, sticky="w")

        self.refresh()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Refresh platform status from disk."""
        try:
            status_list = self._vm.get_protocol_status()
        except Exception:
            status_list = []

        injected_count = sum(1 for s in status_list if s.get("injected"))
        total = len(status_list)

        # Update master toggle
        if injected_count > 0:
            self._master_toggle.select()
            self._status_label.configure(
                text=f"🟢 PRAXIS ON — injected in {injected_count}/{total} platforms",
                text_color="#2ecc71",
            )
        else:
            self._master_toggle.deselect()
            self._status_label.configure(
                text=f"🔴 PRAXIS OFF — Phase A (baseline)",
                text_color="#e74c3c",
            )

        # Rebuild platform cards
        for w in self._cards_frame.winfo_children():
            w.destroy()
        self._platform_widgets.clear()

        for i, s in enumerate(status_list):
            card = self._build_platform_card(self._cards_frame, s, i)
            self._platform_widgets[s["platform"]] = card

    def _build_platform_card(self, parent: Any, status: dict, row: int) -> dict:
        """Build a single platform status card."""
        card = ctk.CTkFrame(parent, fg_color=("#f0f0f0", "#333333"))
        card.grid(row=row, column=0, pady=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Status icon
        injected = status.get("injected", False)
        file_exists = status.get("file_exists", False)
        icon = "🟢" if injected else ("🟡" if file_exists else "⚪")
        tooltip = "Injected" if injected else ("File exists" if file_exists else "Not found")

        ctk.CTkLabel(
            card, text=icon, font=ctk.CTkFont(size=16), width=30,
        ).grid(row=0, column=0, padx=(12, 4), pady=8)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=4, pady=8, sticky="w")
        ctk.CTkLabel(
            info_frame, text=status["platform"],
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w")
        ctk.CTkLabel(
            info_frame, text=f"{status['filename']} — {tooltip}",
            font=ctk.CTkFont(size=10), text_color="gray",
        ).pack(anchor="w")
        if status.get("needs_per_project"):
            ctk.CTkLabel(
                info_frame, text="⚠ Per-project: inject into each project folder",
                font=ctk.CTkFont(size=9), text_color="#f39c12",
            ).pack(anchor="w")

        # Toggle per platform
        toggle = ctk.CTkSwitch(
            card,
            text="",
            width=40,
            height=22,
            command=lambda name=status["platform"]: self._toggle_platform(name),
        )
        toggle.grid(row=0, column=2, padx=12, pady=8)
        if injected:
            toggle.select()

        return {"card": card, "toggle": toggle}

    def _on_master_toggle(self) -> None:
        """Handle master toggle change."""
        if self._master_toggle.get():
            self._activate_all()
        else:
            self._deactivate_all()

    def _activate_all(self) -> None:
        """Inject PRAXIS into all detected platforms."""
        # Check if any per-project platforms exist and show warning
        try:
            status_list = self._vm.get_protocol_status()
            per_project = [s for s in status_list if s.get("needs_per_project")]
            if per_project and not self._check_acknowledged():
                self._show_per_project_warning(per_project)
                return
        except Exception:
            pass
        
        try:
            results = self._vm.inject_protocol_all()
            ok = sum(1 for v in results.values() if v)
            total = len(results)
            self._status_label.configure(
                text=f"🟢 PRAXIS ON — injected in {ok}/{total} platforms",
                text_color="#2ecc71",
            )
        except Exception as e:
            self._status_label.configure(
                text=f"⚠️ Error: {e}", text_color="#e74c3c",
            )
        self.refresh()
        if self._on_change:
            self._on_change()

    def _check_acknowledged(self) -> bool:
        """Check if user has acknowledged the per-project warning."""
        config_path = Path.home() / ".praxis_per_project_ack"
        return config_path.exists()

    def _acknowledge(self) -> None:
        """Mark per-project warning as acknowledged."""
        config_path = Path.home() / ".praxis_per_project_ack"
        config_path.write_text("acknowledged", encoding="utf-8")

    def _show_per_project_warning(self, platforms: list) -> None:
        """Show warning about per-project platforms."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("⚠️ Per-Project Injection Required")
        dialog.geometry("480x320")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="⚠️ Per-Project Platforms Detected",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(padx=20, pady=(20, 10))

        names = "\n".join(f"  • {p['platform']} ({p['filename']})" for p in platforms)
        ctk.CTkLabel(
            dialog,
            text=(
                f"The following platforms read config from EACH project folder:\n{names}\n\n"
                "This means you must inject PRAXIS into every project folder\n"
                "where you use these tools. One injection per project.\n\n"
                "PRAXIS Kit injects into the current project directory.\n"
                "For other projects, open them in PRAXIS Kit and activate again."
            ),
            font=ctk.CTkFont(size=12),
            justify="left",
            wraplength=440,
        ).pack(padx=20, pady=(0, 15))

        def _proceed():
            self._acknowledge()
            dialog.destroy()
            # Now actually activate
            try:
                results = self._vm.inject_protocol_all()
                ok = sum(1 for v in results.values() if v)
                total = len(results)
                self._status_label.configure(
                    text=f"🟢 PRAXIS ON — injected in {ok}/{total} platforms",
                    text_color="#2ecc71",
                )
            except Exception as e:
                self._status_label.configure(
                    text=f"⚠️ Error: {e}", text_color="#e74c3c",
                )
            self.refresh()
            if self._on_change:
                self._on_change()

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(0, 20))
        ctk.CTkButton(
            btn_frame, text="I Understand — Activate", width=180, height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=_proceed,
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_frame, text="Cancel", width=100, height=36,
            font=ctk.CTkFont(size=13),
            fg_color="gray", hover_color="darkgray",
            command=dialog.destroy,
        ).pack(side="left", padx=8)

    def _deactivate_all(self) -> None:
        """Remove PRAXIS from all platforms."""
        try:
            self._vm.remove_protocol_all()
            self._status_label.configure(
                text="🔴 PRAXIS OFF — Phase A (baseline)",
                text_color="#e74c3c",
            )
        except Exception as e:
            self._status_label.configure(
                text=f"⚠️ Error: {e}", text_color="#e74c3c",
            )
        self.refresh()
        if self._on_change:
            self._on_change()

    def _toggle_platform(self, name: str) -> None:
        """Toggle PRAXIS for a single platform."""
        widgets = self._platform_widgets.get(name, {})
        toggle = widgets.get("toggle")
        if toggle is None:
            return
        if toggle.get():
            try:
                self._vm.inject_protocol_platform(name)
            except Exception:
                pass
        else:
            try:
                self._vm.remove_protocol_platform(name)
            except Exception:
                pass
        self.refresh()
        if self._on_change:
            self._on_change()
