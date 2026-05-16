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

The parent folder intentionally contains only the user-facing install files and this `source\` folder. The installer creates `.venv` inside `source\`, installs dependencies locally, creates a per-user Startup shortcut for this app, and starts the tray app. It does not download local AI models.

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

- `Settings`: choose the AI provider, model, API key, base URL, and system prompt.
- `Exit`: closes the app.
- `Uninstall`: removes the app startup shortcut and stops the running app.

The tray icon uses `icon.jpg` from this folder when available.

## AI Rewriting

AI rewriting is now configured from the tray `Settings` menu. The default provider is OpenAI-compatible:

```json
"aiProvider": "openai",
"openaiModel": "gpt-5",
"openaiBaseUrl": "https://api.openai.com/v1/responses"
```

Enter your API key in `Settings`. The key is saved to `config.local.json`, which is ignored by git.

The system prompt is brief and tone-aware:

```text
You are an expert English rephrasing editor. Rewrite the selected text in a {tone} tone. Preserve meaning, names, numbers, links, dates, and technical terms. Correct grammar, punctuation, clarity, and phrasing. Do not add facts. Return JSON only with exactly three concise, distinct options: {"options":["...","...","..."]}.
```

The app sends the selected tone and selected text only after you choose a tone. It asks the model to return strict JSON with exactly three options.

## Configuration

General app defaults are in `config.json`:

```json
{
  "hotkey": "Ctrl+Space",
  "aiProvider": "openai",
  "openaiModel": "gpt-5",
  "openaiBaseUrl": "https://api.openai.com/v1/responses",
  "systemPrompt": "You are an expert English rephrasing editor...",
  "maxTextLength": 4000,
  "startOnBoot": true,
  "debugLogging": false,
  "copyTimeoutMs": 550,
  "pasteRestoreDelayMs": 350,
  "openaiTimeoutSeconds": 45
}
```

User settings from the tray are saved in `config.local.json`. This file can contain the API key and is not committed to git.

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
- OpenAI mode sends selected text to the configured OpenAI-compatible API only after you choose a tone.
- The API key is stored locally in ignored `config.local.json`.
- The deterministic `fallback` provider stays available for local cleanup, but it is not the default AI path.

Logs are stored in `sources/logs` and do not include selected text.

## Known Limitations

- Clipboard restoration is best effort. Most text formats are restored, but some custom or non-memory clipboard formats may not be recoverable.
- Replacement can fail in apps that block paste, run elevated while this app is not elevated, or clear selection when focus changes.
- OpenAI mode requires a valid API key, reachable base URL, and model access.
- The fallback provider is private and local, but it is intentionally conservative and lower quality than a configured AI model.

## Troubleshooting

- If the hotkey does not work, run `.\source\run.ps1 -Console` from the parent folder and check whether another app already owns it.
- If replacement fails in an elevated app, run Phrase Auto-correct with the same integrity level or use it in a non-elevated target app.
- If AI rewriting fails, open tray `Settings` and confirm the model, API key, and base URL.
- If the tray icon is hidden, check Windows tray overflow settings.
