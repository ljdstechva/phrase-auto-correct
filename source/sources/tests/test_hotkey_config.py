from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.config import AppConfig
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
        self.assertEqual(config.ai_provider, "auto")
        self.assertEqual(config.ollama_model, "qwen3.5:9b")
        self.assertEqual(config.hotkey, "Ctrl+Space")


if __name__ == "__main__":
    unittest.main()
