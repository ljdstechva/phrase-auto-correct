# Phrase Auto-correct

Phrase Auto-correct is a Windows tray app for improving selected English text in any editable app.

Highlight text, press `Ctrl+Space`, choose a tone from a small context-menu-style palette, then use the check icon beside a rewrite to replace the selected text. The palette is designed not to activate itself, so the original app can keep its selection while you choose.

## Install

From the parent folder:

```powershell
.\install.ps1
```

Or double-click:

```bat
install.bat
```

The parent folder intentionally contains only the user-facing install files and this `source\` folder. The installer creates `.venv` inside `source\`, installs dependencies locally, creates a per-user Startup shortcut for this app, and starts the tray app.

During install, the script asks whether to download the recommended local AI model:

```text
qwen3.5:9b, about 6.6 GB
```

For unattended installs:

```powershell
.\install.ps1 -PullModel
```

To skip the model prompt:

```powershell
.\install.ps1 -SkipModelPrompt
```

If Ollama is missing and you want the installer to offer WinGet-based Ollama installation during model setup:

```powershell
.\install.ps1 -PullModel -InstallOllamaWithWinget
```

Model downloads use the official `ollama pull` command. The installer does not throttle the download and raises the pull process priority when Windows allows it, but it does not make unsafe network changes or reserve all system bandwidth. Actual speed depends on your internet connection, Ollama, disk speed, and the model host.

## Run

```powershell
.\source\run.ps1
```

For console diagnostics:

```powershell
.\source\run.ps1 -Console
```

## Use

1. Highlight a phrase, sentence, or paragraph in an editable app.
2. Press `Ctrl+Space`.
3. Left-click a tone:
   Formal, Informal, Optimistic, Worried, Friendly, Curious, Assertive, Encouraging, Surprised, or Cooperative.
4. A generation panel opens beside the tone menu and starts generating.
5. Click the check icon beside one rewrite to replace the selected text.
6. Click the recycle icon to regenerate the three options.

If no text is selected, the palette shows `No text selected.`

## Tray Menu

Right-click the tray icon:

- `Exit`: closes the app.
- `Uninstall`: removes the app startup shortcut and stops the running app.

The tray icon uses `icon.jpg` from this folder when available.

## AI Rewriting

Default mode is automatic local AI:

```json
"aiProvider": "auto",
"ollamaModel": "qwen3.5:9b"
```

This tries a local Ollama model first and falls back to offline deterministic cleanup if Ollama is not installed or not running. It does not send selected text to the internet.

Recommended local models:

- Best practical default: `qwen3.5:9b` through Ollama. It is newer than the previous `qwen3:8b` default, still a realistic local download for many Windows machines, and is better suited to context-aware rewriting.
- Higher quality if your machine can handle it: `qwen3.5:27b`.
- Faster fallback: `qwen3:8b` or `qwen3.5:4b`.
- Grammar-only research candidate: `qingy2024/GRMR-V3-Q4B` on Hugging Face. It is Apache-2.0 and grammar-focused, but it is not bundled because it needs a separate local Transformers/Unsloth or compatible quantized inference setup.

To enable the recommended local model:

1. Install Ollama for Windows from https://docs.ollama.com/windows, or let `install.ps1 -PullModel -InstallOllamaWithWinget` offer WinGet installation.
2. Pull a model, or choose the installer model prompt:

```powershell
ollama pull qwen3.5:9b
```

3. Edit `config.json`:

```json
"aiProvider": "ollama",
"ollamaModel": "qwen3.5:9b",
"ollamaUrl": "http://127.0.0.1:11434/api/generate"
```

4. Restart Phrase Auto-correct.

You can also set:

```json
"aiProvider": "auto"
```

This tries local Ollama first and falls back to the offline provider if Ollama is unavailable.

The Ollama prompt now asks the model to internally analyze the user's intent, message type, protected terms, and grammar issues before generating rewrites. That analysis is not displayed; the app still receives only three rewrite options.

## Configuration

Edit `config.json` in this folder:

```json
{
  "hotkey": "Ctrl+Space",
  "aiProvider": "auto",
  "ollamaModel": "qwen3.5:9b",
  "ollamaUrl": "http://127.0.0.1:11434/api/generate",
  "maxTextLength": 4000,
  "startOnBoot": true,
  "debugLogging": false,
  "copyTimeoutMs": 550,
  "pasteRestoreDelayMs": 350,
  "ollamaTimeoutSeconds": 45
}
```

If `Ctrl+Space` conflicts with another app, change `hotkey`, for example:

```json
"hotkey": "Ctrl+Shift+Space"
```

Supported modifier names: `Ctrl`, `Alt`, `Shift`, `Win`.

## Uninstall

```powershell
.\source\uninstall.ps1
```

Or, from the `source\` folder:

```bat
uninstall.bat
```

Uninstall stops the running app and removes only this app's startup shortcut. Source files and `.venv` are left in place.

## Privacy

- Text is captured only when you press the hotkey.
- Selected text is not logged by default.
- Rewrite history is not stored.
- No telemetry is collected.
- The default automatic provider uses only local Ollama or local fallback.
- Ollama mode sends text only to the configured local Ollama URL.
- Ollama stores downloaded models in its own local model cache, not inside this app folder.
- External grammar or cloud APIs are not used.

Logs are stored in `sources/logs` and do not include selected text.

## Known Limitations

- Clipboard restoration is best effort. Most text formats are restored, but some custom or non-memory clipboard formats may not be recoverable.
- Replacement can fail in apps that block paste, run elevated while this app is not elevated, or clear selection when focus changes.
- The fallback provider is useful and private, but `qwen3.5:9b` through Ollama gives better rewrite quality.
- Large local AI models are not bundled. The installer can optionally download `qwen3.5:9b` when the user chooses that option.

## Troubleshooting

- If the hotkey does not work, run `.\source\run.ps1 -Console` from the parent folder and check whether another app already owns it.
- If replacement fails in an elevated app, run Phrase Auto-correct with the same integrity level or use it in a non-elevated target app.
- If Ollama mode fails, confirm Ollama is running and that `ollamaModel` exists locally.
- If the tray icon is hidden, check Windows tray overflow settings.
