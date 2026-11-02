Safe to Send · Ep 11 — The API key never touches the UI

I connected an AI model to my CRM workbench. The interesting part isn't the prompt. It's everything around it.

→ The key lives in an environment variable on the server. Not in the app, not in Git, not in a downloadable report.
→ Emails and phone numbers are redacted before the prompt leaves the process.
→ Every call has a timeout and one retry.
→ If the model is down, the user gets the rules-only answer, clearly labelled.

I tested the last one by making the provider time out twice. The Greek market still got: "BF-GR-01 failed: price format; send time outside 08:00–21:00." Less elegant, but correct and on time.

One more design choice: every answer is tagged with where it came from, a model or the rules. People deserve to know which one they're reading.

If your AI feature dies when the model does, it's a demo, not a tool.

Repo: https://github.com/sghatge/safe-to-send-11-llm-adapter

#SafeToSend #AIEngineering #Security
