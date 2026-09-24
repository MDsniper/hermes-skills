# Ten Upstream Skill Projects — Deep Research, Hermes-Native Adaptations, Validation

Date: 2026-09-24. Profile: `default` only (`/Users/bwilliams/.hermes`). Runtime: Hermes v0.21.4 (2026.9.21), upstream `00878275`, macOS arm64, Python 3.11.15.

## Verdict summary

All ten projects were researched at pinned commits and delivered as **ten first-party Hermes skills** (nine new, one updated in place) plus reviewed upstream engines where rebuilding would have destroyed capability. Every skill was re-validated by the parent after worker completion: fresh-loader discovery, frontmatter/reference/syntax checks, Hermes's static security scanner, and independent test reruns — **8/8 test suites green** (65 test cases total), one live platform sweep green. No upstream repo-root `hermes skills install` command from the brief works on this Hermes version; see "Installer bug" below.

| Upstream | Delivered skill | Parent-rerun tests | Result |
|---|---|---|---|
| witt3rd/oh-my-hermes [4] | `native-orchestration` | 7 unittest methods (task contracts, DAG, evidence ledger) | PASS |
| DeusData/codebase-memory-mcp [5] | `codebase-graph-memory` | graph 25 nodes/43 edges (Python+TS), separate-process persistence, 2 stdio MCP sessions, 13 read-only tools | PASS |
| Panniantong/Agent-Reach [6] | `reach-public-sources` | live sweep: 6 platforms success, 1 blocked, 1 unverified, 8 excluded | PASS (honest gaps) |
| kepano/defuddle [7] | `clean-web-content` | fixture extraction + fail-closed wrapper tests (worker run; harness green on parent live rerun) | PASS |
| blader/humanizer [8] | `humanizer` (updated) | 5 unittest methods + 29-case corpus, 38 fact anchors retained | PASS |
| JuliusBrussee/caveman [9] | `concise-technical-writing` | same corpus: opt-in gating, protected spans, measured reductions | PASS |
| addyosmani/agent-skills [10] | `engineering-delivery` | 3 contract tests + 6 pagination tests (red→green TDD evidence retained) | PASS |
| jakubkrehel/make-interfaces-feel-better [11] | `interface-polish` | 4 browser tests (retry, linked errors, busy state, focus), 6 axe scans, reduced-motion + forced-colors captures | PASS |
| daymade PDF Creator [12] | `markdown-pdf-studio` | 10 tests: 5 themes × CJK/tables/code/pagebreak, uneven-table right borders, multi-page tables, embedded TrueType CJK + extracted text | PASS |
| mukul975/Anthropic-Cybersecurity-Skills [13] | `defensive-security-review` (+ 818-row local catalog, not activated) | 22 unittest methods (known-good/known-bad fixtures, fail-closed paths) | PASS |

Integrity: the three other profiles show **zero file changes** against a pre-run hash baseline of 1,969 files. Within `~/.hermes/skills`: 9 SKILL.md added, 0 removed, 2 modified (`humanizer` by design; `hermes-agent` where I corrected delegation guidance and added the third-party skill-validation reference). Backup: `skills-before.tar.gz`. Full evidence tree: `/Users/bwilliams/.hermes/workspace/skill-lab-20260924/` (per-project `manifest.json`/`research.md`, `independent-test-reruns.json`, `static-scan-results.json`, `reach-live-rerun.json`).

## Installer bug (affects the brief's copy-paste commands)

All ten provided `hermes skills install owner/repo` identifiers fail with `Error: Could not find '<id>' in any source` — **while exiting 0**, so scripting on exit code alone silently "succeeds" at doing nothing.[3] Root cause: Hermes v0.21.4's GitHub skill source requires `owner/repo/path/to/skill`; a root-level SKILL.md needs its verified raw URL instead (confirmed working for Humanizer).[1][3] The correct pattern is now documented in the `hermes-agent` skill (`references/third-party-skill-validation.md`). None of the adaptations used `--force` or bypassed any scan.

