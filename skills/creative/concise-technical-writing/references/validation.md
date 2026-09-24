# Shared validation dependency

Call `skill_view(name='humanizer')` and use the returned `skill_dir`. That skill contains the common checker, unit tests, and paired rewrite corpus, including the concise-technical-writing cases. This skill intentionally does not duplicate the executable or fixtures.

Load its schema with `skill_view(name='humanizer', file_path='references/preservation.md')` and corpus with `skill_view(name='humanizer', file_path='references/fixtures.json')`. Run `python3 scripts/test_verify_edits.py` and `python3 scripts/verify_edits.py references/fixtures.json` through `terminal` with that directory as `workdir`. Missing dependency: stop and report it; do not install a similarly named third-party package.

For a new passage, save original, edited, exact invariant spans, and explicitly declared style/context metadata. Rules check declared opt-in and context, not real user intent; the agent must check that against the actual conversation. Even a complete literal pass cannot establish that attribution, polarity, or cause stayed attached to the same fact. `Ada did not approve. Ben approved.` and `Ada approved. Ben did not approve.` share all names and the same negation count. The corpus contains that blind spot and a stronger clause-anchor rejection.
