# Review and acceptance sheet

Mode: quick / full. Scope: exact page/component/file list. Browser/viewport/theme: exact values. Framework and styling convention: observed source, not assumed.

## State contract
| Control | Idle / unavailable | Focus / pressed | Pending / duplicate input | Error / retry | Success |
|---|---|---|---|---|---|
| Primary action | explicit reason when unavailable | visible ring; Enter/Space semantics | synchronous guard, text, busy state; focus retained deliberately | values retained; linked field feedback | actual completed effect named |

## Coverage
| Pass | Evidence inspected | Findings or explicitly not reviewed |
|---|---|---|
| Typography | wrapping, actual font/fallback, 99→100 or long value, zoom | |
| Surfaces | narrow/wide layout, target sizes, focus and forced colors | |
| Icons | names, decorative hiding, optical weight, state meaning | |
| Motion | normal/reduced, reversal, base transition declarations | |
| Performance | payload, external requests, console, scoped measurements | |

## Findings
| Severity | Path:line or exact component | Before → After | Why / verification |
|---|---|---|---|

High = inaccessible, misleading, unreadable or repeatedly disruptive; medium = noticeable usability/consistency defect; low = isolated polish. Consolidate a shared defect while retaining affected locations. Never report low items in quick mode.

## Considered but rejected
List only real candidates and the evidence for not changing them. Preserve existing tokens over arbitrary stylistic rewrites; prefer no animation when frequent input would make it distracting.

## Verdict
Block / Needs changes / Approve within tested scope. Commands, actual results, screenshot paths and manual observations. List not-verified checks directly beside the verdict: screen reader, other browser/device, complex motion playback, zoom, RTL, production persistence, field performance as applicable.

## Durable test lesson
- Check disabled behavior on the actual input/button, not solely on a disabled fieldset: automation libraries may report a fieldset as enabled while its descendants are correctly disabled. Preserve the intended user-facing assertion instead of weakening it.
- Keep status live regions outside busy subtrees: inherited busy state can delay the very loading announcement the user needs.
- Test the entire counter including its denominator at narrow widths: stable digit width can pass while “100 / 120” still wraps. Keep the unit together and let adjacent help text wrap.
- Create an explicit Playwright browser context for axe-core scans: the convenience browser.newPage context cannot open axe's analysis page.
