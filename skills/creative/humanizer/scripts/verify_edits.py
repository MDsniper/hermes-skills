"""Conservative literal checks. A pass is NOT semantic equivalence."""
from collections import Counter
import argparse
import json
from pathlib import Path
import re

NUMBER = re.compile(r"(?<!\w)[+-]?\d+(?:[.,:/-]\d+)*(?:%|\b)")
PROTECTED = re.compile(
    r'^```[^\n]*\n.*?^```[^\n]*(?:\n|$)|^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)'
    r'|`[^`\n]+`|"[^"\n]*"|“[^”\n]*”|https?://[^\s)>]+',
    re.MULTILINE | re.DOTALL,
)


def protected_spans(text):
    spans = PROTECTED.findall(text)
    frontmatter = re.match(r"\A---\r?\n.*?\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if frontmatter:
        spans.append(frontmatter.group(0))
    return Counter(spans)


def select_style(requested, explicit_opt_in, context):
    """Check DECLARED metadata only, not natural-language intent."""
    if requested not in {"humanizer", "concise", "caveman"}:
        raise ValueError("unknown requested_style")
    if requested == "caveman":
        return "caveman" if explicit_opt_in is True and context == "low-stakes" else "concise"
    return requested


def audit(case):
    original, edited = case["original"], case["edited"]
    errors = []
    allowed = select_style(case.get("requested_style", "humanizer"), case.get("explicit_opt_in", False), case.get("context", "unknown"))
    if case.get("selected_style", allowed) != allowed:
        errors.append("unauthorized_register")
    if Counter(NUMBER.findall(original)) != Counter(NUMBER.findall(edited)):
        errors.append("numeric_literals_changed")
    if protected_spans(original) != protected_spans(edited):
        errors.append("protected_spans_changed")
    for anchor in case.get("invariants", []):
        text = anchor["text"]
        if not text or text not in original:
            errors.append("invalid_source_anchor:" + anchor["kind"] + ":" + text)
        elif edited.count(text) < original.count(text):
            errors.append("missing_anchor:" + anchor["kind"] + ":" + text)
    if case.get("require_unchanged") and edited != original:
        errors.append("unchanged_control_modified")
    metrics = {}
    for unit, count in [("characters", len), ("bytes", lambda s: len(s.encode("utf-8"))), ("words", lambda s: len(s.split()))]:
        before, after = count(original), count(edited)
        metrics[unit] = {"before": before, "after": after, "reduction_pct": round(100 * (1 - after / before), 2) if before else None}
    return {"id": case["id"], "passed": not errors, "errors": errors, "metrics": metrics, "invariant_count": len(case.get("invariants", [])), "semantic_equivalence": "not_established_by_checker"}


def run_suite(cases):
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    ids = [case["id"] for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate case ids")
    results, failures, accepted = [], [], []
    for case in cases:
        result = audit(case)
        expected = case.get("expected_pass", True)
        result["expected_pass"] = expected
        result["known_limitation"] = case.get("known_limitation", False)
        result["semantic_review"] = case.get("semantic_review", "not_reviewed")
        result["expectation_met"] = result["passed"] == expected and set(case.get("expected_errors", [])) <= set(result["errors"])
        if not result["expectation_met"]:
            failures.append(case["id"])
        if expected and case.get("semantic_review") == "equivalent" and not case.get("known_limitation"):
            accepted.append(result)
        results.append(result)
    aggregates = {}
    for unit in ["characters", "bytes", "words"]:
        before = sum(row["metrics"][unit]["before"] for row in accepted)
        after = sum(row["metrics"][unit]["after"] for row in accepted)
        aggregates[unit] = {"before": before, "after": after, "reduction_pct": round(100 * (1 - after / before), 2) if before else None}
    return {"case_count": len(cases), "expectation_failures": failures, "all_expectations_met": not failures, "accepted_case_count": len(accepted), "accepted_mechanical_passes": sum(row["passed"] for row in accepted), "accepted_invariant_count": sum(row["invariant_count"] for row in accepted), "accepted_metrics": aggregates, "cases": results, "limitations": "Authored examples and deterministic literal/rule checks; not independent model trials, semantic proof, tokenizer measurements, style-quality evidence, or bill savings."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="JSON object containing original/edited cases")
    parser.add_argument("--skill", help="Filter the corpus by its declared skill field")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.cases.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("root must be an object with cases")
        cases = data["cases"]
        if not isinstance(cases, list):
            raise ValueError("cases must be a list")
        if args.skill:
            cases = [case for case in cases if case.get("skill") == args.skill]
        report = run_suite(cases)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_expectations_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


