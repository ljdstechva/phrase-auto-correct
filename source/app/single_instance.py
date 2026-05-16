"""Single-instance guard using a Windows named mutex."""

from __future__ import annotations

from dataclasses import dataclass

from .windows_api import (
    ERROR_ALREADY_EXISTS,
    get_last_error,
    kernel32,
)


@dataclass
class SingleInstance:
    """Own a named mutex for the app process lifetime."""

    name: str
    handle: int | None = None
    already_running: bool = False

    def acquire(self) -> bool:
        """Acquire the app mutex; return False when another instance exists."""

        handle = kernel32.CreateMutexW(None, True, self.name)
        self.handle = int(handle or 0)
        if not self.handle:
            raise OSError(get_last_error(), "CreateMutexW failed")
        self.already_running = get_last_error() == ERROR_ALREADY_EXISTS
        return not self.already_running

    def release(self) -> None:
        """Release and close the mutex handle."""

        if self.handle:
            kernel32.ReleaseMutex(self.handle)
            kernel32.CloseHandle(self.handle)
            self.handle = None
