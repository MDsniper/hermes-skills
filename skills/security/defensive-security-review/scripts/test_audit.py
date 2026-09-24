#!/usr/bin/env python3
"""Disposable local fixture tests; no infrastructure or upstream code."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('audit.py')
GUARD = """
import runpy, sys
script = sys.argv.pop(1)
def deny_external_effects(event, args):
    if event.startswith(('socket.', 'subprocess.', 'os.exec', 'os.spawn')) or event in ('os.system', 'os.mkdir', 'os.remove', 'os.rename'):
        raise RuntimeError('external effect forbidden by fixture harness')
    if event == 'open':
        mode = args[1]
        flags = args[2]
        import os
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
            raise RuntimeError('write forbidden by fixture harness')
sys.addaudithook(deny_external_effects)
sys.argv[0] = script
runpy.run_path(script, run_name='__main__')
"""


class AuditTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(os.environ.get('TMPDIR') or Path.home() / '.hermes/cache/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='defensive-review-', dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def run_audit(self, kind, *names):
        return subprocess.run([sys.executable, '-B', '-c', GUARD, str(SCRIPT), '--root', str(self.root),
                               '--kind', kind, *names], capture_output=True, text=True,
                              timeout=10, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})

    def test_iam_wildcard_candidate_has_evidence(self):
        path = self.put('bad.json', {'Statement': [{'Effect': 'Allow', 'Action': '*',
                         'Resource': '*', 'Sid': 'SYNTHETIC_DO_NOT_ECHO'}]})
        before = path.read_bytes()
        result = self.run_audit('iam', 'bad.json')
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['summary']['findings'], 1)
        item = report['files'][0]
        self.assertEqual(item['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(item['findings'][0]['rule_id'], 'IAM001')
        self.assertEqual(item['findings'][0]['evidence']['location'],
                         {'statement_index': 0, 'fields': ['Action', 'Resource']})
        self.assertNotIn('SYNTHETIC_DO_NOT_ECHO', result.stdout + result.stderr)
        self.assertEqual(path.read_bytes(), before)

    def test_compose_explicit_risks_have_exact_rule_ids(self):
        self.put('bad-compose.json', {'services': {'SYNTHETIC_SERVICE_DO_NOT_ECHO': {
            'privileged': True, 'network_mode': 'host', 'cap_add': ['SYS_ADMIN'],
            'user': '0:1000', 'read_only': False,
            'volumes': ['/var/run/docker.sock:/socket:ro']}}})
        result = self.run_audit('compose', 'bad-compose.json')
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual({f['rule_id'] for f in report['files'][0]['findings']},
                         {'CMP001', 'CMP002', 'CMP003', 'CMP004', 'CMP005', 'CMP006'})
        self.assertEqual(report['summary']['findings'], 6)
        self.assertNotIn('SYNTHETIC_SERVICE_DO_NOT_ECHO', result.stdout + result.stderr)
        for item in report['files'][0]['findings']:
            self.assertEqual(item['evidence']['location']['service_index'], 0)

    def test_known_good_compose_avoids_substring_false_positive(self):
        self.put('good-compose.json', {'services': {'app': {
            'privileged': False, 'network_mode': 'bridge', 'cap_add': ['NET_BIND_SERVICE'],
            'user': '1000:1000', 'read_only': True,
            'environment': {'NOTE': 'privileged: true SYNTHETIC_PRIVATE_VALUE'},
            'volumes': ['logs:/logs:rw', '/logs/docker.sock.log:/logs/socket-log:ro']}}})
        result = self.run_audit('compose', 'good-compose.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'no_findings_in_supported_checks')
        self.assertNotIn('SYNTHETIC_PRIVATE_VALUE', result.stdout + result.stderr)

    def test_known_good_iam_deny_and_required_global_resource(self):
        self.put('good.json', {'Statement': [
            {'Effect': 'Deny', 'Action': '*', 'Resource': '*'},
            {'Effect': 'Allow', 'Action': ['ec2:DescribeInstances'], 'Resource': '*'},
            {'Effect': 'Allow', 'Action': 's3:*', 'Resource': 'arn:aws:s3:::fixture-only/*'}]})
        result = self.run_audit('iam', 'good.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['summary']['findings'], 0)

    def test_iam_scalar_statement_list_actions_and_condition(self):
        self.put('condition.json', {'Statement': {'Effect': 'Allow', 'Action': ['iam:Pass*'],
            'Resource': ['*'], 'Condition': {'StringEquals': {'fixture': 'SYNTHETIC_CONDITION'}}}})
        result = self.run_audit('iam', 'condition.json')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn('conditions_not_evaluated', json.loads(result.stdout)['files'][0]['not_evaluated'])
        self.assertNotIn('SYNTHETIC_CONDITION', result.stdout + result.stderr)

    def test_notaction_is_explicitly_unassessed(self):
        self.put('notaction.json', {'Statement': {'Effect': 'Allow', 'NotAction': 'iam:*', 'Resource': '*'}})
        result = self.run_audit('iam', 'notaction.json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('notaction_notresource_not_evaluated', json.loads(result.stdout)['files'][0]['not_evaluated'])

    def test_invalid_iam_schemas_fail_closed(self):
        cases = [{}, {'Statement': []}, {'Statement': [{'Effect': 'Maybe', 'Action': '*', 'Resource': '*'}]},
                 {'Statement': [{'Effect': 'Allow', 'Action': None, 'Resource': '*'}]},
                 {'Statement': [{'Effect': 'Allow', 'Action': '*', 'NotAction': '*', 'Resource': '*'}]},
                 {'Statement': [{'Effect': 'Allow', 'Action': '*', 'Resource': '*', 'Condition': []}]}]
        for doc in cases:
            with self.subTest(doc=doc):
                self.put('invalid.json', doc)
                result = self.run_audit('iam', 'invalid.json')
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['status'], 'incomplete')

    def test_missing_compose_settings_are_unknown_not_root_findings(self):
        self.put('missing.json', {'services': {'app': {'image': 'fixture-only'}}})
        result = self.run_audit('compose', 'missing.json')
        self.assertEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report['summary']['findings'], 0)
        self.assertIn('service_0_missing_user', report['files'][0]['not_evaluated'])

    def test_compose_boolean_strings_fail_closed(self):
        self.put('boolean.json', {'services': {'app': {'privileged': 'false'}}})
        result = self.run_audit('compose', 'boolean.json')
        self.assertEqual(result.returncode, 2)

    def test_compose_long_mounts_socket_readonly_and_named_volume(self):
        self.put('mounts.json', {'services': {'app': {'volumes': [
            {'type': 'bind', 'source': '/run/user/1000/docker.sock', 'target': '/socket', 'read_only': True},
            {'type': 'bind', 'source': '/', 'target': '/host', 'read_only': True},
            {'type': 'volume', 'source': 'docker.sock', 'target': '/not-a-host-socket'}]}}})
        result = self.run_audit('compose', 'mounts.json')
        self.assertEqual(result.returncode, 1)
        findings = json.loads(result.stdout)['files'][0]['findings']
        self.assertEqual([f['rule_id'] for f in findings], ['CMP004', 'CMP004'])
        self.assertEqual([f['evidence']['location']['volume_index'] for f in findings], [0, 1])

    def test_compose_user_variants(self):
        for value, code in [(0, 1), ('00:1000', 1), ('root:staff', 1), ('1000:0', 0), ('app', 0)]:
            with self.subTest(value=value):
                self.put('user.json', {'services': {'app': {'user': value}}})
                result = self.run_audit('compose', 'user.json')
                self.assertEqual(result.returncode, code)
                if code:
                    self.assertEqual(json.loads(result.stdout)['files'][0]['findings'][0]['rule_id'], 'CMP005')

    def test_invalid_compose_shapes_fail_closed(self):
        for doc in [{}, {'services': {}}, {'services': []}, {'services': {'app': []}},
                    {'services': {'app': {'cap_add': 'ALL'}}},
                    {'services': {'app': {'volumes': [False]}}},
                    {'services': {'app': {'user': True}}}]:
            with self.subTest(doc=doc):
                self.put('invalid.json', doc)
                self.assertEqual(self.run_audit('compose', 'invalid.json').returncode, 2)

    def test_duplicate_json_keys_rejected(self):
        (self.root / 'duplicate.json').write_text('{"services":{"app":{"privileged":true,"privileged":false}}}')
        self.assertEqual(self.run_audit('compose', 'duplicate.json').returncode, 2)

    def test_nonfinite_json_rejected(self):
        for constant in ['NaN', 'Infinity', '-Infinity', '1e999']:
            with self.subTest(constant=constant):
                (self.root / 'nan.json').write_text('{"services":{"app":{}},"ignored":' + constant + '}')
                self.assertEqual(self.run_audit('compose', 'nan.json').returncode, 2)

    def test_malformed_json_does_not_echo_content(self):
        (self.root / 'malformed.json').write_text('{"SYNTHETIC_PRIVATE_VALUE":')
        result = self.run_audit('iam', 'malformed.json')
        self.assertEqual(result.returncode, 2)
        self.assertNotIn('SYNTHETIC_PRIVATE_VALUE', result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_partial_failure_is_incomplete_with_correct_totals(self):
        self.put('bad.json', {'Statement': {'Effect': 'Allow', 'Action': '*', 'Resource': '*'}})
        (self.root / 'invalid.json').write_text('{')
        result = self.run_audit('iam', 'bad.json', 'invalid.json')
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'incomplete')
        self.assertEqual(report['summary'], {'files_requested': 2, 'files_read': 2, 'findings': 1, 'input_errors': 1})

    def test_explicit_scope_refuses_absolute_and_parent_paths(self):
        path = self.put('local.json', {'services': {'app': {}}})
        for name in [str(path), '../local.json', 'nested/../local.json']:
            with self.subTest(name=name):
                result = self.run_audit('compose', name)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn('sha256', json.loads(result.stdout)['files'][0])

    def test_symlink_file_and_directory_refused(self):
        self.put('real.json', {'services': {'app': {}}})
        (self.root / 'link.json').symlink_to(self.root / 'real.json')
        (self.root / 'linkdir').symlink_to(self.root, target_is_directory=True)
        for name in ['link.json', 'linkdir/real.json']:
            with self.subTest(name=name):
                result = self.run_audit('compose', name)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(json.loads(result.stdout)['files'][0]['error'], 'symlink_refused')

    def test_missing_directory_and_nonregular_files_refused(self):
        (self.root / 'folder').mkdir()
        os.mkfifo(self.root / 'pipe')
        for name in ['not-there.json', 'folder', 'pipe']:
            with self.subTest(name=name):
                self.assertEqual(self.run_audit('iam', name).returncode, 2)

    def test_file_limit_enforced(self):
        (self.root / 'big.json').write_bytes(b' ' * (1024 * 1024 + 1))
        result = self.run_audit('iam', 'big.json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['files'][0]['error'], 'file_too_large')

    def test_file_count_and_duplicates_refused(self):
        self.assertEqual(self.run_audit('iam', *[str(i) + '.json' for i in range(33)]).returncode, 2)
        self.assertEqual(self.run_audit('iam', 'same.json', 'same.json').returncode, 2)

    def test_help_does_not_need_a_target(self):
        result = subprocess.run([sys.executable, '-B', '-c', GUARD, str(SCRIPT), '--help'],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn('--root', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
