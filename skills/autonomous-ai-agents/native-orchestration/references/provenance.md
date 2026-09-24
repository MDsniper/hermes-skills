# Provenance and tested boundary

First-party Hermes workflow informed by Oh My Hermes, not a copy of its plugin.

- Upstream: https://github.com/witt3rd/oh-my-hermes
- Reviewed commit: `2a98d38b43010a438b316fb48dbe68a3c8ee8fed` (MIT, Donald Thompson).
- Pinned source: https://github.com/witt3rd/oh-my-hermes/tree/2a98d38b43010a438b316fb48dbe68a3c8ee8fed
- Read README, `plugins/omh/skills/omh-ralph/SKILL.md`, `omh-ralph-driver/SKILL.md`, `omh_delegate.py`, `hooks/llm_hooks.py`, `tools/evidence_tool.py`, and evidence tests. The actual skills reside below `plugins/omh/skills/`, not README's top-level `skills/` shorthand.
- Recent reports reviewed: https://github.com/witt3rd/oh-my-hermes/issues/25 and https://github.com/witt3rd/oh-my-hermes/issues/19. These report installation/profile/toolset friction, not locally reproduced current Hermes failures. The release listing returned no published releases at review.

Retained: bounded task contracts, dependency-aware scheduling, explicit output artifacts, disjoint write scopes, parent evidence gathering, and acceptance review. Replaced: plugin role markers and hooks with self-contained native delegation contexts; OMH state engine with an explicit user-owned JSON contract for short work. Durable work belongs in Hermes's existing Kanban/cron, not this helper. Rejected: mandatory fan-out, automatic skill copying, global mode injection, and fixed iteration/retry numbers presented as runtime facts.

Current docs checked at review:

- https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation
- https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills

Installed Hermes source at review: `0087827510b6a184d512c90b08d4566fcf68b346`. Current delegation documentation supersedes older local reference claims about blocking behavior, concurrency defaults and durable delivery. Completed events can persist; interrupted child execution does not resume.

Validation: the included offline tests exercise scheduling, directory and read/write conflicts, running reservations, invalid DAGs, path traversal, evidence presence/hash checks and tampering. They do not dispatch agents, enforce an OS sandbox or certify truth of a child report. End-to-end native delegation is the parent's responsibility; do not invent a nested delegation test from a leaf session.

For inspecting upstream with Hermes's Skills Hub, use a concrete path, e.g. `witt3rd/oh-my-hermes/plugins/omh/skills/omh-ralph`, or a pinned raw SKILL URL. `owner/repo` alone is not a complete skill identifier in the tested Hermes version. No upstream skill is installed automatically by this adaptation.

Durable lesson: a persisted output path is a receipt, not acceptance; require the exact check's real log and parent source review before unlocking dependents.
