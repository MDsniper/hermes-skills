"""Offline tests for literal safeguards, not semantic-equivalence tests."""
import importlib.util
from pathlib import Path
import unittest
import subprocess
import sys
import json

# Keep test execution from creating generated files in the skill.
sys.dont_write_bytecode = True


class PreservationTests(unittest.TestCase):
    def load_helper(self):
        path = Path(__file__).with_name("verify_edits.py")
        self.assertTrue(path.is_file(), "Missing preservation validator")
        spec = importlib.util.spec_from_file_location("verify_edits", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_declared_claim_loss_is_rejected(self):
        helper = self.load_helper()
        result = helper.audit({
            "id": "negation-loss",
            "original": "The backup is not verified.",
            "edited": "The backup is verified.",
            "invariants": [{"kind": "negation", "text": "is not verified"}],
        })
        self.assertFalse(result["passed"])
        self.assertIn("missing_anchor:negation:is not verified", result["errors"])

    def test_numbers_and_protected_spans_are_unchanged(self):
        helper = self.load_helper()
        original = 'As of 2026-09-24, retry `job_a` 3 times. Ada said “not ready”.'
        for edited in [original.replace('3 times', '4 times'), original.replace('job_a', 'job_b'), original.replace('not ready', 'ready')]:
            with self.subTest(edited=edited):
                self.assertFalse(helper.audit({'id': 'protected', 'original': original, 'edited': edited, 'invariants': []})['passed'])
        self.assertTrue(helper.audit({'id': 'same', 'original': original, 'edited': original, 'invariants': []})['passed'])

    def test_caveman_needs_opt_in_and_low_stakes(self):
        helper = self.load_helper()
        self.assertTrue(hasattr(helper, 'select_style'), 'Missing register selection guard')
        self.assertEqual(helper.select_style('caveman', False, 'low-stakes'), 'concise')
        self.assertEqual(helper.select_style('caveman', True, 'low-stakes'), 'caveman')
        for context in ['technical', 'safety', 'error', 'third-party', 'unknown']:
            self.assertEqual(helper.select_style('caveman', True, context), 'concise')
        self.assertEqual(helper.select_style('concise', False, 'low-stakes'), 'concise')
        bad = {'id': 'unsafe-mode', 'original': 'Do not restart.', 'edited': 'Do not restart.', 'requested_style': 'caveman', 'explicit_opt_in': False, 'context': 'safety', 'selected_style': 'caveman'}
        self.assertIn('unauthorized_register', helper.audit(bad)['errors'])

    def test_suite_counts_measures_and_keeps_no_change_controls(self):
        helper = self.load_helper()
        self.assertTrue(hasattr(helper, 'run_suite'), 'Missing measured suite runner')
        good = {'id': 'shorten', 'original': 'Please note: café stays open.', 'edited': 'café stays open.', 'invariants': [{'kind': 'claim', 'text': 'café stays open.'}], 'semantic_review': 'equivalent'}
        bad = {'id': 'keep', 'original': 'One thing.', 'edited': 'A thing.', 'require_unchanged': True, 'expected_pass': False}
        blind = {'id': 'blind', 'original': 'Ada did not approve. Ben approved.', 'edited': 'Ada approved. Ben did not approve.', 'invariants': [{'kind':'name','text':'Ada'},{'kind':'name','text':'Ben'}], 'known_limitation': True, 'semantic_review': 'not_equivalent', 'expected_pass': True}
        report = helper.run_suite([good, bad, blind])
        self.assertEqual(report['case_count'], 3)
        self.assertEqual(report['expectation_failures'], [])
        self.assertEqual(report['accepted_case_count'], 1)
        self.assertEqual(report['cases'][0]['metrics']['characters']['before'], len(good['original']))
        self.assertEqual(report['cases'][0]['metrics']['bytes']['after'], len(good['edited'].encode('utf-8')))
        self.assertEqual(report['cases'][0]['metrics']['words']['after'], len(good['edited'].split()))
        self.assertIn('unchanged_control_modified', report['cases'][1]['errors'])
        self.assertTrue(report['cases'][2]['passed'], 'Known semantic blind spot must stay visible')
        with self.assertRaises(ValueError):
            helper.run_suite([good, good])

    def test_cli_runs_the_saved_behavioral_corpus(self):
        root = Path(__file__).resolve().parents[1]
        command = [sys.executable, str(root / 'scripts/verify_edits.py'), str(root / 'references/fixtures.json')]
        result = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith('{'), 'CLI did not emit a JSON report')
        report = json.loads(result.stdout)
        cases = json.loads((root / 'references/fixtures.json').read_text(encoding='utf-8'))['cases']
        self.assertEqual(report['case_count'], len(cases))
        self.assertTrue(report['all_expectations_met'], report['expectation_failures'])
        self.assertEqual(report['accepted_case_count'], report['accepted_mechanical_passes'])
        invalid = subprocess.run(command + ['--skill', 'not-a-skill'], capture_output=True, text=True, timeout=20)
        self.assertNotEqual(invalid.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
