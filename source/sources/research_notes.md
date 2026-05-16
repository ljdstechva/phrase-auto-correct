# Research Notes

## Chosen Stack

Chosen stack: Python 3.14, Tkinter, pystray, Pillow, and direct Windows APIs through `ctypes`.

Why this stack was chosen:

- Python 3.14.3 and Tk 8.6 are available in this workspace.
- .NET, Rust, and Cargo are not available, so WPF, WinUI, and Tauri would add setup risk.
- Electron would add a heavy runtime for a small background utility.
- Windows global hotkeys and simulated Ctrl+C/Ctrl+V can be handled directly with User32 APIs.
- Tkinter is bundled with Python and is adequate for a small tone/options popup.
- pystray is focused on system tray icons and supports Windows tray menus.
- Pillow can load `icon.jpg` for the tray icon.

## Sources Checked

- Microsoft RegisterHotKey documentation: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-registerhotkey
- Microsoft SendInput documentation: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
- Microsoft clipboard documentation:
  - OpenClipboard: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openclipboard
  - GetClipboardData: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getclipboarddata
  - SetClipboardData: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setclipboarddata
  - EnumClipboardFormats: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumclipboardformats
  - GlobalAlloc / GlobalLock: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-globalalloc and https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-globallock
- Microsoft Run and RunOnce startup registration documentation: https://learn.microsoft.com/en-us/windows/win32/setupapi/run-and-runonce-registry-keys
- Python Tkinter documentation: https://docs.python.org/3/library/tkinter.html
- pystray documentation: https://pystray.readthedocs.io/en/latest/usage.html
- Pillow Image documentation: https://pillow.readthedocs.io/en/stable/reference/Image.html
- Ollama Windows and Generate API documentation:
  - https://docs.ollama.com/windows
  - https://docs.ollama.com/api/generate
- llama.cpp server documentation: https://www.mintlify.com/ggml-org/llama.cpp/inference/server
- Hugging Face Transformers pipeline documentation: https://huggingface.co/docs/transformers/main/en/main_classes/pipelines
- Hugging Face `vennify/t5-base-grammar-correction`: https://huggingface.co/vennify/t5-base-grammar-correction
- Hugging Face `qingy2024/GRMR-V3-Q4B`: https://huggingface.co/qingy2024/GRMR-V3-Q4B
- Hugging Face `Qwen/Qwen3-4B-Instruct-2507`: https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- Ollama `qwen3` model library: https://ollama.com/library/qwen3
- Ollama `qwen3.5` model library: https://ollama.com/library/qwen3.5
- Ollama `qwen3.6` model library: https://ollama.com/library/qwen3.6
- Hugging Face `Qwen/Qwen3-14B`: https://huggingface.co/Qwen/Qwen3-14B
- LanguageTool public HTTP API documentation: https://dev.languagetool.org/public-http-api.html
- Context7 was used for Python/Tkinter, pystray, and Transformers documentation lookup.

## AI Backend Options

### Ollama

Ollama is the best practical local AI integration target for this app. On Windows, Ollama runs in the background and serves a local API at `http://localhost:11434`. The Generate API supports `stream: false`, structured output through `format`, and a `think` flag for supported models. Models can be large, so the app should not download or bundle models automatically.

Decision: keep the Ollama provider interface and set the default provider to `auto`, using `qwen3.5:9b` when it is already installed and running locally. If Ollama is unavailable, the app falls back to the local deterministic provider. This preserves privacy while giving users a better local AI path.

The Ollama request sets `think: false` because phrase rewriting needs direct concise output, not visible reasoning. This also reduces latency for Qwen3-style models.

The prompt still asks the model to internally analyze the user's intent before rewriting. The app does not display or store that analysis; it only accepts the final three rewrite options.

### Recommended Model

Recommended practical default: `qwen3.5:9b` through Ollama.

Reasoning:

- Ollama lists `qwen3.5:9b` as the latest tag in the local Qwen3.5 family, with a 6.6 GB download and 256K context window. That is a practical size for many Windows machines while being stronger than the previous `qwen3:8b` default for context-aware rewriting.
- `qwen3.5:27b` is the higher-quality local recommendation if the user's machine can handle a 17 GB model.
- `qwen3.6` is newer, but the Ollama page positions it around agentic coding and thinking preservation. For this grammar/rewrite app, Qwen3.5's general utility and language coverage are the better default fit.
- `qwen3:8b` or `qwen3.5:4b` remain documented as faster fallbacks for lower-memory machines.
- Hugging Face lists Qwen3 models with Apache-2.0 licenses and Transformers support.

Best grammar-specific research candidate: `qingy2024/GRMR-V3-Q4B`.

Reasoning:

