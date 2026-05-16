"""Windows UI Automation selected text reader."""

from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _load_uia() -> object:
    """Load generated UI Automation COM bindings once per process."""

    import comtypes.client

    comtypes.client.GetModule("UIAutomationCore.dll")
    import comtypes.gen.UIAutomationClient as UIA

    return UIA


def warm_up_uia() -> None:
    """Generate and cache UI Automation bindings before the first hotkey."""

    try:
        _load_uia()
    except Exception:
        return


def read_selected_text() -> str:
    """Read selected text from the focused UI Automation element."""

    try:
        import comtypes
        from comtypes import COMError
        import comtypes.client

        try:
            comtypes.CoInitialize()
            UIA = _load_uia()

            automation = comtypes.client.CreateObject(
                UIA.CUIAutomation,
                interface=UIA.IUIAutomation,
            )
            element = automation.GetFocusedElement()
            if not element:
                return ""

            try:
                pattern = element.GetCurrentPattern(UIA.UIA_TextPatternId)
                text_pattern = pattern.QueryInterface(
                    UIA.IUIAutomationTextPattern
                )
                selections = text_pattern.GetSelection()
            except COMError:
                return ""

            parts: list[str] = []
            for index in range(selections.Length):
                text_range = selections.GetElement(index)
                selected = str(text_range.GetText(-1) or "")
                if selected:
                    parts.append(selected)
            return "\n".join(parts).strip()
        finally:
            comtypes.CoUninitialize()
    except Exception:
        return ""
