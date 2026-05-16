"""Clipboard snapshot and Unicode text operations."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import ctypes
import time
from typing import Iterator

from ctypes import wintypes

from .windows_api import get_last_error, kernel32, user32


CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
GMEM_ZEROINIT = 0x0040


user32.OpenClipboard.argtypes = (wintypes.HWND,)
user32.OpenClipboard.restype = wintypes.BOOL
user32.CloseClipboard.argtypes = ()
user32.CloseClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.argtypes = ()
user32.EmptyClipboard.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = (wintypes.UINT,)
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = (wintypes.UINT, wintypes.HANDLE)
user32.SetClipboardData.restype = wintypes.HANDLE
user32.EnumClipboardFormats.argtypes = (wintypes.UINT,)
user32.EnumClipboardFormats.restype = wintypes.UINT
user32.IsClipboardFormatAvailable.argtypes = (wintypes.UINT,)
user32.IsClipboardFormatAvailable.restype = wintypes.BOOL

kernel32.GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalSize.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalSize.restype = ctypes.c_size_t
kernel32.GlobalFree.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalFree.restype = wintypes.HGLOBAL


class ClipboardError(RuntimeError):
    """Raised when clipboard access fails."""


@dataclass(frozen=True)
class ClipboardFormat:
    """A best-effort backup of one global-memory clipboard format."""

    format_id: int
    data: bytes


@dataclass(frozen=True)
class ClipboardSnapshot:
    """Clipboard backup used for restoration."""

    formats: tuple[ClipboardFormat, ...]
    skipped_formats: tuple[int, ...]


class ClipboardManager:
    """Read, write, snapshot, and restore Windows clipboard data."""

    def __init__(self, owner_hwnd: int) -> None:
        self.owner_hwnd = owner_hwnd

    @contextmanager
    def _open(
        self,
        owner_hwnd: int = 0,
        timeout_ms: int = 300,
    ) -> Iterator[None]:
        last_error = 0
        deadline = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < deadline:
            if user32.OpenClipboard(owner_hwnd):
                try:
                    yield
                finally:
                    user32.CloseClipboard()
                return
            last_error = get_last_error()
            time.sleep(0.01)
        raise ClipboardError(f"Could not open clipboard (Win32 {last_error})")

    def snapshot(self) -> ClipboardSnapshot:
        """Copy clipboard formats that expose global-memory handles."""

        formats: list[ClipboardFormat] = []
        skipped: list[int] = []
        with self._open(self.owner_hwnd, timeout_ms=500):
            format_id = 0
            while True:
                ctypes.set_last_error(0)
                format_id = int(user32.EnumClipboardFormats(format_id))
                if format_id == 0:
                    break
                data = self._read_format_bytes(format_id)
                if data is None:
                    skipped.append(format_id)
                else:
                    formats.append(ClipboardFormat(format_id, data))
        return ClipboardSnapshot(tuple(formats), tuple(skipped))

    def snapshot_text_only(self) -> ClipboardSnapshot:
        """Fast backup of Unicode text only for hotkey capture."""

        try:
            data = self._read_unicode_text_bytes()
        except ClipboardError:
            return ClipboardSnapshot((), ())
        if data is None:
            return ClipboardSnapshot((), ())
        return ClipboardSnapshot((ClipboardFormat(CF_UNICODETEXT, data),), ())

    def clear(self) -> None:
        """Clear the clipboard with this app as owner."""

        with self._open(self.owner_hwnd):
            if not user32.EmptyClipboard():
                raise ClipboardError(
                    f"Could not clear clipboard (Win32 {get_last_error()})"
                )

    def get_text(self) -> str:
        """Read CF_UNICODETEXT from the clipboard if available."""

        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return ""

        with self._open(self.owner_hwnd):
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return ""
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                return ""
            try:
                return ctypes.wstring_at(pointer)
            finally:
                kernel32.GlobalUnlock(handle)

    def set_text(self, text: str) -> None:
        """Place Unicode text on the clipboard."""

        encoded = (text + "\0").encode("utf-16-le")
        with self._open(self.owner_hwnd):
            if not user32.EmptyClipboard():
                raise ClipboardError(
                    f"Could not clear clipboard (Win32 {get_last_error()})"
                )
            handle = self._alloc_bytes(encoded)
            if not user32.SetClipboardData(CF_UNICODETEXT, handle):
                error = get_last_error()
                kernel32.GlobalFree(handle)
                raise ClipboardError(
                    f"Could not set clipboard text (Win32 {error})"
                )

    def restore(self, snapshot: ClipboardSnapshot) -> bool:
        """Restore backed-up formats. Returns False if any format failed."""

        success = True
        with self._open(self.owner_hwnd, timeout_ms=500):
            if not user32.EmptyClipboard():
                raise ClipboardError(
                    f"Could not clear clipboard (Win32 {get_last_error()})"
                )
            for item in snapshot.formats:
                handle = self._alloc_bytes(item.data)
                if not user32.SetClipboardData(item.format_id, handle):
                    kernel32.GlobalFree(handle)
                    success = False
        return success and not snapshot.skipped_formats

    def _read_format_bytes(self, format_id: int) -> bytes | None:
        handle = user32.GetClipboardData(format_id)
        if not handle:
            return None
        size = int(kernel32.GlobalSize(handle))
        if size <= 0 or size > 50_000_000:
            return None
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return None
        try:
            return ctypes.string_at(pointer, size)
        finally:
            kernel32.GlobalUnlock(handle)

    def _read_unicode_text_bytes(self) -> bytes | None:
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        with self._open(self.owner_hwnd):
            return self._read_format_bytes(CF_UNICODETEXT)

    @staticmethod
    def _alloc_bytes(data: bytes) -> int:
        handle = kernel32.GlobalAlloc(
            GMEM_MOVEABLE | GMEM_ZEROINIT,
            len(data),
        )
        if not handle:
            raise ClipboardError(
                f"GlobalAlloc failed (Win32 {get_last_error()})"
            )
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            error = get_last_error()
            kernel32.GlobalFree(handle)
            raise ClipboardError(f"GlobalLock failed (Win32 {error})")
        try:
            ctypes.memmove(pointer, data, len(data))
        finally:
            kernel32.GlobalUnlock(handle)
        return int(handle)
