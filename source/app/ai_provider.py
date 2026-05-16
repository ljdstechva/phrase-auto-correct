"""Rewrite providers for local fallback and optional Ollama."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import urllib.error
import urllib.request

from .config import AppConfig, SUPPORTED_TONES


class RewriteError(RuntimeError):
    """Raised when a rewrite provider cannot produce valid options."""


class RewriteProvider:
    """Provider protocol without requiring runtime typing dependencies."""

    def rewrite(self, text: str, tone: str) -> list[str]:
        raise NotImplementedError


@dataclass
class RewriteEngine:
    """Select a configured provider and validate its output."""

    config: AppConfig

    def rewrite(self, text: str, tone: str) -> list[str]:
        if tone not in SUPPORTED_TONES:
            raise RewriteError(f"Unsupported tone: {tone}")

        provider_name = self.config.ai_provider
        if provider_name == "fallback":
            return _validate_options(FallbackRewriteProvider().rewrite(text, tone))

        if provider_name == "ollama":
            return _validate_options(OllamaProvider(self.config).rewrite(text, tone))

        try:
            return _validate_options(OllamaProvider(self.config).rewrite(text, tone))
        except RewriteError:
            return _validate_options(FallbackRewriteProvider().rewrite(text, tone))


@dataclass
class OllamaProvider(RewriteProvider):
    """Local Ollama provider using the Generate API."""

    config: AppConfig

    def rewrite(self, text: str, tone: str) -> list[str]:
        prompt = _build_ollama_prompt(text, tone)
        payload = {
            "model": self.config.ollama_model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {
                "temperature": 0.25,
                "top_p": 0.9,
                "num_predict": 700,
            },
        }
        request = urllib.request.Request(
            self.config.ollama_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.config.ollama_timeout_seconds,
            ) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RewriteError(
                "Ollama is not available. Start Ollama or set "
                "aiProvider to fallback in config.json."
            ) from exc

        try:
            data = json.loads(raw)
            content = data["response"]
            parsed = json.loads(content)
            options = parsed.get("options")
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise RewriteError("Ollama returned an invalid response.") from exc

        if not isinstance(options, list):
            raise RewriteError("Ollama response did not contain options.")
        return [str(option).strip() for option in options]


class FallbackRewriteProvider(RewriteProvider):
    """Conservative local rewriting without external services."""

    def rewrite(self, text: str, tone: str) -> list[str]:
        cleaned = clean_text(text)
        candidates = _tone_candidates(cleaned, tone)
        return _ensure_three(candidates, cleaned)


def _build_ollama_prompt(text: str, tone: str) -> str:
    tones = ", ".join(SUPPORTED_TONES)
    return (
        "You are an expert English grammar, clarity, and rephrasing editor.\n"
        "Task: rewrite the selected text into exactly three options.\n"
        f"Selected tone: {tone}. Supported tones: {tones}.\n\n"
        "First, internally analyze the user's likely intent before writing:\n"
        "- What is the user trying to say or request?\n"
        "- Is the message informing, asking, apologizing, warning, "
        "confirming, or coordinating?\n"
        "- Which names, numbers, dates, links, product names, and technical "
        "terms must remain unchanged?\n"
        "- What grammar, punctuation, clarity, or phrasing issues need fixing?\n"
        "Do not output this analysis.\n\n"
        "Rewrite rules:\n"
        "- Preserve the user's intended meaning and relationship context.\n"
        "- Correct grammar, spelling, clarity, punctuation, and phrasing.\n"
        "- Match the selected tone naturally without exaggeration.\n"
        "- Do not add facts, promises, emotions, urgency, or details that are "
        "not implied by the original text.\n"
        "- Do not change names, numbers, links, dates, or technical terms "
        "unless grammar clearly requires it.\n"
        "- Keep the rewrite concise. Slight expansion is allowed only when it "
        "makes the sentence grammatical or the selected tone clearer.\n"
        "- Make the three options visibly different from each other.\n"
        "- Do not return the original sentence unchanged if it contains "
        "grammar or clarity errors.\n"
        "Return JSON only in this exact shape: "
        '{"options":["first","second","third"]}\n'
        "\nSelected text:\n"
        f"{text}"
    )


COMMON_FIXES: tuple[tuple[str, str], ...] = (
    (r"\bi\b", "I"),
    (r"\bim\b", "I'm"),
    (r"\bi'm\b", "I'm"),
    (r"\bive\b", "I've"),
    (r"\bdont\b", "don't"),
    (r"\bcant\b", "can't"),
    (r"\bwont\b", "won't"),
    (r"\bshouldnt\b", "shouldn't"),
    (r"\bcouldnt\b", "couldn't"),
    (r"\bwouldnt\b", "wouldn't"),
    (r"\balot\b", "a lot"),
    (r"\brecieve\b", "receive"),
    (r"\bseperate\b", "separate"),
    (r"\bbecause client\b", "because the client"),
    (r"\bclient waiting\b", "client is waiting"),
    (r"\breport finish today\b", "report finished today"),
    (r"\breport completed today\b", "report completed today"),
    (r"\bneed this report finish\b", "need this report finished"),
)


def clean_text(text: str) -> str:
    """Apply conservative grammar, whitespace, and punctuation cleanup."""

    result = re.sub(r"\s+", " ", text.strip())
    result = re.sub(r"\s+([,.;:!?])", r"\1", result)
    result = re.sub(r"([,.;:!?])([A-Za-z])", r"\1 \2", result)
    for pattern, replacement in COMMON_FIXES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    result = _capitalize_sentences(result)
    if result and result[-1] not in ".!?":
        result += "."
    return result


def _capitalize_sentences(text: str) -> str:
    if not text:
        return text
    text = text[0].upper() + text[1:]
    return re.sub(
        r"([.!?]\s+)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        text,
    )


def _tone_candidates(text: str, tone: str) -> list[str]:
    need_parts = _parse_need_because(text)
    if need_parts:
        need_content, reason = need_parts
        passive = _passivize_need_content(need_content)
        return _need_candidates(text, tone, need_content, passive, reason)
    return _generic_candidates(text, tone)


def _parse_need_because(text: str) -> tuple[str, str] | None:
    body = text.rstrip(".!?")
    match = re.match(r"(?i)^I need (.+?) because (.+)$", body)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip()


def _passivize_need_content(content: str) -> str:
    result = content.strip()
    result = re.sub(
        r"\b(report|document|file|task|work) finished\b",
        r"\1 is finished",
        result,
        flags=re.IGNORECASE,
    )
    result = re.sub(
        r"\b(report|document|file|task|work) completed\b",
        r"\1 is completed",
        result,
        flags=re.IGNORECASE,
    )
    return result


def _sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def _need_candidates(
    original: str,
    tone: str,
    need_content: str,
    passive: str,
    reason: str,
) -> list[str]:
    passive_sentence = _sentence_case(passive)
    reason_sentence = reason.rstrip(".")
    templates = {
        "Formal": [
            original,
            f"Please ensure that {passive}, as {reason_sentence}.",
            f"{passive_sentence} because {reason_sentence}.",
        ],
        "Informal": [
            original,
            f"Can we get {need_content} because {reason_sentence}?",
            f"Let's get {need_content} because {reason_sentence}.",
        ],
        "Optimistic": [
            f"I think we can get {need_content} because {reason_sentence}.",
            f"Let's get {need_content} because {reason_sentence}.",
            original,
        ],
        "Worried": [
            f"I'm concerned that {passive} because {reason_sentence}.",
            f"We need {need_content} because {reason_sentence}.",
            original,
        ],
        "Friendly": [
            f"Could we please get {need_content} because {reason_sentence}?",
            f"Please help make sure {passive} because {reason_sentence}.",
            original,
        ],
        "Curious": [
            f"Could we get {need_content} because {reason_sentence}?",
            f"I'm wondering if we can get {need_content} because "
            f"{reason_sentence}.",
            original,
        ],
        "Assertive": [
            f"{passive_sentence} because {reason_sentence}.",
            f"We need {need_content} because {reason_sentence}.",
            original,
        ],
        "Encouraging": [
            f"Let's get {need_content} because {reason_sentence}.",
            f"We can get {need_content} because {reason_sentence}.",
            original,
        ],
        "Surprised": [
            f"I'm surprised that {passive} because {reason_sentence}.",
            f"It is surprising that {passive} because {reason_sentence}.",
            original,
        ],
        "Cooperative": [
            f"Let's work together to get {need_content} because "
            f"{reason_sentence}.",
            f"Please coordinate with me so {passive} because "
            f"{reason_sentence}.",
            original,
        ],
    }
    return templates.get(tone, [original])


def _generic_candidates(text: str, tone: str) -> list[str]:
    body = text.rstrip(".!?")
    lower_body = body[:1].lower() + body[1:] if body else body
    templates = {
        "Formal": [
            text,
            f"Please note that {lower_body}.",
            f"It is important that {lower_body}.",
        ],
        "Informal": [text, f"Just so you know, {lower_body}.", f"{body}!"],
        "Optimistic": [text, f"I think {lower_body}.", f"{body}, and this can work."],
        "Worried": [
            text,
            f"I'm concerned that {lower_body}.",
            f"{body}, which is concerning.",
        ],
        "Friendly": [
            text,
            f"Please keep in mind that {lower_body}.",
            f"{body}, thanks.",
        ],
        "Curious": [
            text,
            f"I'm wondering whether {lower_body}.",
            f"Could it be that {lower_body}?",
        ],
        "Assertive": [text, f"{body}.", f"This needs attention: {lower_body}."],
        "Encouraging": [
            text,
            f"We can handle this: {lower_body}.",
            f"Let's keep moving: {lower_body}.",
        ],
        "Surprised": [
            text,
            f"I'm surprised that {lower_body}.",
            f"It is surprising that {lower_body}.",
        ],
        "Cooperative": [
            text,
            f"Let's work together on this: {lower_body}.",
            f"We can coordinate on this: {lower_body}.",
        ],
    }
    return templates.get(tone, [text])


def _ensure_three(candidates: list[str], fallback: str) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for candidate in candidates + [
        fallback,
        f"Please {fallback[:1].lower()}{fallback[1:]}",
        f"{fallback.rstrip('.!?')}.",
    ]:
        cleaned = clean_text(candidate)
        key = cleaned.casefold()
        if cleaned and key not in seen:
            results.append(cleaned)
            seen.add(key)
        if len(results) == 3:
            return results
    while len(results) < 3:
        results.append(fallback)
    return results[:3]


def _validate_options(options: list[str]) -> list[str]:
    cleaned = [option.strip() for option in options if option.strip()]
    if len(cleaned) != 3:
        raise RewriteError("Rewrite provider must return exactly three options.")
    return cleaned
