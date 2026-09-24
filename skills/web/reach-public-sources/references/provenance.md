# Provenance and boundaries

- Upstream: https://github.com/Panniantong/Agent-Reach
- Research pin: `a19a171fa980a0785849596492e0af4db800c82f` (package declares 1.5.0).
- License: MIT, copyright (c) 2025 Agent Eyes; see UPSTREAM-LICENSE.md.
- Actual upstream skill paths: `agent_reach/skill/SKILL.md` and `agent_reach/skill/SKILL_en.md`, with accompanying `references/`.
- Pinned English document: https://raw.githubusercontent.com/Panniantong/Agent-Reach/a19a171fa980a0785849596492e0af4db800c82f/agent_reach/skill/SKILL_en.md
- Directory identifier, if inspecting upstream rather than this adaptation: `Panniantong/Agent-Reach/agent_reach/skill`. A repository-root shortcut is not a skill installation. A text error can coexist with CLI exit zero; inspect results and loaded files.

## What is adapted

The first-party procedure keeps the useful pattern: choose public sources by platform, run actual tools, preserve evidence, diagnose prerequisites separately, and report coverage. It replaces blanket activation/update mandates, global installs, automatic session/cookie helpers and broad availability claims with narrowly scoped read-only behavior. No upstream Agent Reach CLI or installer is installed. Actual pinned backends used here are yt-dlp 2026.8.19 and feedparser 6.0.14, plus the existing gh executable.

The Python runtime has its own .venv and a hash-pinned requirements.lock. To rebuild after explicit approval, use `terminal` with `uv pip sync --python "$RUNTIME/.venv/bin/python" --require-hashes "$RUNTIME/requirements.lock"`. Never target Hermes' interpreter. The lock, not the current latest package index, defines this tested environment.

## Claims versus source

The English README says 'Completely free' and 'all APIs are free' but also lists cookie-backed platforms, a Groq transcription key, optional proxies and service/MCP configuration. The useful interpretation is that certain public reads do not require an API key; there is no universal no-auth or no-cost guarantee.

At the pin, `agent_reach/channels/web.py:WebChannel.check` returns `ok` without any network probe; `tests/test_web_channel.py` explicitly asserts that. The YouTube channel probes executable version and local JS configuration, not the success of a given video transcript. GitHub checks local credential metadata and returns a warning rather than verifying a live public read. These facts limit the meaning of doctor output.

Upstream issues reviewed as reports, not automatically proven findings:
- https://github.com/Panniantong/Agent-Reach/issues/685 — false-positive web doctor status.
- https://github.com/Panniantong/Agent-Reach/issues/678 — Twitter search fails while account reads work.
- https://github.com/Panniantong/Agent-Reach/issues/623 — Exa configured/working distinction.

README: https://github.com/Panniantong/Agent-Reach/blob/a19a171fa980a0785849596492e0af4db800c82f/docs/README_en.md
Source: https://github.com/Panniantong/Agent-Reach/blob/a19a171fa980a0785849596492e0af4db800c82f/agent_reach/channels/web.py

## Durable lessons

- Test a concrete read, not just availability or exit status: a doctor can deliberately avoid the network.
- With yt-dlp `--dump-single-json`, add `--no-simulate` when testing caption-file writing; otherwise selected subtitle metadata is not a downloaded transcript. Keep `--skip-download` to avoid media downloads.
- An unavailable sample video is not a platform outage. Try a distinct known public sample once and retain both outcomes; do not bypass an auth or bot wall.
- Do not infer 'anonymous access impossible' from one network/location. Conversely, one public post does not prove search or session-backed endpoints work.
