# Provenance and runtime boundary

- Upstream: https://github.com/DeusData/codebase-memory-mcp
- Installed release: https://github.com/DeusData/codebase-memory-mcp/releases/tag/v0.11.0
- Release source commit: `8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798`.
- Main branch separately reviewed at `5958f546dc0f9af9b856f4bbc1e709382ba8425f`; the installed binary is the release, not that newer main head.
- License: MIT, Copyright (c) 2025 DeusData. Upstream LICENSE and THIRD_PARTY_NOTICES.md are retained next to the runtime binary. This first-party workflow does not vendor upstream source code.
- Downloaded archive: `codebase-memory-mcp-darwin-arm64.tar.gz` from the pinned v0.11.0 release.
- Archive SHA-256: `4dee7f38b63740e6751d7a7ed7eb10291c1f2a3ea2415f599dc68370ca0a2d18`.
- Extracted executable SHA-256: `a67b7ccead5d2ca852051f8619458ab96af41393257b56fb36e523a110265d48`.
- Both matched upstream release/checksum metadata. This is checksum verification, not an independent source-to-binary reproducible build or Sigstore attestation validation.

Review included README; docs/CONFIGURATION.md; CLI/MCP dispatch and workspace guards in `src/main.c`, `src/mcp/mcp.c`, `src/foundation/workspace.c`; embedded skill at `src/cli/cli.c:1424`; and MCP test structure. There is no standalone upstream SKILL.md at this revision: the installer renders embedded C text. The embedded text's 15-tool list lags the binary's full 17-tool list. Live discovery is authoritative. The read-only analysis profile exposes 13 tools in the tested release.

Retained the actual native C/tree-sitter/SQLite engine because reimplementing its grammar catalog and resolvers here would be misleading. The first-party layer scopes indexing, keeps installers/hooks out, emphasizes fresh generation/coverage/source evidence and teaches native Hermes CLI/MCP use. Auto-index, auto-watch, watcher subsystem and UI were explicitly disabled in the isolated cache. No global Hermes config, gateway, profiles, SOUL or OpenViking changes.

Recent reports reviewed:

- https://github.com/DeusData/codebase-memory-mcp/issues/2297 — TypeScript renamed-import callers reportedly missing.
- https://github.com/DeusData/codebase-memory-mcp/issues/2293 — closure/lambda call attribution reportedly misleading.

These are upstream user reports, not proof every repository or this release behaves identically. Current README reports 162 languages while an older pipeline bullet still says 158 grammars; neither is locally certified. Marketing speed/token/quality benchmarks are not reproduced.

Real local validation on macOS arm64: three fixture files in Python/TypeScript, fast-mode index, 25 nodes and 43 edges; exact symbol search, Python inbound callers (`calculate`, `multiply`), TypeScript caller (`greetTeam`), Cypher relationship query, coverage query, and persistence across separate CLI processes. Two stdio sessions with analysis profile queried the stored symbol after reconnect. MCP SDK 2.x exposes Python `is_error`/`structured_content`; serialize with `model_dump(by_alias=True)` when testing wire names `isError`/`structuredContent`.

Not validated: all 162 languages, semantic/full mode, large monorepos, cross-service inference, graph UI, dynamic call completeness, installer integration, or global MCP registration. Stored structural graphs complement, not replace, conversation memory.

Hermes documentation: https://hermes-agent.nousresearch.com/docs/reference/mcp-config-reference and https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation.

Durable lesson: a successful MCP handshake is insufficient; assert a known graph result, end the session, then query again after reopen while recording the exact runtime hash.