- It is Apache-2.0 and fine-tuned from Qwen3 4B specifically for grammar correction.
- The model card says it fixes grammar, punctuation, spelling, sentence structure, and clarity.
- It is not set as the default because it requires a separate Transformers/Unsloth/local inference setup or a compatible quantized runner, while this app already supports Ollama cleanly.

### llama.cpp

llama.cpp can run local GGUF models and expose an OpenAI-compatible local HTTP server. It is powerful but requires a separate binary and model files, which is too heavy to bundle into this folder without explicit approval.

Decision: document as a future provider option, not implemented in the first build.

### Transformers

Hugging Face Transformers can run text generation or text-to-text pipelines locally, but it usually requires PyTorch plus model downloads. That is too heavy for the initial installer and not appropriate without explicit approval.

Decision: not used by default.

## Popup and Focus Approach

The app now uses a non-activating, context-menu-style Tkinter palette:

- The selected text is captured before any UI appears.
- Windows UI Automation is attempted first to read the current focused control's selection without touching the clipboard. The UI Automation bindings are warmed up after startup so the first hotkey press does less setup work.
- If UI Automation cannot read the selection, the app falls back to Ctrl+C clipboard capture.
- The palette uses `overrideredirect(True)`, topmost positioning, and Win32 `WS_EX_NOACTIVATE`.
- The UI no longer calls `focus_force()` for tone or rewrite selection.
- Tone choices are shown first; after a left-click tone selection, a generation panel opens beside the tone menu.
- Rewrite options use check icons for replacement and a recycle icon for regeneration.

This is intended to keep the original app active so the highlighted selection is less likely to disappear before replacement.

### LanguageTool

LanguageTool can do grammar/style checking, but its public API is external and explicitly discourages automated use for application workloads unless users run their own instance or use a paid/enterprise plan. It also does not generate three tone-specific rewrite options by itself.

Decision: not used by default.

### Fallback Rewriter

The app includes a local deterministic fallback. It applies conservative grammar/punctuation cleanup and creates three tone-aware options. This is not as capable as an LLM, but it keeps the app working offline without sending selected text to a service.

## Hotkey Approach

Use `RegisterHotKey(NULL, id, MOD_CONTROL | MOD_NOREPEAT, VK_SPACE)` in a background thread with its own message loop. Microsoft documents that a NULL window handle posts `WM_HOTKEY` to the calling thread's message queue and that failure can indicate a conflict with another registered hotkey. The app reports that failure and supports changing `hotkey` in `config.json`.

## Tray Icon Approach

Use pystray with a Pillow image loaded from `icon.jpg` if present. The pystray docs state that `Icon.run()` is blocking, but on Windows it is safe to run it outside the main thread. Tkinter remains on the main thread.

## Clipboard Approach

The app backs up clipboard formats that can be copied from global-memory clipboard handles, clears the clipboard, sends Ctrl+C, reads `CF_UNICODETEXT`, then restores the backup. Replacement sets `CF_UNICODETEXT` to the chosen rewrite, sends Ctrl+V to the original foreground window, waits briefly, then restores the prior clipboard snapshot.

Limitations:

- Some clipboard formats are not global-memory formats and cannot be restored by this lightweight implementation.
- Elevated applications can block input injection from a non-elevated app.
- Some target apps may clear selection when focus leaves the app.

## Startup Approach

Use a per-user Startup folder shortcut created by `install.ps1`. This is easier to inspect and safer to remove than broad registry modification. `uninstall.ps1` removes only this app's shortcut, and also removes only this app's legacy Run registry value if one is found pointing to this project folder.

## Install-Time Model Download

The installer now offers an optional `qwen3.5:9b` model pull during setup. This uses the official Ollama CLI flow documented as `ollama pull <model>` and checks installed models with `ollama list`.

Implementation decisions:

- The model prompt is explicit because `qwen3.5:9b` is about 6.6 GB.
- `install.ps1 -PullModel` supports unattended model setup.
- `install.ps1 -SkipModelPrompt` supports quick installs and tests.
- If Ollama is missing, the installer can offer WinGet-based Ollama installation only when the user chooses it or passes `-InstallOllamaWithWinget`.
- The pull process is started with high process priority when Windows allows it, but the installer does not modify network adapter settings, QoS policy, firewall policy, or unrelated system bandwidth controls. It is not safe or reliable for a local app installer to reserve all system bandwidth.
- Ollama models are stored by Ollama in its own local model cache. The app source, scripts, logs, and config remain in this project folder.

## Security and Privacy Notes

- The app captures selected text only after the hotkey is pressed.
- Selected text is not logged by default.
- The default `fallback` provider keeps all rewriting local inside the Python process.
- The Ollama provider sends text only to `127.0.0.1`/localhost when the user changes `aiProvider` to `ollama`.
- No telemetry, browser data access, credential access, or rewrite history storage is implemented.
- Clipboard data is treated as untrusted input.
