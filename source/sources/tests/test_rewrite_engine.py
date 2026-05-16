from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.ai_provider import (
    FallbackRewriteProvider,
    OpenAIResponsesProvider,
    clean_text,
)
from app.config import AppConfig


class FakeResponse:
    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(
            {
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {"options": ["One.", "Two.", "Three."]}
                                ),
                            }
                        ]
                    }
                ]
            }
        ).encode("utf-8")


class RewriteEngineTests(unittest.TestCase):
    def test_clean_text_fixes_sample_sentence(self) -> None:
        text = "i need this report finish today because client waiting"
        self.assertEqual(
            clean_text(text),
            "I need this report finished today because the client is waiting.",
        )

    def test_fallback_returns_three_formal_options(self) -> None:
        provider = FallbackRewriteProvider()
        options = provider.rewrite(
            "i need this report finish today because client waiting",
            "Formal",
        )
        self.assertEqual(len(options), 3)
        self.assertEqual(len(set(options)), 3)
        self.assertTrue(all(option.endswith(".") for option in options))

    def test_fallback_preserves_numbers(self) -> None:
        provider = FallbackRewriteProvider()
        options = provider.rewrite("i need 3 files by May 20", "Assertive")
        self.assertEqual(len(options), 3)
        self.assertTrue(all("3" in option for option in options))
        self.assertTrue(all("May 20" in option for option in options))

    def test_openai_payload_uses_json_schema_and_tone_prompt(self) -> None:
        captured: dict[str, object] = {}

        def fake_urlopen(request: object, timeout: int) -> FakeResponse:
            captured["timeout"] = timeout
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["authorization"] = request.get_header("Authorization")
            return FakeResponse()

        config = AppConfig(
            ai_provider="openai",
            openai_model="gpt-test",
            openai_api_key="test-key",
            openai_timeout_seconds=7,
            system_prompt="Rewrite in a {tone} tone. Return JSON only.",
        )
        with patch("app.ai_provider.urllib.request.urlopen", fake_urlopen):
            options = OpenAIResponsesProvider(config).rewrite(
                "hello there",
                "Friendly",
            )

        self.assertEqual(options, ["One.", "Two.", "Three."])
        self.assertEqual(captured["timeout"], 7)
        self.assertEqual(captured["authorization"], "Bearer test-key")
        payload = captured["payload"]
        self.assertEqual(payload["model"], "gpt-test")
        self.assertEqual(
            payload["text"]["format"]["schema"]["properties"]["options"][
                "maxItems"
            ],
            3,
        )
        self.assertIn("Friendly", payload["input"][0]["content"])


if __name__ == "__main__":
    unittest.main()
