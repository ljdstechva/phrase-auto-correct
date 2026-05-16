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


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration loaded from config.json."""

    hotkey: str = "Ctrl+Space"
    ai_provider: str = "auto"
    ollama_model: str = "qwen3.5:9b"
    ollama_url: str = "http://127.0.0.1:11434/api/generate"
    max_text_length: int = 4000
    start_on_boot: bool = True
    debug_logging: bool = False
    copy_timeout_ms: int = 550
    paste_restore_delay_ms: int = 350
    ollama_timeout_seconds: int = 45


CONFIG_FIELD_MAP: dict[str, str] = {
    "hotkey": "hotkey",
    "aiProvider": "ai_provider",
    "ollamaModel": "ollama_model",
    "ollamaUrl": "ollama_url",
    "maxTextLength": "max_text_length",
    "startOnBoot": "start_on_boot",
    "debugLogging": "debug_logging",
    "copyTimeoutMs": "copy_timeout_ms",
    "pasteRestoreDelayMs": "paste_restore_delay_ms",
    "ollamaTimeoutSeconds": "ollama_timeout_seconds",
}


def default_config_dict() -> dict[str, Any]:
    """Return defaults using the public config.json key names."""

    defaults = AppConfig()
    return {
        "hotkey": defaults.hotkey,
        "aiProvider": defaults.ai_provider,
        "ollamaModel": defaults.ollama_model,
        "ollamaUrl": defaults.ollama_url,
        "maxTextLength": defaults.max_text_length,
        "startOnBoot": defaults.start_on_boot,
        "debugLogging": defaults.debug_logging,
        "copyTimeoutMs": defaults.copy_timeout_ms,
        "pasteRestoreDelayMs": defaults.paste_restore_delay_ms,
        "ollamaTimeoutSeconds": defaults.ollama_timeout_seconds,
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

    kwargs: dict[str, Any] = {}
    for public_name, field_name in CONFIG_FIELD_MAP.items():
        if public_name in data:
            kwargs[field_name] = data[public_name]

    config = AppConfig(**kwargs)
    return _sanitize_config(config)


def _sanitize_config(config: AppConfig) -> AppConfig:
    provider = str(config.ai_provider).strip().lower()
    if provider not in {"fallback", "ollama", "auto"}:
        provider = "fallback"

    max_text_length = _bounded_int(config.max_text_length, 100, 20000, 4000)
    copy_timeout_ms = _bounded_int(config.copy_timeout_ms, 200, 5000, 550)
    paste_delay_ms = _bounded_int(
        config.paste_restore_delay_ms,
        100,
        3000,
        350,
    )
    ollama_timeout = _bounded_int(
        config.ollama_timeout_seconds,
        5,
        180,
        45,
    )

    return AppConfig(
        hotkey=str(config.hotkey or "Ctrl+Space").strip() or "Ctrl+Space",
        ai_provider=provider,
        ollama_model=str(config.ollama_model or "qwen3.5:9b").strip(),
        ollama_url=str(
            config.ollama_url or "http://127.0.0.1:11434/api/generate"
        ).strip(),
        max_text_length=max_text_length,
        start_on_boot=bool(config.start_on_boot),
        debug_logging=bool(config.debug_logging),
        copy_timeout_ms=copy_timeout_ms,
        paste_restore_delay_ms=paste_delay_ms,
        ollama_timeout_seconds=ollama_timeout,
    )


def _bounded_int(value: Any, minimum: int, maximum: int, default: int) -> int:
    try:
        integer = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, integer))