## Claim checks (brief vs. source at pin)

- **Humanizer "35 patterns"**: current upstream consolidated 35 → **25** patterns ("nothing dropped").[8] Adaptation targets the pinned current text.[8]
- **Cybersecurity "817 skills, 29 domains"**: 817 skills is right; the domain count was a stale table — upstream's own correction regenerates **34 domains** from frontmatter.[13] Local catalog holds 818 rows (one extra entry versus the README count; recorded, not silently normalized).[13]
- **"Anthropic" Cybersecurity Skills**: not Anthropic-owned — GitHub user `mukul975` (Mahipal); the README itself disclaims Anthropic PBC affiliation; the repository is Apache-2.0.[13]
- **PDF Creator "four themes"**: installed adaptation ships **five** themes (upstream evolved), each exercised.[12]
- **Codebase Memory "158 languages, sub-millisecond"**: engine reused at pinned v0.11.0; only Python and TypeScript were exercised and query latency was not benchmarked — treat both figures as upstream claims.[5]
- **Caveman "cuts ~65%"**: measured per fixture (for example 8.7% on one control case); 65% is not universal, and reductions vary by text.[9]
- **Agent Reach "no API keys, no fees"**: true for the six public routes tested (GitHub, RSS, V2EX, Bilibili, YouTube metadata/captions, GitHub CLI); Reddit returned 403 unauthenticated, X public HTML stayed unverified, and session-backed platforms (Facebook, Instagram, XiaoHongShu, LinkedIn, Boss Zhipin, Xueqiu) were deliberately excluded rather than smuggled through cookies.[6]

## Per-project detail

**1–2. Orchestration + code memory.** `native-orchestration` is a first-party task-contract + evidence-ledger workflow on native `delegate_task` (verified against live Hermes delegation docs — batch schema, current 10-child default, background/join semantics) rather than Oh My Hermes's plugin layer.[1][2][4] Live end-to-end proof: this project itself ran as one 6-child parallel fan-out with per-child contracts. `codebase-graph-memory` wraps the reviewed DeusData engine (MIT) installed under `~/.hermes/tools/codebase-memory/` with a stdio MCP procedure and a repo-scoped index; it never replaces OpenViking and never indexes outside the target repo.[5] Pin: oh-my-hermes `2a98d38` (MIT, Donald Thompson).[4]

**3–4. Reach + extraction.** `reach-public-sources` (Agent Reach pin `a19a171`, MIT, © Agent Eyes) uses an isolated pinned venv (`~/.hermes/tools/reach-public-sources/.venv`: yt-dlp 2026.8.19, feedparser 6.0.14, hash-locked) and never touches cookies, logins, or posting.[6] `clean-web-content` wraps the real Defuddle 0.19.4 npm engine (pin `d4c4bad`, MIT, © Steph Ango)[7] — README/package/CLI at the chosen release verified byte-equal to reviewed main.[7] Parent live rerun: GitHub/RSS/V2EX/Bilibili/YouTube/gh all returned verified data.

**5–6. Writing.** `humanizer` (pin `9862685`, MIT) replaces the previously installed copy: fabricated examples and forced-voice instructions removed, fact-anchor preservation enforced by `scripts/verify_edits.py` (numbers, dates, identifiers, quotes, negations must survive; unsupported additions rejected), with a documented manual semantic review step because literal checks can't prove equivalence.[8] `concise-technical-writing` is the Caveman opt-in adaptation (pin `2fd153c`; repo carries LICENSE + LICENSE.BSL + LICENSING.md — adaptation copies no upstream code):[9] blunt mode is explicitly requested, low-stakes only, and never abbreviates errors, security, or commands.[9] Corpus result: 29 cases — 14 accepted rewrites with 38/38 anchors retained, 14 negative controls rejected, 1 blind spot documented, 6 no-change controls untouched.

