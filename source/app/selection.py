"""Selected text capture and replacement flow."""

from __future__ import annotations

from dataclasses import dataclass
import time

from .clipboard_manager import (
    ClipboardError,
    ClipboardManager,
    ClipboardSnapshot,
)
from .config import AppConfig
from .uia_selection import read_selected_text
from .windows_api import (
    VK_CONTROL,
    VK_SPACE,
    focus_window,
    get_focus_window_for_thread,
    get_clipboard_sequence_number,
    get_foreground_window,
    send_copy,
    send_paste,
    wait_for_keys_released,
)


@dataclass(frozen=True)
class CaptureResult:
    """Captured selection and its original clipboard state."""

    text: str
    original_clipboard: ClipboardSnapshot
    target_hwnd: int
    focus_hwnd: int


class SelectionService:
    """Capture selected text and replace it through the clipboard."""

    def __init__(
        self,
        clipboard: ClipboardManager,
        config: AppConfig,
    ) -> None:
        self.clipboard = clipboard
        self.config = config

    def capture_selected_text(self) -> CaptureResult:
        """Copy selected text from the foreground app."""

        target_hwnd = get_foreground_window()
        focus_hwnd = get_focus_window_for_thread(target_hwnd)
        wait_for_keys_released((VK_CONTROL, VK_SPACE), timeout_ms=320)
        snapshot = self.clipboard.snapshot_text_only()
        text = read_selected_text()
        if text:
            return self._validate_capture_text(
                text,
                snapshot,
                target_hwnd,
                focus_hwnd,
            )

        return self._capture_selected_text_from_clipboard(
            snapshot,
            target_hwnd,
            focus_hwnd,
        )

    def _capture_selected_text_from_clipboard(
        self,
        snapshot: ClipboardSnapshot,
        target_hwnd: int,
        focus_hwnd: int,
    ) -> CaptureResult:
        """Fallback capture using Ctrl+C and the clipboard."""

        text = ""
        try:
            sequence = get_clipboard_sequence_number()
            send_copy()
            changed = self._wait_for_clipboard_change(sequence)
            text = self.clipboard.get_text()
            if not changed and not text:
                text = ""
        finally:
            self._restore_best_effort(snapshot)

        return self._validate_capture_text(
            text,
            snapshot,
            target_hwnd,
            focus_hwnd,
        )

    def _validate_capture_text(
        self,
        text: str,
        snapshot: ClipboardSnapshot,
        target_hwnd: int,
        focus_hwnd: int,
    ) -> CaptureResult:
        if not text or not text.strip():
            raise ValueError("No text selected.")
        if len(text.strip()) > self.config.max_text_length:
            raise ValueError(
                "Selected text is too long. "
                f"Limit: {self.config.max_text_length} characters."
            )
        return CaptureResult(text, snapshot, target_hwnd, focus_hwnd)

    def replace_selected_text(
        self,
        capture: CaptureResult,
        replacement: str,
    ) -> None:
        """Paste the chosen rewrite over the original selection."""

        final_text = preserve_outer_spacing(capture.text, replacement)
        try:
            if get_foreground_window() != capture.target_hwnd:
                focus_window(capture.target_hwnd, capture.focus_hwnd)
                time.sleep(0.12)
            else:
                time.sleep(0.03)
            self.clipboard.set_text(final_text)
            send_paste()
            time.sleep(self.config.paste_restore_delay_ms / 1000)
        finally:
            self._restore_best_effort(capture.original_clipboard)

    def _wait_for_clipboard_change(self, previous_sequence: int) -> bool:
        timeout_at = time.monotonic() + self.config.copy_timeout_ms / 1000
        while time.monotonic() < timeout_at:
            if get_clipboard_sequence_number() != previous_sequence:
                return True
            time.sleep(0.025)
        return False

    def _restore_best_effort(self, snapshot: ClipboardSnapshot) -> bool:
        if not snapshot.formats and not snapshot.skipped_formats:
            return True
        for delay in (0.0, 0.05, 0.15):
            if delay:
                time.sleep(delay)
            try:
                return self.clipboard.restore(snapshot)
            except ClipboardError:
                continue
        return False


def preserve_outer_spacing(original: str, replacement: str) -> str:
    """Keep whitespace that was included around the original selection."""

    leading_len = len(original) - len(original.lstrip())
    trailing_len = len(original) - len(original.rstrip())
    prefix = original[:leading_len]
    suffix = original[len(original) - trailing_len :] if trailing_len else ""
    return f"{prefix}{replacement.strip()}{suffix}"
