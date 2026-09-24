# Preservation checker: scope and case format

Run the helper through `terminal` with this skill's directory as `workdir`:

```text
python3 scripts/verify_edits.py references/fixtures.json
python3 scripts/verify_edits.py references/fixtures.json --skill humanizer
python3 scripts/verify_edits.py references/fixtures.json --skill concise-technical-writing
python3 scripts/test_verify_edits.py
```

The checker is local stdlib Python. It does not call models, edit drafts, install dependencies, or send anything to a provider. It prints a JSON report and exits nonzero for invalid input or failed expectations. Save stdout as a task artifact with `write_file` or a tool's captured output. Keep files outside the installed skill directory unless maintaining the skill via `skill_manage`.

## Input

Use `write_file` to create a JSON object with `cases`, a nonempty list:

```json
{
  "cases": [
    {
      "id": "one",
      "skill": "humanizer",
      "original": "Please note: Ada did not approve on 2026-09-24.",
      "edited": "Ada did not approve on 2026-09-24.",
      "invariants": [
        {"kind": "clause-polarity", "text": "Ada did not approve"},
        {"kind": "date", "text": "2026-09-24"}
      ],
      "semantic_review": "equivalent"
    }
  ]
}
```

`semantic_review` is a human/agent review annotation, never a result of the checker. Use `not_reviewed` or omit it until comparing all claims. Exact invariant spans must be nonempty and actually occur in the original. The checker requires at least the original count of each in the candidate, not merely one surviving copy. Include units with amounts and whole clauses for relationships; isolated names are insufficient.

Optional fields:

- `require_unchanged: true` makes any textual change an error for a negative-control passage that should not be edited.
- `requested_style`: `humanizer` (default), `concise`, or `caveman`.
- `explicit_opt_in`: must be the Boolean `true`, not a truthy string, to authorize Caveman-like wording.
- `context`: only `low-stakes` permits Caveman-like style; anything else falls back to concise.
- `selected_style`: records the register the editor actually selected. If omitted, the checker assumes the permitted selection. This is declared metadata, not intent detection or grammar classification.
- `expected_pass` defaults to `true`. Set `false` only in deliberate negative tests, not to excuse a failed real edit. `expected_errors` can require particular error strings.
- `known_limitation: true` documents an intentionally undetected bad candidate. Never put it in accepted outputs.

## What is checked

Exact declared spans; heuristic numeric literals; fenced code using ordinary backticks/tilde fences; single-backtick inline code; straight double and curly-double quoted strings; common HTTP(S) URLs; leading YAML/frontmatter; no-change controls; declared style-selection rules. Numeric and protected-span multisets detect additions as well as loss. This is not a full Markdown parser. Put unusual fences, single-quoted speech, non-HTTP link targets, malformed identifiers, spelled-out amounts, and structural/data regions into explicit invariant spans.

Metrics report Unicode codepoints as `characters`, UTF-8 `bytes`, and whitespace-delimited `words`. CJK word counts are not linguistic segmentation. Percent reduction is computed from these counts; an empty original yields null. No token or monetary claims are produced. Aggregate metrics include only cases explicitly reviewed `equivalent`, expected to pass, and not marked known limitations. Read `accepted_mechanical_passes` too; review labels do not erase failures.

## What is not checked

Regex cannot establish semantic equivalence, factual truth, naturalness, authorship, safety, or real model compliance. It can miss new unsupported prose without numeric/quoted markers; reassociation of preserved facts; pronoun ambiguity; changes in implication; or missing facts not represented in the ledger. It can also overflag valid paraphrases. Resolve mismatches by reviewing the source, not by deleting inconvenient anchors.

The corpus deliberately contrasts two tests using the same reversal:

- Original: `Ada did not approve. Ben approved.`
- Bad candidate: `Ada approved. Ben did not approve.`

Names and the single `not` survive. Weak lexical anchors pass, while whole-clause anchors reject the reversal. Manual review rejects it regardless. The passing weak-check test is a demonstration of a limitation, never evidence that the rewrite is valid.

## Acceptance discipline

Use the source to enumerate claims before drafting. First compare who/what/when/how/why and modality in both directions, then use mechanical checks as an additional guard. Retain exact quotations and technical surfaces. Test ordinary edits, technical/caution text, deliberately AI-like human prose, already-concise controls, mutated numbers/units/attribution/negation/uncertainty, and unauthorized style selection. Authored fixture pairs plus deterministic tests validate these specific examples and rules; they are not independent A/B model evaluation or proof of general writing quality.