**7–8. Engineering + interface.** `engineering-delivery` distills Addy Osmani's ~24-skill bundle (pin `bcab6a1`, MIT) into one change-lifecycle procedure instead of activating 24 overlapping skills;[10] inventory of exact upstream names retained for selective use.[10] `interface-polish` (MIT) encodes the animation/typography/micro-interaction opinions with accessibility floors; the browser-tested local fixture proves retry-after-error, linked validation, busy/submit-locking and focus behavior, with axe JSON and forced-colors/reduced-motion captures retained. Upstream note recorded: PR #5 closed unmerged and issue #4 points to a newer `/better` collection — flagged, not silently merged into our text.[11]

**9. PDF.** `markdown-pdf-studio` is a first-party workflow "inspired by" the daymade bundle (no upstream code copied; our skill is MIT)[12] rendering with **pinned Chromium via Playwright** in `~/.hermes/tools/markdown-pdf/` — not pandoc/WeasyPrint — with the actual backend recorded in every generated document, external resource requests blocked at render time (fail-closed), and Apple PDFKit/pdfium cross-checks.[12] All 5 themes × CJK + wide/uneven tables were rendered and inspected; this specifically exercises the table-edge clipping class the upstream fixed in `d6d4705` (text extraction alone misses it).

**10. Security.** `defensive-security-review` (Apache-2.0 source concepts, our text; pin `54a7988`) is authorization-first and fixture-only:[13] seven bounded IAM/Compose checks plus manual-review procedures for K8s/Cloudflare/Traefik/IaC, MITRE ATT&CK/NIST CSF 2.0/ATLAS/D3FEND mappings recorded as metadata, and explicit non-compliance language.[13] The other 817 upstream entries live in a searchable local catalog with `installed: false` — available for later domain picks without activating hundreds of unreviewed playbooks. Nothing scans live hosts.

## Security review of the installed skills

Hermes's scanner (the same `tools/skills_guard` engine behind hub installs) verdicts: 4 safe, 5 caution, 1 "dangerous". Every flagged finding was reviewed in context: test-harness `subprocess` calls, `os.environ` filtering **down** to safe vars, one `PLAYWRIGHT_BROWSERS_PATH` setter, and one fixture-HTML false positive. No network exfiltration, credential access, persistence, or obfuscation in any installed skill. Scan verdict ≠ safety guarantee; findings recorded in `static-scan-results.json`.

## What was NOT done / limits

- No upstream repo-root installs (impossible on this version — see installer bug); no `--force`.
- Unverified claims (158 languages, sub-ms queries, universal 65% cut) are labeled as upstream claims above, not results.[5][9]
- Session-backed platforms in Agent Reach and 817 non-selected security skills are deliberately uninstalled/untested.
- Semantic quality of prose rewrites needs human judgment; the checker proves fact retention only.[8]
- The `pdf`/`security`/`reach`/`engineering` workspaces have research docs + evidence files rather than the strict per-project `manifest.json` shape (writing + orchestration do); this report plus `independent-test-reruns.json` carries the equivalent fields.

## Sources

[1] https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
[2] https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation
[3] https://hermes-agent.nousresearch.com/docs/reference/cli-commands
[4] https://github.com/witt3rd/oh-my-hermes
[5] https://github.com/DeusData/codebase-memory-mcp
[6] https://github.com/Panniantong/Agent-Reach
[7] https://github.com/kepano/defuddle
[8] https://github.com/blader/humanizer
[9] https://github.com/JuliusBrussee/caveman
[10] https://github.com/addyosmani/agent-skills
[11] https://github.com/jakubkrehel/make-interfaces-feel-better
[12] https://github.com/daymade/claude-code-skills/tree/main/daymade-docs/pdf-creator
[13] https://github.com/mukul975/Anthropic-Cybersecurity-Skills
