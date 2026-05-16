# Architecture

## Folder Layout

The parent folder is intentionally simple for users:

- `install.ps1`: primary installer wrapper.
- `install.bat`: double-click installer wrapper.
- `README.md`: short install instructions.
- `source\`: app implementation, configuration, scripts, virtual environment, logs, tests, and screenshots.

The wrappers call `source\install.ps1` so installation still runs from the clean parent folder while all generated app files stay under `source\`.

## Modules

- `app/main.py`: application controller, lifecycle, hotkey flow, tray callbacks.
- `app/config.py`: config defaults and `config.json` loading.
- `app/windows_api.py`: Win32 API wrappers for hotkeys, keyboard input, foreground window, cursor, mutex, and clipboard sequence numbers.
- `app/clipboard_manager.py`: clipboard snapshot, restore, text read/write.
- `app/selection.py`: selected text capture and replacement orchestration.
- `app/hotkey.py`: global hotkey parser and listener thread.
- `app/ui.py`: Tkinter tone selection, loading, option, and error popups.
- `app/tray.py`: pystray icon and right-click menu.
- `app/ai_provider.py`: provider interface, Ollama provider, and local fallback provider.
- `app/logging_setup.py`: local rotating log setup.
- `app/single_instance.py`: named mutex to avoid duplicate app instances.

## User Flow

1. App starts hidden and creates a tray icon.
2. Hotkey listener registers Ctrl+Space.
3. User selects text in another app and presses Ctrl+Space.
4. App remembers the foreground window handle and the focused control handle when Windows exposes one.
5. App captures selected text before showing UI. It tries Windows UI Automation first, then falls back to Ctrl+C and the clipboard.
6. If no text was captured, the app shows `No text selected.`
7. App shows a non-activating context-menu-style tone palette.
8. User picks a tone.
9. App opens one generation panel beside the tone menu and asks the configured rewrite provider for exactly three options.
10. App shows three options with check icons and one recycle icon.
11. User clicks a check icon to replace, or the recycle icon to regenerate.
12. If the original app is still foreground, the app leaves focus alone, puts the rewrite on the clipboard, sends Ctrl+V, waits briefly, restores the prior clipboard snapshot, and closes the popup. If focus moved, it restores the original app and focused control first.

## AI Provider Interface

Providers expose:

```python
rewrite(text: str, tone: str) -> list[str]
```

Rules enforced by providers and validation:

- Return exactly three non-empty strings.
- Preserve meaning.
- Avoid changing names, numbers, links, dates, and technical terms.
- Do not log selected text.

Configured providers:

- `fallback`: deterministic offline provider.
- `ollama`: local Ollama HTTP provider.
- `auto`: default; try local Ollama with `qwen3.5:9b` if available, otherwise fall back locally.

The Ollama prompt asks the model to internally analyze the user's intent, message type, protected terms, and grammar issues before writing. The analysis is not returned to the UI; only the three final rewrite options are parsed.

## Clipboard Handling

The app uses a fast text-only clipboard snapshot during hotkey capture, then restores it after the Ctrl+C fallback. Replacement restores the same original clipboard snapshot after paste. If a clipboard format cannot be copied safely, it is skipped and not logged with content. The paste path avoids changing focus when the original app remains foreground, which is the expected path for the non-activating palette.

## Hotkey Handling

`RegisterHotKey` runs in a background thread with a message loop. Ctrl+Space is the default. If registration fails, the app displays an error and the user can edit `config.json`.

## UI Flow

Tkinter stays on the main thread. Long-running rewrite calls run in worker threads and return to Tkinter through `root.after`.

Hotkey capture also runs in a worker thread so the Tk event loop does not freeze while Windows clipboard or UI Automation calls complete. AI generation is not started during hotkey handling; it starts only after the user left-clicks a tone.

The palette is intentionally non-activating:

- It uses `overrideredirect(True)` so it behaves more like a context menu than a normal dialog.
- It applies the Win32 `WS_EX_NOACTIVATE` extended style.
- It avoids `focus_force()`.
- It is positioned near the cursor and kept topmost.

Palette states:

- tone chooser
- side-by-side loading panel after tone selection
- side-by-side rewrite options with check icons
- error message

## Tray Menu Behavior

Right-click tray menu:

- `Uninstall`: confirms with the user, launches `uninstall.ps1`, then exits.
- `Exit`: stops the tray icon, unregisters the hotkey, and exits the Tk loop.

## Startup Behavior

The parent `install.ps1` wrapper forwards supported switches to `source\install.ps1`. The source installer creates a per-user Startup folder shortcut named `Phrase Auto-correct.lnk` that targets `source\.venv\Scripts\pythonw.exe` and runs `-m app.main` with `source\` as the working directory.

`source\uninstall.ps1` removes only this shortcut and stops only Python processes whose command line points to this project folder and `app.main`.

## Install-Time AI Model Setup

`install.ps1` can optionally pull the configured recommended model through Ollama:

- Interactive install asks whether to download `qwen3.5:9b`.
- `-PullModel` pulls without asking.
- `-SkipModelPrompt` skips the prompt.
- `-InstallOllamaWithWinget` lets the installer offer WinGet installation if Ollama is not found.

The model pull uses the official `ollama pull` command and does not change Windows networking settings. Download speed is left to Ollama and the user's network.

## Error Handling

- No selected text: show `No text selected.`
- Too long: show max length error.
- Clipboard locked or blocked: show helpful clipboard error.
- Hotkey conflict: show hotkey registration error and config guidance.
- AI backend failure: show backend error for `ollama`; for `auto`, use fallback.
- Replacement blocked: show replacement error and restore clipboard snapshot if possible.
