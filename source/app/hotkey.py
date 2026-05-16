"""Global hotkey registration and listener thread."""

from __future__ import annotations

import ctypes
import threading
from ctypes import wintypes
from typing import Callable

from .windows_api import get_last_error, kernel32, user32, WM_QUIT


MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312
HOTKEY_ID = 0x5041

MODIFIER_NAMES = {
    "ctrl": MOD_CONTROL,
    "control": MOD_CONTROL,
    "alt": MOD_ALT,
    "shift": MOD_SHIFT,
    "win": MOD_WIN,
    "windows": MOD_WIN,
}

KEY_NAMES = {
    "space": 0x20,
    "spacebar": 0x20,
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}

for index in range(1, 25):
    KEY_NAMES[f"f{index}"] = 0x70 + index - 1


user32.RegisterHotKey.argtypes = (
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
)
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
user32.UnregisterHotKey.restype = wintypes.BOOL
user32.GetMessageW.argtypes = (
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
)
user32.GetMessageW.restype = ctypes.c_int
user32.PostThreadMessageW.argtypes = (
    wintypes.DWORD,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)
user32.PostThreadMessageW.restype = wintypes.BOOL


class HotkeyError(ValueError):
    """Raised for invalid or unavailable hotkey configuration."""


class HotkeyListener:
    """Register and listen for a single Windows global hotkey."""

    def __init__(
        self,
        hotkey: str,
        callback: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> None:
        self.hotkey = hotkey
        self.callback = callback
        self.on_error = on_error
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._stop_event = threading.Event()
        self._registered = False

    def start(self) -> None:
        """Start the hotkey message loop."""

        self._thread = threading.Thread(
            target=self._run,
            name="PhraseHotkeyListener",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop the hotkey message loop."""

        self._stop_event.set()
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run(self) -> None:
        try:
            modifiers, vk_code = parse_hotkey(self.hotkey)
        except HotkeyError as exc:
            self.on_error(str(exc))
            return

        self._thread_id = int(kernel32.GetCurrentThreadId())
        flags = modifiers | MOD_NOREPEAT
        if not user32.RegisterHotKey(None, HOTKEY_ID, flags, vk_code):
            error = get_last_error()
            self.on_error(
                f"Could not register hotkey {self.hotkey} "
                f"(Win32 {error}). Edit config.json to change it."
            )
            return

        self._registered = True
        msg = wintypes.MSG()
        try:
            while not self._stop_event.is_set():
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result in (0, -1):
                    break
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    self.callback()
        finally:
            if self._registered:
                user32.UnregisterHotKey(None, HOTKEY_ID)
                self._registered = False


def parse_hotkey(hotkey: str) -> tuple[int, int]:
    """Parse hotkey text such as Ctrl+Space into Win32 flags."""

    parts = [part.strip().lower() for part in hotkey.split("+")]
    parts = [part for part in parts if part]
    if len(parts) < 2:
        raise HotkeyError("Hotkey must include a modifier and a key.")

    key_name = parts[-1]
    modifiers = 0
    for part in parts[:-1]:
        try:
            modifiers |= MODIFIER_NAMES[part]
        except KeyError as exc:
            raise HotkeyError(f"Unsupported hotkey modifier: {part}") from exc

    if not modifiers:
        raise HotkeyError("Hotkey must include Ctrl, Alt, Shift, or Win.")

    vk_code = _parse_key(key_name)
    return modifiers, vk_code


def _parse_key(key_name: str) -> int:
    if key_name in KEY_NAMES:
        return KEY_NAMES[key_name]
    if len(key_name) == 1 and key_name.isalpha():
        return ord(key_name.upper())
    if len(key_name) == 1 and key_name.isdigit():
        return ord(key_name)
    raise HotkeyError(f"Unsupported hotkey key: {key_name}")
