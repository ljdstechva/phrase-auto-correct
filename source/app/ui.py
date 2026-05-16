"""Non-activating Tkinter palette UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from .config import AppConfig, SUPPORTED_TONES
from .windows_api import get_cursor_position, make_window_no_activate


BG = "#f8fafc"
SURFACE = "#ffffff"
SURFACE_HOVER = "#eff6ff"
TEXT = "#111827"
MUTED = "#4b5563"
ACCENT = "#2563eb"
BORDER = "#cbd5e1"
ERROR = "#b91c1c"


class PopupUI:
    """Context-menu-style palette that does not activate its window."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.window: tk.Toplevel | None = None
        self.shell: tk.Frame | None = None
        self.tone_frame: tk.Frame | None = None
        self.generation_frame: tk.Frame | None = None
        self.settings_window: tk.Toplevel | None = None
        self.selected_tone: str | None = None
        self.anchor: tuple[int, int] | None = None
        self._configure_style()

    def close(self) -> None:
        """Close the active popup if one exists."""

        if self.window and self.window.winfo_exists():
            self.window.destroy()
        self.window = None
        self.shell = None
        self.tone_frame = None
        self.generation_frame = None
        self.selected_tone = None
        self.anchor = None

    def show_tone_picker(
        self,
        on_tone: Callable[[str], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Show the first-step tone chooser without stealing focus."""

        self.close()
        window = self._make_palette(on_cancel)
        self.window = window

        shell = tk.Frame(window, bg=BORDER, padx=1, pady=1)
        shell.pack()
        self.shell = shell

        tone_frame = tk.Frame(shell, bg=SURFACE, padx=6, pady=6)
        tone_frame.grid(row=0, column=0, sticky="ns")
        self.tone_frame = tone_frame

        self._build_tone_menu(tone_frame, on_tone, on_cancel)
        self._show_palette()

    def show_loading(
        self,
        tone: str,
        on_cancel: Callable[[], None],
    ) -> None:
        """Show generation loading beside the tone menu."""

        self.selected_tone = tone
        frame = self._ensure_generation_frame()
        self._clear(frame)

        header = self._panel_header(frame, f"{tone} rewrite", on_cancel)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            frame,
            text="Generating three options...",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", padx=10, pady=(0, 10))

        progress = ttk.Progressbar(frame, mode="indeterminate", length=300)
        progress.pack(fill="x", padx=10, pady=(0, 10))
        progress.start(12)
        self._show_palette()

    def show_options(
        self,
        options: list[str],
        on_option: Callable[[int], None],
        on_regenerate: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        """Show generated options with replace icons and one regenerate icon."""

        frame = self._ensure_generation_frame()
        self._clear(frame)

        header = self._panel_header(
            frame,
            "AI rewrites",
            on_cancel,
            on_regenerate,
        )
        header.pack(fill="x", pady=(0, 8))

        for index, option in enumerate(options):
            card = tk.Frame(
                frame,
                bg=BG,
                highlightthickness=1,
                highlightbackground=BORDER,
                padx=8,
                pady=8,
            )
            card.pack(fill="x", padx=8, pady=5)

            label = tk.Label(
                card,
                text=option,
                bg=BG,
                fg=TEXT,
                font=("Segoe UI", 9),
                justify="left",
                anchor="w",
                wraplength=350,
            )
            label.grid(row=0, column=0, sticky="ew", padx=(0, 8))

            replace = tk.Button(
                card,
                text="✓",
                command=lambda selected=index: on_option(selected),
                width=3,
                takefocus=0,
                cursor="hand2",
                relief="flat",
                bg=ACCENT,
                fg="white",
                activebackground="#1d4ed8",
                activeforeground="white",
                font=("Segoe UI Symbol", 11, "bold"),
            )
            replace.grid(row=0, column=1, sticky="n")
            card.columnconfigure(0, weight=1)

        self._show_palette()

    def show_error(
        self,
        message: str,
        on_close: Callable[[], None],
        title: str = "Phrase Auto-correct",
    ) -> None:
        """Show a compact non-activating error popup."""

        self.close()
        window = self._make_palette(on_close)
        self.window = window

        shell = tk.Frame(window, bg=BORDER, padx=1, pady=1)
        shell.pack()
        frame = tk.Frame(shell, bg=SURFACE, padx=12, pady=10)
        frame.pack()

        tk.Label(
            frame,
            text=title,
            bg=SURFACE,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            frame,
            text=message,
            bg=SURFACE,
            fg=ERROR,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=340,
            anchor="w",
        ).pack(fill="x", pady=(8, 10))
        self._menu_button(frame, "Close", on_close).pack(fill="x")
        self._show_palette()

    def confirm_uninstall(self) -> bool:
        """Ask for confirmation before launching uninstall."""

        return messagebox.askyesno(
            "Uninstall Phrase Auto-correct",
            "Stop Phrase Auto-correct and remove its startup shortcut?",
            parent=self.root,
        )

    def show_settings(
        self,
        config: AppConfig,
        on_save: Callable[[dict[str, str]], None],
    ) -> None:
        """Show editable AI provider settings from the tray menu."""

        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title("Phrase Auto-correct Settings")
        window.resizable(False, False)
        window.configure(bg=BG)
        window.attributes("-topmost", True)
        window.protocol("WM_DELETE_WINDOW", window.destroy)

        frame = tk.Frame(window, bg=BG, padx=16, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="AI Settings",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        provider = tk.StringVar(value=config.ai_provider)
        model = tk.StringVar(value=config.openai_model)
        api_key = tk.StringVar(value=config.openai_api_key)
        base_url = tk.StringVar(value=config.openai_base_url)

        self._settings_label(frame, "Provider").grid(row=1, column=0, sticky="w")
        provider_box = ttk.Combobox(
            frame,
            textvariable=provider,
            values=("openai", "fallback"),
            state="readonly",
            width=36,
        )
        provider_box.grid(row=1, column=1, sticky="ew", pady=4)

        self._settings_label(frame, "Model").grid(row=2, column=0, sticky="w")
        tk.Entry(frame, textvariable=model, width=40).grid(
            row=2,
            column=1,
            sticky="ew",
            pady=4,
        )

        self._settings_label(frame, "API key").grid(row=3, column=0, sticky="w")
        tk.Entry(frame, textvariable=api_key, width=40, show="*").grid(
            row=3,
            column=1,
            sticky="ew",
            pady=4,
        )

        self._settings_label(frame, "Base URL").grid(row=4, column=0, sticky="w")
        tk.Entry(frame, textvariable=base_url, width=40).grid(
            row=4,
            column=1,
            sticky="ew",
            pady=4,
        )

        self._settings_label(frame, "System prompt").grid(
            row=5,
            column=0,
            sticky="nw",
            pady=(8, 0),
        )
        prompt = tk.Text(
            frame,
            width=58,
            height=7,
            wrap="word",
            font=("Segoe UI", 9),
        )
        prompt.grid(row=5, column=1, sticky="ew", pady=(8, 4))
        prompt.insert("1.0", config.system_prompt)

        buttons = tk.Frame(frame, bg=BG)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))

        def save() -> None:
            on_save(
                {
                    "ai_provider": provider.get(),
                    "openai_model": model.get(),
                    "openai_api_key": api_key.get(),
                    "openai_base_url": base_url.get(),
                    "system_prompt": prompt.get("1.0", "end-1c"),
                }
            )
            window.destroy()
            messagebox.showinfo(
                "Phrase Auto-correct",
                "Settings saved.",
                parent=self.root,
            )

        tk.Button(
            buttons,
            text="Cancel",
            command=window.destroy,
            width=10,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            buttons,
            text="Save",
            command=save,
            width=10,
            bg=ACCENT,
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
        ).pack(side="right")

        frame.columnconfigure(1, weight=1)
        window.update_idletasks()
        x = (window.winfo_screenwidth() - window.winfo_reqwidth()) // 2
        y = (window.winfo_screenheight() - window.winfo_reqheight()) // 2
        window.geometry(f"+{max(20, x)}+{max(20, y)}")
        window.lift()
        window.focus_force()
        window.after(
            1200,
            lambda: window.winfo_exists() and window.attributes("-topmost", False),
        )

    def _build_tone_menu(
        self,
        frame: tk.Frame,
        on_tone: Callable[[str], None],
        on_cancel: Callable[[], None],
    ) -> None:
        tk.Label(
            frame,
            text="Tone",
            bg=SURFACE,
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=8,
            pady=4,
        ).pack(fill="x")

        for tone in SUPPORTED_TONES:
            self._menu_button(
                frame,
                tone,
                lambda selected=tone: on_tone(selected),
            ).pack(fill="x")

        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", pady=5)
        self._menu_button(frame, "Cancel", on_cancel).pack(fill="x")

    def _ensure_generation_frame(self) -> tk.Frame:
        if self.shell is None:
            raise RuntimeError("Tone picker must be shown first")
        if self.generation_frame is None:
            self.generation_frame = tk.Frame(
                self.shell,
                bg=SURFACE,
                padx=6,
                pady=6,
                width=430,
            )
            self.generation_frame.grid(row=0, column=1, sticky="nsew")
        return self.generation_frame

    def _panel_header(
        self,
        parent: tk.Frame,
        title: str,
        on_cancel: Callable[[], None],
        on_regenerate: Callable[[], None] | None = None,
    ) -> tk.Frame:
        header = tk.Frame(parent, bg=SURFACE)
        tk.Label(
            header,
            text=title,
            bg=SURFACE,
            fg=TEXT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(8, 4))
        if on_regenerate is not None:
            self._icon_button(header, "↻", on_regenerate).pack(
                side="right",
                padx=(4, 0),
            )
        self._icon_button(header, "×", on_cancel).pack(side="right")
        return header

    def _menu_button(
        self,
        parent: tk.Frame,
        text: str,
        command: Callable[[], None],
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            anchor="w",
            justify="left",
            padx=12,
            pady=7,
            width=18,
            relief="flat",
            takefocus=0,
            cursor="hand2",
            bg=SURFACE,
            fg=TEXT,
            activebackground=SURFACE_HOVER,
            activeforeground=TEXT,
            font=("Segoe UI", 9),
        )

    def _icon_button(
        self,
        parent: tk.Frame,
        text: str,
        command: Callable[[], None],
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=3,
            relief="flat",
            takefocus=0,
            cursor="hand2",
            bg=SURFACE,
            fg=TEXT,
            activebackground=SURFACE_HOVER,
            activeforeground=TEXT,
            font=("Segoe UI Symbol", 11, "bold"),
        )

    def _settings_label(self, parent: tk.Frame, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 9),
            anchor="w",
            padx=0,
            pady=2,
        )

    def _make_palette(self, on_close: Callable[[], None]) -> tk.Toplevel:
        window = tk.Toplevel(self.root)
        window.withdraw()
        window.overrideredirect(True)
        window.configure(bg=BORDER)
        window.attributes("-topmost", True)
        window.protocol("WM_DELETE_WINDOW", on_close)
        try:
            window.attributes("-toolwindow", True)
        except tk.TclError:
            pass
        return window

    def _show_palette(self) -> None:
        if self.window is None:
            return
        self.window.update_idletasks()
        if self.anchor is None:
            self.anchor = self._calculate_anchor(self.window)
        x, y = self.anchor
        self.window.geometry(f"+{x}+{y}")
        make_window_no_activate(int(self.window.winfo_id()))
        self.window.deiconify()
        self.window.lift()
        make_window_no_activate(int(self.window.winfo_id()))

    def _calculate_anchor(self, window: tk.Toplevel) -> tuple[int, int]:
        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()
        cursor_x, cursor_y = get_cursor_position()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = cursor_x + 12 if cursor_x else (screen_width - width) // 2
        y = cursor_y + 12 if cursor_y else (screen_height - height) // 2
        x = max(12, min(x, screen_width - width - 20))
        y = max(12, min(y, screen_height - height - 50))
        return (x, y)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Horizontal.TProgressbar", troughcolor=BG)

    @staticmethod
    def _clear(frame: tk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()
