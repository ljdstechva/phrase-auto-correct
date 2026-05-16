"""Phrase Auto-correct application entry point."""

from __future__ import annotations

import argparse
from dataclasses import replace
import logging
from pathlib import Path
from queue import Queue
import subprocess
import sys
import threading
import tkinter as tk
from typing import NoReturn, TypeAlias

from . import APP_NAME
from .ai_provider import RewriteEngine, RewriteError
from .clipboard_manager import ClipboardManager
from .config import AppConfig, load_config
from .hotkey import HotkeyListener, parse_hotkey
from .logging_setup import setup_logging
from .selection import CaptureResult, SelectionService
from .single_instance import SingleInstance
from .tray import TrayIcon
from .ui import PopupUI
from .uia_selection import warm_up_uia


CREATE_NEW_CONSOLE = 0x00000010
CaptureMessage: TypeAlias = tuple[str, CaptureResult | str]


class PhraseAutoCorrectApp:
    """Coordinate tray, hotkey, clipboard, UI, and rewrite providers."""

    def __init__(
        self,
        project_root: Path,
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.logger = logger
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(APP_NAME)

        owner_hwnd = int(self.root.winfo_id())
        self.clipboard = ClipboardManager(owner_hwnd)
        self.selection = SelectionService(self.clipboard, config)
        self.rewriter = RewriteEngine(config)
        self.ui = PopupUI(self.root)
        self.capture: CaptureResult | None = None
        self.options: list[str] = []
        self.selected_tone: str | None = None
        self.busy = False
        self.capture_queue: Queue[CaptureMessage] = Queue()

        self.hotkey = HotkeyListener(
            config.hotkey,
            callback=lambda: self.root.after(0, self.on_hotkey),
            on_error=lambda message: self.root.after(
                0,
                lambda: self.show_error(message),
            ),
        )
        self.tray = TrayIcon(
            project_root,
            on_exit=lambda: self.root.after(0, self.shutdown),
            on_uninstall=lambda: self.root.after(0, self.uninstall_from_tray),
        )

    def run(self) -> None:
        """Start background services and enter Tk's event loop."""

        self.logger.info("Starting app")
        self.tray.start()
        self.hotkey.start()
        threading.Thread(
            target=warm_up_uia,
            daemon=True,
            name="PhraseUIAWarmup",
        ).start()
        self.root.mainloop()

    def on_hotkey(self) -> None:
        """Handle Ctrl+Space from the hotkey thread."""

        if self.busy:
            return
        self.busy = True
        self.ui.close()
        threading.Thread(
            target=self._capture_worker,
            daemon=True,
            name="PhraseCaptureWorker",
        ).start()
        self.root.after(30, self._poll_capture_queue)

    def _capture_worker(self) -> None:
        """Capture selected text without blocking the UI thread."""

        try:
            capture = self.selection.capture_selected_text()
        except Exception as exc:
            self.logger.info(
                "Text capture failed: %s: %s",
                type(exc).__name__,
                exc,
            )
            self.capture_queue.put(("error", str(exc)))
            return
        self.capture_queue.put(("capture", capture))

    def _poll_capture_queue(self) -> None:
        """Handle capture completion on the Tk thread."""

        if self.capture_queue.empty():
            if self.busy and self.capture is None:
                self.root.after(30, self._poll_capture_queue)
            return

        kind, payload = self.capture_queue.get()
        if kind == "error":
            self.show_error(str(payload))
            return
        self.capture = payload if isinstance(payload, CaptureResult) else None
        if self.capture is None:
            self.show_error("No text selected.")
            return
        self.ui.show_tone_picker(self.on_tone_selected, self.cancel_flow)

    def on_tone_selected(self, tone: str) -> None:
        """Generate rewrites after the user chooses a tone."""

        capture = self.capture
        if capture is None:
            self.show_error("No text selected.")
            return
        self.selected_tone = tone
        self.ui.show_loading(tone, self.cancel_flow)
        self._start_rewrite_worker(capture.text.strip(), tone)

    def regenerate_options(self) -> None:
        """Generate another set for the current captured text and tone."""

        if self.capture is None or self.selected_tone is None:
            self.show_error("No text selected.")
            return
        self.ui.show_loading(self.selected_tone, self.cancel_flow)
        self._start_rewrite_worker(
            self.capture.text.strip(),
            self.selected_tone,
        )

    def _start_rewrite_worker(self, text: str, tone: str) -> None:
        thread = threading.Thread(
            target=self._generate_options,
            args=(text, tone),
            daemon=True,
            name="PhraseRewriteWorker",
        )
        thread.start()

    def _generate_options(self, text: str, tone: str) -> None:
        try:
            options = self.rewriter.rewrite(text, tone)
        except RewriteError as exc:
            self.logger.info("Rewrite failed: %s", type(exc).__name__)
            self.root.after(0, lambda: self.show_error(str(exc)))
            return
        except Exception as exc:
            self.logger.exception("Unexpected rewrite failure")
            self.root.after(
                0,
                lambda: self.show_error(
                    f"Rewrite failed unexpectedly: {type(exc).__name__}"
                ),
            )
            return
        self.root.after(0, lambda: self.show_options(options))

    def show_options(self, options: list[str]) -> None:
        self.options = options
        self.ui.show_options(
            options,
            self.on_option_selected,
            self.regenerate_options,
            self.cancel_flow,
        )

    def on_option_selected(self, index: int) -> None:
        """Replace the selected text with the chosen option."""

        if self.capture is None or index >= len(self.options):
            self.show_error("The selected rewrite is no longer available.")
            return
        try:
            self.selection.replace_selected_text(
                self.capture,
                self.options[index],
            )
        except Exception as exc:
            self.logger.info("Replacement failed: %s", type(exc).__name__)
            self.show_error(
                "Could not replace the selected text. "
                "The target app may have blocked paste or lost selection."
            )
            return
        self.cancel_flow()

    def cancel_flow(self) -> None:
        """Close active UI and reset current capture state."""

        self.ui.close()
        self.capture = None
        self.options = []
        self.selected_tone = None
        self.busy = False

    def show_error(self, message: str) -> None:
        """Show an error and reset after dismissal."""

        self.ui.show_error(message, self.cancel_flow)

    def uninstall_from_tray(self) -> None:
        """Launch uninstall script from the tray menu after confirmation."""

        if not self.ui.confirm_uninstall():
            return
        uninstall_script = self.project_root / "uninstall.ps1"
        try:
            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(uninstall_script),
                    "-FromTray",
                ],
                cwd=self.project_root,
                creationflags=CREATE_NEW_CONSOLE,
            )
        except OSError as exc:
            self.show_error(f"Could not start uninstall script: {exc}")
            return
        self.shutdown()

    def shutdown(self) -> None:
        """Stop services and close the app."""

        self.logger.info("Shutting down app")
        try:
            self.hotkey.stop()
        finally:
            self.tray.stop()
            self.root.quit()
            self.root.destroy()


def self_test(project_root: Path) -> int:
    """Validate core non-interactive pieces."""

    config = load_config(project_root)
    parse_hotkey(config.hotkey)
    test_config = replace(config, ai_provider="fallback")
    options = RewriteEngine(test_config).rewrite(
        "i need this report finish today because client waiting",
        "Formal",
    )
    if len(options) != 3:
        raise RuntimeError("Rewrite engine did not return three options")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=APP_NAME)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_root = Path(__file__).resolve().parents[1]
    if args.self_test:
        return self_test(project_root)

    config = load_config(project_root)
    logger = setup_logging(project_root, config.debug_logging)
    instance = SingleInstance("Local\\PhraseAutoCorrect")
    if not instance.acquire():
        logger.info("Another instance is already running")
        return 0

    try:
        app = PhraseAutoCorrectApp(project_root, config, logger)
        app.run()
    finally:
        instance.release()
    return 0


def run() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    run()
