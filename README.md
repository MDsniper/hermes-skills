# Hermes Agent Skill Pack

Ten validated skills for [Hermes Agent](https://hermes-agent.nousresearch.com), researched and built as Hermes-native adaptations of ten upstream skill projects. Every skill ships its own tests, provenance (`references/provenance.md`) and pinned dependencies; see `docs/VALIDATION-REPORT.md` for the full validation record (8/8 test suites, live read-only platform checks, static-scan review).

## Install

**Important:** on Hermes v0.21.x the `hermes skills install owner/repo` shortcut does not resolve a root-level skill — you must pass the full path to the skill directory. Each command below is the exact working form:

```bash
hermes skills install MDsniper/hermes-skills/skills/autonomous-ai-agents/native-orchestration
hermes skills install MDsniper/hermes-skills/skills/software-development/codebase-graph-memory
hermes skills install MDsniper/hermes-skills/skills/web/reach-public-sources
hermes skills install MDsniper/hermes-skills/skills/web/clean-web-content
hermes skills install MDsniper/hermes-skills/skills/creative/humanizer
hermes skills install MDsniper/hermes-skills/skills/creative/concise-technical-writing
hermes skills install MDsniper/hermes-skills/skills/software-development/engineering-delivery
hermes skills install MDsniper/hermes-skills/skills/creative/interface-polish
hermes skills install MDsniper/hermes-skills/skills/productivity/markdown-pdf-studio
hermes skills install MDsniper/hermes-skills/skills/security/defensive-security-review
```

Verify after installing: `hermes skills inspect <name>`, then run the skill's `scripts/test_*.py`.

All ten were verified end-to-end against a fresh Hermes v0.21.4 home on 2026-09-24: every install resolves from GitHub and passes the built-in security scan with verdict SAFE — no `--force` needed anywhere.

## The skills

| Skill | What it does | Runtime needs |
|---|---|---|
| `native-orchestration` | Multi-agent fan-out on native `delegate_task`: task contracts, evidence ledger, honest limits | none |
| `codebase-graph-memory` | Persistent code knowledge graph with stdio MCP interface (13 read-only tools) | pinned v0.11.0 engine under `~/.hermes/tools/codebase-memory` (see `references/provenance.md`) |
| `reach-public-sources` | Read-only reach beyond `web_extract`/search: GitHub API, RSS, V2EX, Bilibili, yt-dlp transcripts | pinned venv under `~/.hermes/tools/reach-public-sources` (pins in `references/requirements.lock`) |
| `clean-web-content` | Extract article content from hostile HTML using Defuddle 0.19.4 | npm package on demand (`npx defuddle-cli`) |
| `humanizer` | Remove AI writing tells while preserving facts (fact-anchor preservation check) | none |
| `concise-technical-writing` | Blunt, short technical writing (opt-in only) | none |
| `engineering-delivery` | One production-grade engineering lifecycle: scoped change → TDD → evidence → review | none |
| `interface-polish` | UI behavior/interaction polish with in-browser verification | Hermes browser tools |
| `markdown-pdf-studio` | Markdown → themed PDF, 5 themes, real CJK fallback (Chromium/Playwright backend) | tool dir `~/.hermes/tools/markdown-pdf` (see `references/setup.md`) |
| `defensive-security-review` | Authorization-first defensive config review; 818-entry upstream domain catalog inert under `references/` | none |

## Fresh-machine setup for runtime skills

Three skills wrap pinned runtimes in `~/.hermes/tools/`. Each documents exact recovery:

- `codebase-graph-memory` → `references/provenance.md` (release archive + SHA-256s)
- `reach-public-sources` → `references/requirements.lock` (`uv venv` + `uv pip install --require-hashes`)
- `markdown-pdf-studio` → `references/setup.md` (pinned venv, Playwright headless shell, verified Noto CJK font download)

## Scope and safety

These are defensive/review and productivity skills. `defensive-security-review` is explicitly authorization-first (config review only — no scanning or exploitation), and its catalog is inert metadata. No skill contains credentials or machine-local paths.

## License

MIT for first-party material (see `LICENSE`). Adaptations retain upstream notices: see `THIRD_PARTY_NOTICES.md` and the per-skill `references/` files. The security catalog is derived from mukul975/Anthropic-Cybersecurity-Skills (Apache-2.0, text in `third-party-licenses/`).
