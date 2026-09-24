"""Read-only task planner; no dispatch, shell execution, or state mutation."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def scoped(root, value):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or any(c in value for c in '*?[]\\\\') or '..' in Path(value).parts:
        raise ValueError('scope must be a literal relative path without traversal')
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError('scope escapes workspace through a symlink')
    return path


def validate(plan, max_parallel):
    if type(max_parallel) is not int or max_parallel < 1:
        raise ValueError('max-parallel must be positive')
    root = Path(plan['workspace'])
    if not root.is_absolute() or not root.is_dir():
        raise ValueError('workspace must be an existing absolute directory')
    root = root.resolve()
    if root in (Path.home().resolve(), Path(root.anchor)):
        raise ValueError('name a project, not a home or filesystem root')
    tasks = plan['tasks']
    if not isinstance(tasks, list) or not tasks or len(tasks) > 1000:
        raise ValueError('tasks must be a nonempty list of at most 1000 contracts')
    ids = []
    for task in tasks:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', task['id']):
            raise ValueError('invalid task id')
        ids.append(task['id'])
        if not isinstance(task['goal'], str) or not task['goal'].strip():
            raise ValueError('goal is required')
        if task['status'] not in {'pending', 'running', 'verified', 'blocked', 'unknown'}:
            raise ValueError('invalid status; completed is not verified')
        for field in ('depends_on', 'reads', 'writes', 'acceptance', 'constraints'):
            if not isinstance(task[field], list) or any(not isinstance(v, str) or not v.strip() for v in task[field]):
                raise ValueError(field + ' must be a list of nonempty strings')
        if not task['acceptance'] or not task['constraints']:
            raise ValueError('acceptance checks and constraints are required')
        for value in task['reads'] + task['writes']:
            scoped(root, value)
        if not isinstance(task['evidence'], list):
            raise ValueError('evidence must be a list')
        if task['status'] == 'verified':
            checks = set()
            for receipt in task['evidence']:
                if type(receipt['exit_code']) is not int or receipt['exit_code'] != 0 or not isinstance(receipt['command'], str) or not receipt['command'].strip():
                    raise ValueError('verified receipt requires a command and exit_code 0')
                log = scoped(root, receipt['log'])
                if not log.is_file() or not re.fullmatch(r'[a-f0-9]{64}', receipt['sha256']) or hashlib.sha256(log.read_bytes()).hexdigest() != receipt['sha256']:
                    raise ValueError('evidence log missing or hash mismatch')
                checks.add(receipt['check'])
            if not set(task['acceptance']) <= checks:
                raise ValueError('every acceptance check needs evidence')
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate task id')
    by_id = {t['id']: t for t in tasks}
    for task in tasks:
        if not set(task['depends_on']) <= set(ids):
            raise ValueError('unknown dependency')
        if task['status'] == 'verified' and any(by_id[d]['status'] != 'verified' for d in task['depends_on']):
            raise ValueError('verified task has unverified dependencies')
    remaining = set(ids)
    while remaining:
        ready = {i for i in remaining if not set(by_id[i]['depends_on']) & remaining}
        if not ready:
            raise ValueError('dependency cycle')
        remaining -= ready
    return root


def conflicts(left, right, root):
    def overlap(a, b):
        a, b = (root / a).resolve(), (root / b).resolve()
        return a == b or a in b.parents or b in a.parents
    return any(overlap(a, b) for a in left['writes'] for b in right['reads'] + right['writes']) or any(overlap(a, b) for a in left['reads'] for b in right['writes'])


def schedule(plan, max_parallel):
    root = validate(plan, max_parallel)
    tasks = plan['tasks']
    verified = {t['id'] for t in tasks if t['status'] == 'verified'}
    eligible = [t for t in tasks if t['status'] == 'pending' and set(t['depends_on']) <= verified]
    running = [t for t in tasks if t['status'] == 'running']
    chosen = []
    for task in eligible:
        if len(chosen) >= max(0, max_parallel - len(running)):
            break
        if not any(conflicts(task, other, root) for other in running + chosen):
            chosen.append(task)
    return {
        'dispatch_ids': [t['id'] for t in chosen],
        'waiting_ids': [t['id'] for t in tasks if t['status'] == 'pending' and t not in chosen],
        'delegate_tasks': [{'goal': t['goal'], 'context': json.dumps({'workspace': plan['workspace'], 'contract': t}, indent=2)} for t in chosen],
        'note': 'Suggestion only. Parent reviews evidence and dispatches native tools.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--max-parallel', type=int, default=1)
    args = parser.parse_args()
    try:
        result = schedule(json.loads(args.plan.read_text()), args.max_parallel)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        parser.exit(2, 'contract error: ' + str(error) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
