"""PRAXIS Kit Desktop — Main Application

CustomTkinter GUI wrapping the PRAXIS Universal Kit collector.
Works as both source (`python desktop/app.py`) and PyInstaller bundle.

Sprint 2: background session timer, auto-save on close,
settings dialog with PRAXIS ON/OFF toggle, session recovery.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import customtkinter as ctk

# Ensure both the desktop package and kit root are importable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # PyInstaller bundle: data files are under _MEIPASS
    _base = Path(sys._MEIPASS)
    sys.path.insert(0, str(_base))
    sys.path.insert(0, str(_base / 'desktop'))
else:
    # Running as source
    _kit_root = str(Path(__file__).resolve().parent.parent)
    if _kit_root not in sys.path:
        sys.path.insert(0, _kit_root)
    _desktop_dir = str(Path(__file__).resolve().parent)
    if _desktop_dir not in sys.path:
        sys.path.insert(0, _desktop_dir)

import json

from viewmodel import PraxisViewModel  # noqa: E402
from views.init_wizard import InitWizardView  # noqa: E402
from views.dashboard import DashboardView  # noqa: E402
# PRAXIS-Q removed — redundant with micro-checkout
from views.log_sprint import LogSprintView  # noqa: E402
# Protocol tab removed — prescriptive injection is a post-thesis product
from views.export import ExportView  # noqa: E402


# ---------------------------------------------------------------------------
# Appearance
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_TITLE = "PRAXIS Workflow Observatory"
WINDOW_SIZE = (780, 620)
MIN_SIZE = (600, 480)


class SettingsDialog(ctk.CTkToplevel):
    """Settings popup — threshold, project info."""

    def __init__(self, master: Any, vm: PraxisViewModel, app: Any) -> None:
        super().__init__(master)
        self._vm = vm
        self._app = app

        self.title("⚙️ Settings")
        self.geometry("400x300")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        row = 0

        # Title
        ctk.CTkLabel(
            self, text="⚙️ PRAXIS Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).grid(row=row, column=0, padx=20, pady=(20, 15), sticky="w")
        row += 1

        # Recording mode indicator
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=row, column=0, padx=20, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(
            mode_frame, text="Recording Mode:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="left")
        ctk.CTkLabel(
            mode_frame, text="Passive capture + micro-checkout",
            font=ctk.CTkFont(size=13),
            text_color="#2ecc71",
        ).pack(side="right")
        row += 1

        # Project directory
        ctk.CTkLabel(
            self, text="Project Directory:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=row, column=0, padx=20, pady=(10, 4), sticky="w")
        row += 1

        proj_dir = str(vm.project_dir) if vm.project_dir else "Not set"
        ctk.CTkLabel(
            self, text=proj_dir, font=ctk.CTkFont(size=11),
            text_color="gray", wraplength=360,
        ).grid(row=row, column=0, padx=20, pady=(0, 10), sticky="w")
        row += 1

        # Participant ID (read-only)
        state = vm.state or {}
        pid = state.get("participant_id", "N/A")
        ctk.CTkLabel(
            self, text="Participant ID:",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=row, column=0, padx=20, pady=(10, 4), sticky="w")
        row += 1
        ctk.CTkLabel(
            self, text=pid, font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=row, column=0, padx=20, pady=(0, 20), sticky="w")
        row += 1

        # Save button
        ctk.CTkButton(
            self, text="Save & Close", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_and_close,
        ).grid(row=row, column=0, padx=20, pady=(10, 20), sticky="ew")

    def _save_and_close(self) -> None:
        self._app._save_app_config()
        self.destroy()


class PraxisApp(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.title(WINDOW_TITLE)
        self.geometry(f"{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
        self.minsize(*MIN_SIZE)

        # View model
        self._vm = PraxisViewModel()

        # Layout: sidebar (fixed) + main content (expand)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self._sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self._sidebar.grid(row=0, column=0, rowspan=1, sticky="ns")
        self._sidebar.grid_propagate(False)
        self._sidebar.grid_rowconfigure(10, weight=1)

        # Sidebar title
        logo_label = ctk.CTkLabel(
            self._sidebar,
            text="🧪 PRAXIS",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        logo_label.grid(row=0, column=0, padx=16, pady=(20, 4))

        version_label = ctk.CTkLabel(
            self._sidebar,
            text="v0.10.0 Desktop · scientific integrity fix",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        version_label.grid(row=1, column=0, padx=16, pady=(0, 20))

        # Sidebar buttons
        self._nav_buttons: list[ctk.CTkButton] = []
        self._nav_labels = [
            "📊 Dashboard",
            "📋 Sessions",
            "📦 Export",
        ]
        self._nav_callbacks = [
            self._show_dashboard,
            self._show_log_sprint,
            self._show_export,
        ]

        for i, (label, callback) in enumerate(
            zip(self._nav_labels, self._nav_callbacks)
        ):
            btn = ctk.CTkButton(
                self._sidebar,
                text=label,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                height=36,
                font=ctk.CTkFont(size=14),
                command=callback,
            )
            btn.grid(row=2 + i, column=0, padx=8, pady=2, sticky="ew")
            self._nav_buttons.append(btn)

        # Hide nav buttons initially
        self._set_nav_visible(False)

        # --- Session control buttons (below nav) ---
        self._session_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        self._session_frame.grid(row=6, column=0, padx=8, pady=(12, 4), sticky="ew")
        self._session_frame.grid_remove()  # hidden until initialized

        # Session status indicator
        self._session_status = ctk.CTkLabel(
            self._session_frame,
            text="● No Session",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray",
        )
        self._session_status.pack(padx=8, pady=(4, 4), anchor="w")

        # Session timer display
        self._session_timer_label = ctk.CTkLabel(
            self._session_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._session_timer_label.pack(padx=8, pady=(0, 4), anchor="w")

        # Initialize PRAXIS button (re-init)
        self._reinit_btn = ctk.CTkButton(
            self._session_frame,
            text="🔄 Initialize PRAXIS",
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            text_color=("gray10", "gray90"),
            border_width=1,
            border_color="gray50",
            command=self._show_init_wizard,
        )
        self._reinit_btn.pack(padx=8, pady=(4, 4), fill="x")

        # Settings button at bottom of sidebar
        self._settings_btn = ctk.CTkButton(
            self._sidebar,
            text="⚙️ Settings",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            anchor="w",
            height=30,
            font=ctk.CTkFont(size=13),
            command=self._show_settings,
        )
        self._settings_btn.grid(row=11, column=0, padx=8, pady=(4, 12), sticky="ew")
        self._settings_btn.grid_remove()  # hidden until initialized

        # Main content area
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        # Current view
        self._current_view: Optional[ctk.CTkFrame] = None

        # Background timer for session checkpoint (every 60s)
        self._checkpoint_job = None
        # Background timer for UI refresh (every 30s)
        self._ui_timer_job = None

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try to auto-detect existing PRAXIS in cwd
        self._try_autoload()

    # ------------------------------------------------------------------
    # Window close — auto-save session
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        """Handle window close: auto-save session, cancel timers."""
        # Cancel timers
        try:
            if self._checkpoint_job:
                self.after_cancel(self._checkpoint_job)
                self._checkpoint_job = None
            if self._ui_timer_job:
                self.after_cancel(self._ui_timer_job)
                self._ui_timer_job = None
        except Exception:
            pass

        # Auto-save session
        try:
            if self._vm.is_session_active():
                self._vm.auto_save_session()
        except Exception:
            pass  # Don't prevent closing if save fails

        try:
            self._save_app_config()
        except Exception:
            pass

        self.destroy()

    # ------------------------------------------------------------------
    # Config persistence
    # ------------------------------------------------------------------

    def _get_config_path(self) -> Path:
        """Return path to the app config file (persists across sessions)."""
        return Path.home() / ".praxis_desktop_config.json"

    def _save_last_project(self, project_dir: Path) -> None:
        """Save the last-used project directory for auto-load on next launch."""
        self._save_app_config()

    def _save_app_config(self) -> None:
        """Save full app config including session state."""
        config_path = self._get_config_path()
        config = {
            "last_project_dir": str(self._vm._project_dir) if self._vm._project_dir else None,
            "praxis_mode_on": self._vm.is_praxis_mode_on(),
        }
        # Save active session state for recovery
        if self._vm.is_session_active() and self._vm.get_session_start():
            config["active_session_start"] = (
                self._vm.get_session_start().isoformat()
            )
        try:
            config_path.write_text(
                json.dumps(config, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _load_app_config(self) -> dict:
        """Load app config. Returns empty dict on failure."""
        config_path = self._get_config_path()
        if config_path.is_file():
            try:
                return json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    # ------------------------------------------------------------------
    # Background timer
    # ------------------------------------------------------------------

    def _start_checkpoint_timer(self) -> None:
        """Start the 60-second checkpoint timer for session state."""
        if self._checkpoint_job:
            self.after_cancel(self._checkpoint_job)
        self._checkpoint_job = self.after(60000, self._checkpoint_tick)

    def _checkpoint_tick(self) -> None:
        """Write session checkpoint to config every 60s."""
        if self._vm.is_session_active():
            self._save_app_config()
        self._checkpoint_job = self.after(60000, self._checkpoint_tick)

    def _start_ui_timer(self) -> None:
        """Start the 30-second UI refresh timer."""
        if self._ui_timer_job:
            self.after_cancel(self._ui_timer_job)
        self._ui_timer_job = self.after(30000, self._ui_tick)

    def _ui_tick(self) -> None:
        """Refresh UI elements that need periodic updates (timer, session status)."""
        self._update_session_controls()
        # Update current view if it has a timer_refresh method
        if self._current_view and hasattr(self._current_view, "timer_refresh"):
            self._current_view.timer_refresh()
        self._ui_timer_job = self.after(30000, self._ui_tick)

    # ------------------------------------------------------------------
    # Auto-load & session recovery
    # ------------------------------------------------------------------

    def _try_autoload(self) -> None:
        """Try to find and load an existing PRAXIS state.
        Checks: 1) saved last-used path, 2) cwd walk-up, 3) home dir.
        Also handles session recovery from interrupted sessions."""
        from viewmodel import find_praxis_dir

        cfg = self._load_app_config()

        # Restore PRAXIS mode settings
        self._vm._praxis_mode_on = cfg.get("praxis_mode_on", False)

        loaded = False

        # 1. Check saved last-used path
        saved_dir = cfg.get("last_project_dir")
        if saved_dir:
            praxis_dir = Path(saved_dir) / ".praxis"
            if praxis_dir.is_dir() and (praxis_dir / "state.json").is_file():
                project_dir = Path(saved_dir)
                self._vm.set_project_dir(project_dir)
                if self._vm.is_initialized():
                    loaded = True

        # 2. Check cwd walk-up
        if not loaded:
            praxis_dir = find_praxis_dir()
            if praxis_dir is not None:
                project_dir = praxis_dir.parent
                self._vm.set_project_dir(project_dir)
                if self._vm.is_initialized():
                    self._save_last_project(project_dir)
                    loaded = True

        if loaded:
            # Session recovery: check for interrupted session
            active_session_start = cfg.get("active_session_start")
            if active_session_start:
                try:
                    start_dt = datetime.fromisoformat(active_session_start)
                    # Check if there's already a matching entry in metrics
                    recovered = self._vm.recover_session(start_dt)
                    if recovered:
                        dur = recovered.get("duration_min", 0)
                        ts = recovered.get("timestamp", "")[:16]
                        # Show recovery notification after UI is ready
                        self.after(500, lambda: self._show_recovery_notification(ts, dur))
                except Exception:
                    pass

            # Start a new session
            self._vm.start_session()
            self._show_main_tabs()
            self._show_dashboard()
            self._start_checkpoint_timer()
            self._start_ui_timer()
            return

        # 3. No existing state — show init wizard
        self._show_init_wizard()

    def _show_recovery_notification(self, timestamp: str, duration: int) -> None:
        """Show a brief notification about a recovered session."""
        # Just update the session status briefly
        self._session_status.configure(
            text=f"↻ Recovered session from {timestamp}",
            text_color="#f39c12",
        )
        # Reset after 5 seconds
        self.after(5000, self._update_session_controls)

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _clear_content(self) -> None:
        if self._current_view is not None:
            self._current_view.destroy()
            self._current_view = None

    def _set_nav_visible(self, visible: bool) -> None:
        for btn in self._nav_buttons:
            if visible:
                btn.grid()
            else:
                btn.grid_remove()

    def _show_init_wizard(self) -> None:
        self._clear_content()
        self._set_nav_visible(False)
        self._session_frame.grid_remove()
        self._settings_btn.grid_remove()
        self._current_view = InitWizardView(
            self._content,
            vm=self._vm,
            on_complete=self._on_init_complete,
        )
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _on_init_complete(self) -> None:
        """Called when the init wizard finishes."""
        if self._vm._project_dir:
            self._save_last_project(self._vm._project_dir)
        # Start a new session
        self._vm.start_session()
        self._show_main_tabs()
        self._show_dashboard()
        self._start_checkpoint_timer()
        self._start_ui_timer()

    def _show_main_tabs(self) -> None:
        """Enable sidebar navigation after initialization."""
        self._set_nav_visible(True)
        self._session_frame.grid()
        self._settings_btn.grid()
        self._update_session_controls()

    def _update_session_controls(self) -> None:
        """Update session control button states based on session status."""
        if not self._vm.is_initialized():
            return

        if self._vm.is_session_active():
            elapsed = self._vm.get_session_elapsed_minutes()
            mins = int(elapsed)
            self._session_status.configure(
                text="🟢 Session active", text_color="#2ecc71"
            )
            self._session_timer_label.configure(
                text=f"⏱ {mins} min elapsed"
            )
        else:
            self._session_status.configure(
                text="● No active session", text_color="gray"
            )
            self._session_timer_label.configure(text="")

    def _show_dashboard(self) -> None:
        self._clear_content()
        self._current_view = DashboardView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")
        if hasattr(self._current_view, "refresh"):
            self._current_view.refresh()

    def _show_log_sprint(self) -> None:
        self._clear_content()
        self._current_view = LogSprintView(self._content, vm=self._vm, app=self)
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _show_export(self) -> None:
        self._clear_content()
        self._current_view = ExportView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _show_settings(self) -> None:
        SettingsDialog(self, vm=self._vm, app=self)

    # ------------------------------------------------------------------
    # Legacy compatibility (start/stop logging → session controls)
    # ------------------------------------------------------------------

    def _start_logging(self) -> None:
        """Start PRAXIS session logging."""
        self._vm.start_logging()
        self._update_session_controls()

    def _stop_logging(self) -> None:
        """Stop/pause PRAXIS session logging."""
        self._vm.stop_logging()
        self._update_session_controls()


def main() -> None:
    app = PraxisApp()
    app.mainloop()


if __name__ == "__main__":
    main()
