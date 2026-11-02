import unittest

from llm_adapter import explain, redact


class Recorder:
    name = "recorder"

    def __init__(self, fail_times=0):
        self.fail_times, self.calls, self.prompts = fail_times, 0, []

    def complete(self, prompt, timeout):
        self.calls += 1
        self.prompts.append(prompt)
        if self.calls <= self.fail_times:
            raise TimeoutError()
        return "ok"


class AdapterTest(unittest.TestCase):
    def test_pii_never_reaches_provider(self):
        p = Recorder()
        explain({"by": "ana.k@example.com", "tel": "+385 91 234 5678"}, "r", provider=p)
        self.assertNotIn("ana.k@example.com", p.prompts[0])
        self.assertNotIn("234 5678", p.prompts[0])

    def test_retry_then_success(self):
        p = Recorder(fail_times=1)
        self.assertEqual(explain({}, "r", provider=p, backoff=0)[1], "recorder")
        self.assertEqual(p.calls, 2)

    def test_fallback_to_rules(self):
        text, source = explain({}, "rules say fail", provider=Recorder(fail_times=9), backoff=0)
        self.assertEqual(source, "rules")
        self.assertIn("rules say fail", text)
        self.assertIn("TimeoutError", text)

    def test_redact(self):
        self.assertEqual(redact("mail a@example.com now"), "mail [email] now")


if __name__ == "__main__":
    unittest.main()
