"""Configuration loading for Phrase Auto-correct."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


SUPPORTED_TONES: tuple[str, ...] = (
    "Formal",
    "Informal",
    "Optimistic",
    "Worried",
    "Friendly",
    "Curious",
    "Assertive",
    "Encouraging",
    "Surprised",
    "Cooperative",
)

DEFAULT_SYSTEM_PROMPT_TEMPLATE = (
    "You are an expert English rephrasing editor. Rewrite the selected text "
    "in a {tone} tone. Preserve meaning, names, numbers, links, dates, and "
    "technical terms. Correct grammar, punctuation, clarity, and phrasing. "
    "Do not add facts. Return JSON only with exactly three concise, distinct "
    'options: {"options":["...","...","..."]}.'
)


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from config.json."""

    hotkey: str = "Ctrl+Space"
    ai_provider: str = "openai"
    openai_model: str = "gpt-5"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1/responses"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT_TEMPLATE
    max_text_length: int = 4000
    start_on_boot: bool = True
    debug_logging: bool = False
    copy_timeout_ms: int = 550
    paste_restore_delay_ms: int = 350
    openai_timeout_seconds: int = 45


CONFIG_FIELD_MAP: dict[str, str] = {
    "hotkey": "hotkey",
    "aiProvider": "ai_provider",
    "openaiModel": "openai_model",
    "openaiApiKey": "openai_api_key",
    "openaiBaseUrl": "openai_base_url",
    "systemPrompt": "system_prompt",
    "maxTextLength": "max_text_length",
    "startOnBoot": "start_on_boot",
    "debugLogging": "debug_logging",
    "copyTimeoutMs": "copy_timeout_ms",
    "pasteRestoreDelayMs": "paste_restore_delay_ms",
    "openaiTimeoutSeconds": "openai_timeout_seconds",
}


def default_config_dict() -> dict[str, Any]:
    """Return defaults using the public config.json key names."""

    defaults = AppConfig()
    return {
        "hotkey": defaults.hotkey,
        "aiProvider": defaults.ai_provider,
        "openaiModel": defaults.openai_model,
        "openaiBaseUrl": defaults.openai_base_url,
        "systemPrompt": defaults.system_prompt,
        "maxTextLength": defaults.max_text_length,
        "startOnBoot": defaults.start_on_boot,
        "debugLogging": defaults.debug_logging,
        "copyTimeoutMs": defaults.copy_timeout_ms,
        "pasteRestoreDelayMs": defaults.paste_restore_delay_ms,
        "openaiTimeoutSeconds": defaults.openai_timeout_seconds,
    }


def ensure_config_file(project_root: Path) -> Path:
    """Create config.json with defaults if it does not exist."""

    config_path = project_root / "config.json"
    if not config_path.exists():
        config_path.write_text(
            json.dumps(default_config_dict(), indent=2) + "\n",
            encoding="utf-8",
        )
    return config_path


def load_config(project_root: Path) -> AppConfig:
    """Load config.json and coerce known fields to safe values."""

    config_path = ensure_config_file(project_root)
    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config.json must contain a JSON object")

    local_path = project_root / "config.local.json"
    if local_path.exists():
        local_data = json.loads(local_path.read_text(encoding="utf-8"))
        if not isinstance(local_data, dict):
            raise ValueError("config.local.json must contain a JSON object")
        data.update(local_data)

    kwargs: dict[str, Any] = {}
    for public_name, field_name in CONFIG_FIELD_MAP.items():
        if public_name in data:
            kwargs[field_name] = data[public_name]

    config = AppConfig(**kwargs)
    return _sanitize_config(config)


def save_local_ai_settings(
    project_root: Path,
    *,
    ai_provider: str,
    openai_model: str,
    openai_api_key: str,
    openai_base_url: str,
    system_prompt: str,
) -> AppConfig:
    """Persist user AI settings in an untracked local config file."""

    local_path = project_root / "config.local.json"
    data: dict[str, Any] = {}
    if local_path.exists():
        loaded = json.loads(local_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            data.update(loaded)

    data.update(
        {
            "aiProvider": ai_provider,
            "openaiModel": openai_model,
            "openaiApiKey": openai_api_key,
            "openaiBaseUrl": openai_base_url,
            "systemPrompt": system_prompt,
        }
    )
    local_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return load_config(project_root)


def _sanitize_config(config: AppConfig) -> AppConfig:
    provider = str(config.ai_provider).strip().lower()
    if provider in {"ollama", "auto"}:
        provider = "openai"
    if provider not in {"openai", "fallback"}:
        provider = "openai"

    max_text_length = _bounded_int(config.max_text_length, 100, 20000, 4000)
    copy_timeout_ms = _bounded_int(config.copy_timeout_ms, 200, 5000, 550)
    paste_delay_ms = _bounded_int(
        config.paste_restore_delay_ms,
        100,
        3000,
        350,
    )
    openai_timeout = _bounded_int(
        config.openai_timeout_seconds,
        5,
        180,
        45,
    )
    system_prompt = str(config.system_prompt or DEFAULT_SYSTEM_PROMPT_TEMPLATE).strip()

    return AppConfig(
        hotkey=str(config.hotkey or "Ctrl+Space").strip() or "Ctrl+Space",
        ai_provider=provider,
        openai_model=str(config.openai_model or "gpt-5").strip(),
        openai_api_key=str(config.openai_api_key or "").strip(),
        openai_base_url=str(
            config.openai_base_url or "https://api.openai.com/v1/responses"
        ).strip(),
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT_TEMPLATE,
        max_text_length=max_text_length,
        start_on_boot=bool(config.start_on_boot),
        debug_logging=bool(config.debug_logging),
        copy_timeout_ms=copy_timeout_ms,
        paste_restore_delay_ms=paste_delay_ms,
        openai_timeout_seconds=openai_timeout,
    )


def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, integer))
