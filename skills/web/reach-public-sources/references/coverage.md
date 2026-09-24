# Public coverage measured 2026-09-24

These are individual read tests on macOS arm64, not guarantees. No browser session/cookies, proxy installation, paid provider or platform write was used.

| Source | Measurement | Limit |
|---|---|---|
| Web article | Public HTML for https://stephango.com/saw; Defuddle retained the article | One static article only |
| GitHub anonymous | Public repo metadata from api.github.com/repos/kepano/defuddle | Read metadata, not every API/code-search operation |
| GitHub CLI | Existing gh read public kepano/defuddle identity and visibility | Existing authentication may be used; not a no-key test |
| NASA RSS | Parsed feed with non-empty title/link entries | Feed content changes; assert entries, not fixed count |
| V2EX | Public hot-topics JSON with IDs, titles and URLs | This endpoint only |
| Bilibili | Public API video metadata returned code 0 and a title | Not bili-cli, subtitles or browser access |
| YouTube | yt-dlp obtained public metadata and an English VTT for UF8uR6Z6KLc; VTT dialogue was checked separately | No media download; an unavailable-impersonation warning did not prevent this successful public read. No impersonation backend was installed |
| Reddit | Public top.json returned HTTP 403 | Stopped; no authenticated fallback |
| X | Public sample HTML contained jack/status/20 text, but clean extraction emitted an upstream colon-selector error and page clutter | Marked unverified/degraded; no search or account route tested |
| Facebook, Instagram, XiaoHongShu, Boss, Xueqiu | Not tested | Session-backed routes intentionally excluded |
| LinkedIn | Not tested | Neither public profiles nor auth-backed integration exercised |
| Xiaoyuzhou | Not tested | Provider transcription key/integration excluded |
| Exa / mcporter | Not tested | No new MCP/service configuration installed |
| Jina Reader | Not tested | No anonymous-access entitlement assumed; no relay/key use |

The first YouTube test ID BaW_jenozKc was unavailable. A second public sample succeeded. The initial article check expected the wrong title; raw evidence showed 'Use the saw, fear the saw', and the rerun checked that actual title. Both unsuccessful checks were retained rather than overwritten.

`live_checks.py` writes one record per tested route and explicit records for exclusions. Its final process status means the harness completed, not that every platform succeeded. Inspect each status and the raw artifact. Summaries must distinguish metadata success from a transcript/full-article success.
