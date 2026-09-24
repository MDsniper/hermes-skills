"""Offline contract planner acceptance tests. No agents or external writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).with_name('contracts.py')
SCRATCH = Path(os.environ.get('TMPDIR', str(Path.home() / '.hermes/cache/scratch')))


def task(name, deps=(), reads=(), writes=(), status='pending'):
    return {'id': name, 'goal': 'Verify ' + name, 'depends_on': list(deps),
            'reads': list(reads), 'writes': list(writes), 'status': status,
            'acceptance': ['Expected fixture assertion passes'], 'constraints': ['No external writes'],
            'evidence': []}


class ContractsTests(unittest.TestCase):
    def invoke(self, tasks, max_parallel=2, logs=None):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            for name, content in (logs or {}).items():
                (Path(tmp) / name).write_text(content)
            plan = {'workspace': tmp, 'tasks': tasks}
            path = Path(tmp) / 'plan.json'
            path.write_text(json.dumps(plan))
            return subprocess.run([sys.executable, str(SCRIPT), str(path), '--max-parallel', str(max_parallel)],
                                  text=True, capture_output=True)

    def test_pending_dependencies_wait_and_independent_tasks_batch(self):
        result = self.invoke([task('one', writes=['one.py']), task('two', writes=['two.py']),
                              task('three', deps=['one'], reads=['one.py'], writes=['three.py'])])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['dispatch_ids'], ['one', 'two'])
        self.assertEqual(data['waiting_ids'], ['three'])
        self.assertEqual(len(data['delegate_tasks']), 2)
        self.assertIn('Expected fixture assertion passes', data['delegate_tasks'][0]['context'])

    def test_overlapping_write_read_scopes_are_not_parallel(self):
        for first, second in [
            (task('one', writes=['src']), task('two', writes=['src/api.py'])),
            (task('one', writes=['lock.json']), task('two', reads=['lock.json'])),
            (task('one', reads=['src']), task('two', writes=['src/api.py'])),
        ]:
            with self.subTest(first=first, second=second):
                result = self.invoke([first, second])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)['dispatch_ids'], ['one'])

    def test_running_tasks_reserve_their_scopes(self):
        result = self.invoke([task('running', writes=['src'], status='running'),
                              task('wait', reads=['src/lib.py']), task('safe', writes=['docs'])])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['dispatch_ids'], ['safe'])

    def test_invalid_contracts_fail_closed(self):
        for tasks in [
            [task('a'), task('a')], [task('a', deps=['missing'])],
            [task('a', deps=['b']), task('b', deps=['a'])], [task('a', status='completed')],
            [task('a', writes=['../outside.py'])], [task('a', writes=['/outside.py'])],
            [task('a', writes=['*.py'])], [task('a', status='verified')],
        ]:
            with self.subTest(tasks=tasks):
                result = self.invoke(tasks)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('contract error:', result.stderr)
        self.assertEqual(self.invoke([task('a')], max_parallel=0).returncode, 2)

    def test_verified_receipt_unlocks_dependency_and_tamper_fails(self):
        log = 'Synthetic unit-test receipt, not external runtime evidence.\n'
        first = task('first', status='verified')
        first['evidence'] = [{'check': first['acceptance'][0], 'command': 'fixture-test',
                              'exit_code': 0, 'log': 'proof.txt',
                              'sha256': hashlib.sha256(log.encode()).hexdigest()}]
        tasks = [first, task('second', deps=['first'])]
        result = self.invoke(tasks, logs={'proof.txt': log})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['dispatch_ids'], ['second'])
        self.assertEqual(self.invoke(tasks, logs={'proof.txt': 'tampered'}).returncode, 2)
        first['evidence'][0]['exit_code'] = 1
        self.assertEqual(self.invoke(tasks, logs={'proof.txt': log}).returncode, 2)

    def test_read_only_overlap_is_parallel_and_blocked_stays_blocked(self):
        result = self.invoke([task('a', reads=['src']), task('b', reads=['src/a.py']),
                              task('blocked', status='blocked')])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['dispatch_ids'], ['a', 'b'])

    @unittest.skipIf(os.name == 'nt', 'Symlink privileges are not assumed on Windows')
    def test_symlink_escape_is_refused(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('contracts', SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        SCRATCH.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=SCRATCH) as tmp:
            root = Path(tmp)
            (root / 'escape').symlink_to(root.parent, target_is_directory=True)
            with self.assertRaises(ValueError):
                module.schedule({'workspace': str(root), 'tasks': [task('a', writes=['escape/out'])]}, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
