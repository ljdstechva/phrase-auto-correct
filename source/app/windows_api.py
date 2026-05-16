"""Small Win32 API wrapper layer used by the app."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Iterable


user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12
VK_LWIN = 0x5B
VK_C = 0x43
VK_V = 0x56
VK_SPACE = 0x20

KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1
SW_RESTORE = 9

WM_QUIT = 0x0012

ERROR_ALREADY_EXISTS = 183
GWL_EXSTYLE = -20
HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

if ctypes.sizeof(ctypes.c_void_p) == 8:
    ULONG_PTR = ctypes.c_ulonglong
    LONG_PTR = ctypes.c_longlong
else:
    ULONG_PTR = ctypes.c_ulong
    LONG_PTR = ctypes.c_long


class POINT(ctypes.Structure):
    _fields_ = (("x", wintypes.LONG), ("y", wintypes.LONG))


class GUITHREADINFO(ctypes.Structure):
    _fields_ = (
        ("cbSize", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("hwndActive", wintypes.HWND),
        ("hwndFocus", wintypes.HWND),
        ("hwndCapture", wintypes.HWND),
        ("hwndMenuOwner", wintypes.HWND),
        ("hwndMoveSize", wintypes.HWND),
        ("hwndCaret", wintypes.HWND),
        ("rcCaret", wintypes.RECT),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    )


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = (
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    )


class INPUT_UNION(ctypes.Union):
    _fields_ = (
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    )


class INPUT(ctypes.Structure):
    _fields_ = (("type", wintypes.DWORD), ("union", INPUT_UNION))


user32.SendInput.argtypes = (
    wintypes.UINT,
    ctypes.POINTER(INPUT),
    ctypes.c_int,
)
user32.SendInput.restype = wintypes.UINT
user32.GetForegroundWindow.argtypes = ()
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = (wintypes.HWND,)
user32.BringWindowToTop.restype = wintypes.BOOL
user32.SetFocus.argtypes = (wintypes.HWND,)
user32.SetFocus.restype = wintypes.HWND
user32.IsWindow.argtypes = (wintypes.HWND,)
user32.IsWindow.restype = wintypes.BOOL
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.ShowWindow.restype = wintypes.BOOL
user32.GetCursorPos.argtypes = (ctypes.POINTER(POINT),)
user32.GetCursorPos.restype = wintypes.BOOL
user32.GetClipboardSequenceNumber.argtypes = ()
user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetWindowThreadProcessId.argtypes = (
    wintypes.HWND,
    ctypes.POINTER(wintypes.DWORD),
)
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetGUIThreadInfo.argtypes = (
    wintypes.DWORD,
    ctypes.POINTER(GUITHREADINFO),
)
user32.GetGUIThreadInfo.restype = wintypes.BOOL
user32.AttachThreadInput.argtypes = (
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.BOOL,
)
user32.AttachThreadInput.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = (
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
)
user32.SetWindowPos.restype = wintypes.BOOL

if hasattr(user32, "GetWindowLongPtrW"):
    _get_window_long_ptr = user32.GetWindowLongPtrW
    _set_window_long_ptr = user32.SetWindowLongPtrW
else:
    _get_window_long_ptr = user32.GetWindowLongW
    _set_window_long_ptr = user32.SetWindowLongW

_get_window_long_ptr.argtypes = (wintypes.HWND, ctypes.c_int)
_get_window_long_ptr.restype = LONG_PTR
_set_window_long_ptr.argtypes = (wintypes.HWND, ctypes.c_int, LONG_PTR)
_set_window_long_ptr.restype = LONG_PTR

kernel32.GetCurrentThreadId.argtypes = ()
kernel32.GetCurrentThreadId.restype = wintypes.DWORD
kernel32.CreateMutexW.argtypes = (
    wintypes.LPVOID,
    wintypes.BOOL,
    wintypes.LPCWSTR,
)
kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.ReleaseMutex.argtypes = (wintypes.HANDLE,)
kernel32.ReleaseMutex.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.CloseHandle.restype = wintypes.BOOL


def get_last_error() -> int:
    """Return the last Win32 error for the current thread."""

    return ctypes.get_last_error()


def make_key_input(vk_code: int, key_up: bool = False) -> INPUT:
    """Create a keyboard INPUT structure."""

    flags = KEYEVENTF_KEYUP if key_up else 0
    return INPUT(
        type=INPUT_KEYBOARD,
        union=INPUT_UNION(
            ki=KEYBDINPUT(
                wVk=vk_code,
                wScan=0,
                dwFlags=flags,
                time=0,
                dwExtraInfo=0,
            )
        ),
    )


def send_key_combo(modifiers: Iterable[int], key: int) -> None:
    """Inject a key combination such as Ctrl+C or Ctrl+V."""

    modifier_list = list(modifiers)
    events: list[INPUT] = []
    for modifier in modifier_list:
        events.append(make_key_input(modifier))
    events.append(make_key_input(key))
    events.append(make_key_input(key, key_up=True))
    for modifier in reversed(modifier_list):
        events.append(make_key_input(modifier, key_up=True))

    array_type = INPUT * len(events)
    event_array = array_type(*events)
    sent = user32.SendInput(
        len(events),
        event_array,
        ctypes.sizeof(INPUT),
    )
    if sent != len(events):
        raise OSError(get_last_error(), "SendInput did not send all events")


def send_copy() -> None:
    """Send Ctrl+C."""

    send_key_combo([VK_CONTROL], VK_C)


def send_paste() -> None:
    """Send Ctrl+V."""

    send_key_combo([VK_CONTROL], VK_V)


def get_foreground_window() -> int:
    """Return the current foreground HWND."""

    return int(user32.GetForegroundWindow() or 0)


def get_focus_window_for_thread(hwnd: int) -> int:
    """Return the focused child HWND for a foreground window's UI thread."""

    if not hwnd:
        return 0
    thread_id = user32.GetWindowThreadProcessId(hwnd, None)
    if not thread_id:
        return 0
    info = GUITHREADINFO()
    info.cbSize = ctypes.sizeof(GUITHREADINFO)
    if not user32.GetGUIThreadInfo(thread_id, ctypes.byref(info)):
        return 0
    return int(info.hwndFocus or info.hwndActive or 0)


