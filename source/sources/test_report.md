# Test Report

Test date: 2026-05-16

| Test | Result | Notes |
| --- | --- | --- |
| Python syntax compile | Pass | `python -m compileall app sources\tests` completed successfully. |
| Unit tests | Pass | 9 tests passed with `python -m unittest discover -s sources\tests -v`. |
| Clipboard set/read/restore | Pass | Unit test temporarily set text, read it back, and restored the prior snapshot. |
| Fallback rewrite quality sample | Pass | Sample sentence becomes `I need this report finished today because the client is waiting.` and returns exactly three options. |
| Number/date preservation | Pass | Unit test confirmed `3` and `May 20` remain in all fallback options. |
| Hotkey parser | Pass | `Ctrl+Space`, `Ctrl+Shift+F9`, and invalid hotkey cases tested. |
| App self-test | Pass | `.venv\Scripts\python.exe -m app.main --self-test` completed successfully and now uses the fallback provider so it does not depend on Ollama availability. |
| Local Ollama availability | Not installed | `ollama` was not found on PATH, so the app will use the local fallback until Ollama is installed and `qwen3.5:9b` is pulled. |
| Install script | Pass | `install.ps1` created `.venv`, installed dependencies locally, registered Startup shortcut, and started the app. |
| Install model skip mode | Pass | `install.ps1 -SkipModelPrompt` completed successfully without attempting the 6.6 GB model download. |
| Clean parent folder layout | Pass | Parent folder now contains only `install.ps1`, `install.bat`, `README.md`, hidden `.gitignore`, and `source\`. App source, scripts, config, virtual environment, logs, tests, and screenshots are inside `source\`. |
| Root PowerShell installer wrapper | Pass | Parent `install.ps1 -SkipModelPrompt` forwards named parameters to `source\install.ps1` and completed successfully after fixing positional argument forwarding. |
| Batch installer argument forwarding | Pass | Parent `install.bat -SkipModelPrompt` forwarded arguments to PowerShell and completed successfully from the simplified parent folder. |
| Install model selection | Pass | Installer now supports interactive model selection, `-PullModel`, `-SkipModelPrompt`, and optional `-InstallOllamaWithWinget`. |
| Run script idempotency | Pass | Running `run.ps1` again reported the app was already running. |
| Startup registration | Pass | Startup shortcut exists and points to `source\.venv\Scripts\pythonw.exe -m app.main` with `source\` as the working directory. |
| Running process | Pass | App is running under `pythonw.exe`; Windows shows a venv launcher process plus the base Python process for one logical app launch. |
| Default hotkey ownership | Pass | A second test registration for `Ctrl+Space` failed with Win32 `1409`, confirming the hotkey is already registered while the app is running. |
| Uninstall script | Pass | `uninstall.ps1` removed the Startup shortcut and stopped only app-owned Python processes, then the app was reinstalled. |
| Folder boundary | Pass | Source, tests, logs, cache, and generated files are inside this project folder. Only the app Startup shortcut was created outside. |
| Sensitive text logging | Pass | Logs contain lifecycle and error class/message only; selected text is not logged. |
| Context-menu-style palette compile | Pass | New non-activating palette compiled successfully after replacing the focused dialog UI. |
| Default model config | Pass | Default config now uses `aiProvider: auto` and `ollamaModel: qwen3.5:9b`. |
| Non-blocking hotkey capture | Pass | Capture now runs on `PhraseCaptureWorker`; Tkinter stays on the main thread and no rewrite work starts during hotkey handling. |
| UI Automation selection capture | Pass | Added UI Automation selected-text reader before the Ctrl+C fallback and warmed up UIA bindings after startup. |
| Tone-first generation | Pass | AI generation starts only after a left-click tone selection. Hotkey handling shows the tone palette only after capture succeeds. |
| Ollama rewrite payload | Pass | Ollama requests use `stream: false`, JSON format, `think: false`, and an intent-analysis prompt before final rewriting. |
| Screenshot: selected text retained | Pass | `sources/screenshots/capture-worker-tone-palette.png` shows the selected sample phrase still highlighted with the tone palette open. |
| Screenshot: single generation panel | Pass | `sources/screenshots/generation-panel-options.png` shows one side panel with three rewrite options, check icons, and a recycle icon. |
| Focus-safe paste path | Pass | Replacement now avoids refocusing when the target app is still foreground and stores the focused control handle for fallback focus restore. |
| Full foreground editor flow | Pass | Automated foreground editor test selected text, triggered Ctrl+Space, clicked Formal, generated three options, clicked the first replace icon, and verified the selected text changed to `I need this report finished today because the client is waiting.` |
| Screenshot: full hotkey tone palette | Pass | `sources/screenshots/full-check-hotkey-tone-palette.png` shows the real hotkey-triggered tone palette over selected text. |
| Screenshot: full generated options | Pass | `sources/screenshots/full-check-generated-options.png` shows the generated side panel from the running tray app. |
| Screenshot: full replacement result | Pass | `sources/screenshots/full-check-after-replace.png` shows the text replaced in the foreground editor. |
| Tray icon visual verification | Partial | App process starts with pystray and `icon.jpg` loader code. Visual tray inspection is not available from this shell. |
| Tray Exit menu | Partial | Shutdown path exists and process stop was verified through uninstall/run scripts. Direct tray menu clicking is not available from this shell. |
| Tray Uninstall menu | Partial | Tray callback launches `uninstall.ps1` after confirmation. The script itself was verified; direct tray menu clicking is not available from this shell. |
| Full hotkey-to-popup automation | Pass | Synthetic Ctrl+Space against a foreground selected Tk text editor triggered the running tray app and showed the tone palette without clearing the selection. Screenshot: `sources/screenshots/global-hotkey-tone-palette.png`. |
| Notepad capture/replace automation | Partial | Foreground Tk editor automation passed. Automated Notepad selection/copy remains unreliable in this shell because Windows Notepad did not consistently route simulated Ctrl+A/C to the editor control. |

## Fixes Made During Testing

- Added `AttachThreadInput`, `BringWindowToTop`, and focused-control restore to the focus helper.
- Increased clipboard open retry tolerance.
- Made clipboard restoration best effort after copy/paste so a delayed clipboard lock does not abort an otherwise successful operation.
- Added a short wait for Ctrl+Space release before capture.
- Added a UI Automation selected-text reader before clipboard fallback.
- Moved selection capture from the Tk thread to a capture worker thread.
- Warmed up UI Automation bindings after startup to reduce first-hotkey setup cost.
- Replaced normal focus-stealing Tk dialogs with a non-activating context-menu-style palette.
- Added side-by-side tone menu and generation panel.
- Added check icons for replacement and a recycle icon for regeneration.
- Updated the recommended local AI model to `qwen3.5:9b` through Ollama, with fallback when Ollama is unavailable.
- Updated the Ollama prompt so it analyzes intent, message type, protected terms, and grammar issues before producing the three rewrite options.
- Added optional install-time `qwen3.5:9b` download through the official `ollama pull` command.
- Added installer switches: `-PullModel`, `-SkipModelPrompt`, and `-InstallOllamaWithWinget`.
- Moved implementation files into `source\` and added parent-folder install wrappers.
- Fixed parent `install.ps1` wrapper so switch parameters are forwarded by name instead of accidentally becoming the Ollama model argument.
- Removed the old parent `.venv` after confirming the new `source\.venv` install, startup shortcut, app startup, and live replacement flow worked.

## Remaining Manual Verification

Use a normal foreground editable app, select text manually, press `Ctrl+Space`, choose a tone, and select an option. The full automated foreground-editor flow passed, but a final manual check in the user's preferred target app is still useful because Windows apps vary in how they expose selected text and accept pasted replacement text.
