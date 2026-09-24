# Optional default-profile MCP registration

CLI works without this step. Parent/user decides whether to add the server; this document is not permission to edit live config automatically. Inspect `hermes mcp add --help` first. In the tested Hermes version `--args` must be last and adding is interactive.

Choose one approved repository and retain this read-only MCP surface; indexing remains an explicit bounded CLI action. Run with `terminal` after inspecting the variables:

```sh
H="$HOME/.hermes"
B="$H/tools/codebase-memory/runtime/v0.11.0/codebase-memory-mcp"
ROOT="/absolute/path/to/approved/repository"
printf 'Y\n' | HERMES_HOME="$H" hermes mcp add codebase_graph \
  --command "$B" \
  --connect-timeout 60 \
  --env "CBM_CACHE_DIR=$H/tools/codebase-memory/cache" \
        "CBM_RUNTIME_DIR=$H/tools/codebase-memory/run" \
        "CBM_ALLOWED_ROOT=$ROOT" "CBM_WORKERS=2" "CBM_MEM_BUDGET_MB=512" \
  --args --ui=false --tool-profile=analysis
HERMES_HOME="$H" hermes config set mcp_servers.codebase_graph.trust untrusted
HERMES_HOME="$H" hermes config set mcp_servers.codebase_graph.sampling.enabled false
HERMES_HOME="$H" hermes config set mcp_servers.codebase_graph.tools.prompts false
HERMES_HOME="$H" hermes config set mcp_servers.codebase_graph.tools.resources false
HERMES_HOME="$H" hermes mcp test codebase_graph
HERMES_HOME="$H" hermes mcp list
```

Verify the exact named config entry was saved and the discovered analysis tools exclude `index_repository`, `delete_project`, `manage_adr`, and `ingest_traces`. Never add this over an existing unrelated server name. Use a new session for live model tools, not a gateway restart. The docs offer `/reload-mcp`, but do not change a running conversation's cached tool schema for this task.

Tool names are `mcp__codebase_graph__search_graph`, etc.; load them by tool search/describe and call them with the project name. Assert a known query returns expected source symbols — not just `Tools discovered`. `CBM_ALLOWED_ROOT` primarily confines indexing/session scope; it is not a promise of OS-level filesystem isolation for a native executable. Use a dedicated cache and never expose this server to an untrusted remote principal.

The command syntax was verified through `hermes mcp add --help`; global registration is intentionally not performed by the adaptation's acceptance tests. The standalone stdio test exercised the same binary/flags/env without editing Hermes config.