def make_window_no_activate(hwnd: int) -> bool:
    """Make a popup visible without activating or stealing focus."""

    if not hwnd:
        return False
    ex_style = int(_get_window_long_ptr(hwnd, GWL_EXSTYLE))
    new_style = ex_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
    _set_window_long_ptr(hwnd, GWL_EXSTYLE, LONG_PTR(new_style))
    return bool(
        user32.SetWindowPos(
            hwnd,
            HWND_TOPMOST,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )
    )


def focus_window(hwnd: int, focus_hwnd: int = 0) -> bool:
    """Try to restore and focus a target window."""

    if not hwnd or not user32.IsWindow(hwnd):
        return False

    current_thread = kernel32.GetCurrentThreadId()
    target_thread = user32.GetWindowThreadProcessId(hwnd, None)
    foreground = user32.GetForegroundWindow()
    foreground_thread = user32.GetWindowThreadProcessId(foreground, None)

    attached: list[tuple[int, int]] = []
    for other_thread in {int(target_thread), int(foreground_thread)}:
        if other_thread and other_thread != int(current_thread):
            if user32.AttachThreadInput(current_thread, other_thread, True):
                attached.append((int(current_thread), other_thread))

    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    try:
        user32.BringWindowToTop(hwnd)
        focused = bool(user32.SetForegroundWindow(hwnd))
        if focus_hwnd and user32.IsWindow(focus_hwnd):
            user32.SetFocus(focus_hwnd)
        return focused or user32.GetForegroundWindow() == hwnd
    finally:
        for source_thread, target_thread in attached:
            user32.AttachThreadInput(source_thread, target_thread, False)


def get_cursor_position() -> tuple[int, int]:
    """Return the current cursor coordinates."""

    point = POINT()
    if not user32.GetCursorPos(ctypes.byref(point)):
        return (0, 0)
    return (int(point.x), int(point.y))


def get_clipboard_sequence_number() -> int:
    """Return the clipboard sequence number."""

    return int(user32.GetClipboardSequenceNumber())


def is_key_down(vk_code: int) -> bool:
    """Return True when the high-order async key-state bit is set."""

    return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)


def wait_for_keys_released(
    vk_codes: Iterable[int],
    timeout_ms: int = 300,
) -> bool:
    """Wait briefly for physical hotkey keys to be released."""

    import time

    keys = tuple(vk_codes)
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if not any(is_key_down(key) for key in keys):
            return True
        time.sleep(0.01)
    return False
