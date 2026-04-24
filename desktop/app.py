"""PRAXIS Kit Desktop — Main Application

CustomTkinter GUI wrapping the PRAXIS Universal Kit collector.
Works as both source (`python desktop/app.py`) and PyInstaller bundle.
"""

from __future__ import annotations

import sys
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

from viewmodel import PraxisViewModel  # noqa: E402
from views.init_wizard import InitWizardView  # noqa: E402
from views.dashboard import DashboardView  # noqa: E402
from views.praxis_q import PraxisQView  # noqa: E402
from views.log_sprint import LogSprintView  # noqa: E402
from views.export import ExportView  # noqa: E402


# ---------------------------------------------------------------------------
# Appearance
# ---------------------------------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_TITLE = "PRAXIS Kit"
WINDOW_SIZE = (780, 620)
MIN_SIZE = (600, 480)


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
            text="v0.3 Desktop",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        version_label.grid(row=1, column=0, padx=16, pady=(0, 20))

        # Sidebar buttons — new order:
        # 1. 📊 Dashboard
        # 2. 📝 PRAXIS-Q
        # 3. ⚡ Log Sprint
        # 4. 📦 Export
        self._nav_buttons: list[ctk.CTkButton] = []
        self._nav_labels = [
            "📊 Dashboard",
            "📝 PRAXIS-Q",
            "⚡ Log Sprint",
            "📦 Export",
        ]
        self._nav_callbacks = [
            self._show_dashboard,
            self._show_praxis_q,
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
            text="● Active",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#2ecc71",
        )
        self._session_status.pack(padx=8, pady=(4, 4), anchor="w")

        # Start Logging button
        self._start_btn = ctk.CTkButton(
            self._session_frame,
            text="▶ Start Logging",
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2ecc71",
            hover_color="#27ae60",
            text_color="white",
            command=self._start_logging,
        )
        self._start_btn.pack(padx=8, pady=(0, 4), fill="x")

        # Stop PRAXIS button
        self._stop_btn = ctk.CTkButton(
            self._session_frame,
            text="⏹ Stop PRAXIS",
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            text_color="white",
            command=self._stop_logging,
        )
        self._stop_btn.pack(padx=8, pady=(0, 4), fill="x")

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

        # Main content area
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        # Current view
        self._current_view: Optional[ctk.CTkFrame] = None

        # Try to auto-detect existing PRAXIS in cwd
        self._try_autoload()

    def _try_autoload(self) -> None:
        """Try to find and load an existing PRAXIS state from cwd."""
        from viewmodel import find_praxis_dir
        praxis_dir = find_praxis_dir()
        if praxis_dir is not None:
            project_dir = praxis_dir.parent
            self._vm.set_project_dir(project_dir)
            if self._vm.is_initialized():
                self._show_main_tabs()
                self._show_dashboard()
                return

        # No existing state — show init wizard
        self._show_init_wizard()

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
        self._current_view = InitWizardView(
            self._content,
            vm=self._vm,
            on_complete=self._on_init_complete,
        )
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _on_init_complete(self) -> None:
        """Called when the init wizard finishes."""
        self._show_main_tabs()
        self._show_dashboard()

    def _show_main_tabs(self) -> None:
        """Enable sidebar navigation after initialization."""
        self._set_nav_visible(True)
        self._session_frame.grid()
        self._update_session_controls()

    def _update_session_controls(self) -> None:
        """Update session control button states based on logging status."""
        if not self._vm.is_initialized():
            return

        active = self._vm.is_logging_active()
        if active:
            self._session_status.configure(text="● Active", text_color="#2ecc71")
            self._start_btn.configure(state="disabled", fg_color="#1a7a42")
            self._stop_btn.configure(state="normal", fg_color="#e74c3c")
        else:
            self._session_status.configure(text="● Paused", text_color="#e74c3c")
            self._start_btn.configure(state="normal", fg_color="#2ecc71")
            self._stop_btn.configure(state="disabled", fg_color="#7a1a1a")

    def _start_logging(self) -> None:
        """Start PRAXIS session logging."""
        self._vm.start_logging()
        self._update_session_controls()

    def _stop_logging(self) -> None:
        """Stop/pause PRAXIS session logging."""
        self._vm.stop_logging()
        self._update_session_controls()

    def _show_dashboard(self) -> None:
        self._clear_content()
        self._current_view = DashboardView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")
        # Refresh data
        if hasattr(self._current_view, "refresh"):
            self._current_view.refresh()

    def _show_praxis_q(self) -> None:
        self._clear_content()
        self._current_view = PraxisQView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _show_log_sprint(self) -> None:
        self._clear_content()
        self._current_view = LogSprintView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _show_export(self) -> None:
        self._clear_content()
        self._current_view = ExportView(self._content, vm=self._vm)
        self._current_view.grid(row=0, column=0, sticky="nsew")


def main() -> None:
    app = PraxisApp()
    app.mainloop()


if __name__ == "__main__":
    main()
