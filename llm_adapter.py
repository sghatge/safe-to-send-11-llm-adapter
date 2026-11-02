"""A server-side model adapter for CRM tools that keeps working when the model doesn't.

- The API key is read from the environment, never from code, UI or reports
- Personal data is redacted before anything leaves the process
- Every call has a timeout and one retry with backoff
- If the model fails, the caller gets the rules-only answer, clearly labelled

Standard library only. Runs offline by default; set LLM_PROVIDER=anthropic plus
ANTHROPIC_API_KEY and LLM_MODEL to call a real model.
"""
import json
import os
import re
import time
import urllib.request

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE = re.compile(r"\+?\d[\d \-]{7,}\d")


def redact(text):
    text = EMAIL.sub("[email]", text)
    return PHONE.sub("[phone]", text)


class OfflineProvider:
    """Deterministic stand-in so the tool runs with no key and no network."""
    name = "offline"

    def complete(self, prompt, timeout):
        return "Summary (offline template): " + prompt.split("FINDINGS:", 1)[-1].strip()[:300]


class AnthropicProvider:
    name = "anthropic"

    def __init__(self):
        self.key = os.environ["ANTHROPIC_API_KEY"]
        self.model = os.environ["LLM_MODEL"]

    def complete(self, prompt, timeout):
        body = json.dumps({"model": self.model, "max_tokens": 400,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
            "x-api-key": self.key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["content"][0]["text"]


def provider_from_env():
    if os.environ.get("LLM_PROVIDER") == "anthropic":
        return AnthropicProvider()
    return OfflineProvider()


def explain(findings, rules_text, provider=None, timeout=10, retries=1, backoff=0.5):
    """Ask the model to explain rule findings. Returns (text, source)."""
    provider = provider or provider_from_env()
    prompt = ("You explain email QA results to a busy market manager. Do not change any verdict. "
              "Be brief and say how to fix each issue.\nFINDINGS:\n" + redact(json.dumps(findings, ensure_ascii=False)))
    for attempt in range(retries + 1):
        try:
            return provider.complete(prompt, timeout), provider.name
        except Exception as exc:  # timeouts, HTTP errors, malformed responses
            last = type(exc).__name__
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    return f"[rules-only: model unavailable ({last})] {rules_text}", "rules"


if __name__ == "__main__":
    findings = {"delivery": "BF-GR-01", "verdict": "fail",
                "issues": ["price shown as €1,299.00", "send at 23:30 local"],
                "reported_by": "nikos.p@example.com"}
    rules_text = "BF-GR-01 failed: price format; send time outside 08:00-21:00."

    text, source = explain(findings, rules_text)
    print(f"[{source}] {text}\n")

    class Flaky:
        name = "flaky"
        def complete(self, prompt, timeout):
            raise TimeoutError()

    text, source = explain(findings, rules_text, provider=Flaky(), backoff=0.01)
    print(f"[{source}] {text}")
