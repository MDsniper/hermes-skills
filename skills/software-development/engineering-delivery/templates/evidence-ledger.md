# Delivery evidence

## Acceptance mapping
| ID | Changed paths | Check and actual result | Raw evidence |
|---|---|---|---|
| A1 | <files> | <exit/status/assertion> | <path> |

## Execution
Record command, cwd, relevant versions, exit code and actual stdout/stderr.
- Baseline/red (confirm assertion, not environment failure):
- Minimal change/diff:
- Green focused and regression tests:
- Build/lint/types (or explicit unavailable/inapplicable):
- Browser/interaction evidence when applicable:

## Review
Reviewer identity/mode: independent / self-review (not interchangeable).
| Severity | Path:line | Finding / reproduction | Resolution and retest |
|---|---|---|---|

## Performance when relevant
Workload; repeat count; raw samples; warm/cold policy; before/after distribution; correctness gate; keep/revert decision. No measured improvement → no improvement claim.

## Handoff
Verdict; unresolved risks; exact unverified checks; rollback; allowed next actions. Mark synthetic/local fixture data, not production evidence.
