from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import AppConfig, ensure_config_file, save_local_ai_settings
from app.hotkey import MOD_CONTROL, MOD_SHIFT, HotkeyError, parse_hotkey


class HotkeyConfigTests(unittest.TestCase):
    def test_parse_default_hotkey(self) -> None:
        modifiers, key = parse_hotkey("Ctrl+Space")
        self.assertEqual(modifiers, MOD_CONTROL)
        self.assertEqual(key, 0x20)

    def test_parse_compound_hotkey(self) -> None:
        modifiers, key = parse_hotkey("Ctrl+Shift+F9")
        self.assertEqual(modifiers, MOD_CONTROL | MOD_SHIFT)
        self.assertEqual(key, 0x78)

    def test_invalid_hotkey_raises(self) -> None:
        with self.assertRaises(HotkeyError):
            parse_hotkey("Space")

    def test_config_defaults(self) -> None:
        config = AppConfig()
        self.assertEqual(config.ai_provider, "openai")
        self.assertEqual(config.openai_model, "gpt-5")
        self.assertEqual(config.hotkey, "Ctrl+Space")

    def test_save_local_ai_settings(self) -> None:
        with TemporaryDirectory() as temp:
            project_root = Path(temp)
            ensure_config_file(project_root)
            config = save_local_ai_settings(
                project_root,
                ai_provider="openai",
                openai_model="gpt-5-mini",
                openai_api_key="sk-test",
                openai_base_url="https://api.openai.com/v1/responses",
                system_prompt="Rewrite in a {tone} tone. Return JSON only.",
            )

            self.assertEqual(config.openai_model, "gpt-5-mini")
            self.assertEqual(config.openai_api_key, "sk-test")
            self.assertTrue((project_root / "config.local.json").exists())


if __name__ == "__main__":
    unittest.main()
