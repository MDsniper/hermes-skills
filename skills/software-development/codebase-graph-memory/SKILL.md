---
name: codebase-graph-memory
description: "Use when querying a repository's code graph."
version: 0.1.0
author: Ben Williams, Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [codebase, graph, mcp, structural-search, memory]
---

# Codebase graph memory

Query a local persistent structural index, then check the source before making consequential claims. Uses the reviewed, pinned Codebase Memory MCP native runtime rather than pretending to reimplement its parsers. This is a code-analysis backend, not a replacement for OpenViking or Hermes conversation memory.

## When to Use

- Find symbols, callers, dependencies, structural impact or repository architecture.
- Reopen an existing code graph between sessions without rebuilding it unnecessarily.
- Do not use an empty graph result as proof of no callers, dead code, or safe deletion.

## Prerequisites

The default-profile macOS arm64 runtime is installed at `~/.hermes/tools/codebase-memory/runtime/v0.11.0/codebase-memory-mcp`. See `references/provenance.md` for commit, checksums and scope. Other platforms/versions require separately reviewed binaries; this skill does not download or update automatically. CLI uses no Python dependency; the optional stdio smoke test uses the existing Hermes Python environment's `mcp` client.

## Procedure

1. Choose one explicit repository root, never the home directory, filesystem root, credentials directory, or a broad parent tree. Inspect project rules and ignore files. Index only source the user authorized. A refusal is a blocker: do not enroll roots, change permissions, or strip quarantine automatically.
2. Set the isolated cache and runtime paths, and set `CBM_ALLOWED_ROOT` to that exact root for **every invocation**, using `terminal`. Use a filtered environment when scripting. Do not run upstream `install`, `update`, `uninstall`, agent hooks, or auto-index enrollment; those can alter multiple agent clients.
3. Check `list_projects` and `index_status`. For a first index, explicitly call `index_repository` with an absolute `repo_path`, a unique stable `name`, `mode="fast"`, and `persistence=false`. Fast mode omits semantic embeddings. `persistence=false` disables exporting a graph artifact into the repository; the ordinary cache SQLite index still persists. Refresh after source changes before relying on old results.
4. Query `get_graph_schema`, `search_graph`, and `trace_path`. Request JSON for scripts; the outer `cli --json` only controls the MCP envelope, while each supported tool's `format="json"` controls its content. Use `structuredContent` when present; otherwise parse `content[].text`. An exit code alone is insufficient: reject `isError=true` and unexpected shapes.
5. Use exact qualified names from results with `get_code_snippet`. Run `check_index_coverage` for every material evidence path and relevant scopes. Follow every `has_more`/cursor/offset page for any exhaustive claim; record the graph generation and unresolved gaps. Check file contents with `read_file`/`search_files` when coverage is stale, missing, partial or uncertain.
6. Preserve architectural decisions through existing project notes or explicit `manage_adr` if requested. Pass exact project/generation, paths, queries, pagination and limitations in `delegate_task.context` when delegating; children may not have this MCP server. Do not install another conversation-memory provider.

## Quick Reference

Use `terminal` to set these variables for the current terminal session. Substitute an approved absolute repository root; `ROOT` is not a whole-home scan target:

```sh
H="${HERMES_HOME:-$HOME/.hermes}"
B="$H/tools/codebase-memory/runtime/v0.11.0/codebase-memory-mcp"
ROOT="/absolute/path/to/approved/repository"
export CBM_CACHE_DIR="$H/tools/codebase-memory/cache"
export CBM_RUNTIME_DIR="$H/tools/codebase-memory/run"
export CBM_ALLOWED_ROOT="$ROOT"
export CBM_WORKERS=2 CBM_MEM_BUDGET_MB=512
```

Then, through `terminal`:

```sh
"$B" --version
"$B" cli --quiet --json list_projects '{}'
"$B" cli --quiet --json index_repository "{\"repo_path\":\"$ROOT\",\"name\":\"my-repo\",\"mode\":\"fast\",\"persistence\":false}"
"$B" cli --quiet --json search_graph '{"project":"my-repo","name_pattern":"Handler","format":"json"}'
"$B" cli --quiet --json trace_path '{"project":"my-repo","function_name":"exactName","direction":"both","include_evidence":true,"format":"json"}'
"$B" cli --quiet --json check_index_coverage '{"project":"my-repo","paths":["src/file.py"],"format":"json"}'
```

For paths containing quotes, construct JSON with Python `json.dumps` and pass an argv list; do not interpolate untrusted text into shell commands. The example memory budget is a bound, not a promise large repositories fit in it. Investigate an over-budget failure before deliberately raising it.

## Optional native MCP registration

Not registered globally by this skill. `references/mcp-registration.md` gives the minimal parent/user-run `hermes mcp add` command with a read-only `analysis` tool profile, explicit scope, isolated paths, and verification. The installed skill is usable now through CLI without a gateway restart. Do not change live tool schemas mid-conversation.

## Pitfalls

- The upstream installer writes client configs, skills and hooks; downloading the pinned binary alone avoids that behavior. Auto-index, auto-watch, watcher and graph UI are disabled in this isolated cache.
- Stdio sessions can create a shared per-account coordination daemon; CLI one-shot tools do not. Avoid concurrent different builds/cache roots and do not stop another client's daemon to resolve a conflict.
- Graphs are approximate static analysis. Recent upstream reports include TypeScript renamed imports missing callers and closure calls being attributed to an enclosing function. Treat these as reported limitations, not locally proven universal behavior.
- Upstream's language and benchmark counts are not this skill's coverage. Local tests exercise Python and TypeScript fast-mode graphs only, not semantic search, large repos, cross-service inference, or every grammar.
- MCP `analysis` profile intentionally excludes index/delete/ADR writes. Index explicitly through the bounded CLI before read-only MCP use.

## Verification

Use `terminal(command="python3 <skill_dir>/scripts/test_graph_runtime.py --output <durable-report.json>")`. This indexes the shipped tiny fixture, asserts symbols and call edges, executes Cypher/coverage queries, and reopens the SQLite graph in separate processes. The fixture directory must contain only its three supplied files.

For stdio, after the CLI test: `terminal(command="<hermes-python> <skill_dir>/scripts/test_graph_stdio.py --output <durable-stdio-report.json>")`. This starts two read-only MCP sessions and asserts the persisted symbol query works after reconnect, not merely that tools list successfully.
