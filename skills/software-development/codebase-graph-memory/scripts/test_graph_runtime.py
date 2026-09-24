"""Real upstream CLI checks. Writes only the explicitly supplied fixture's cache index."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

BASE = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))) / 'tools/codebase-memory'
BINARY = BASE / 'runtime/v0.11.0/codebase-memory-mcp'
BINARY_SHA256 = 'a67b7ccead5d2ca852051f8619458ab96af41393257b56fb36e523a110265d48'
PROJECT = 'hermes-graph-fixture'


def run_suite(fixture, output):
    fixture = fixture.resolve(strict=True)
    assert fixture != Path.home() and fixture != Path('/'), 'Refuse broad root'
    assert {p.name for p in fixture.iterdir()} == {'math_ops.py', 'app.py', 'greeter.ts'}, 'Use only the supplied fixture'
    assert hashlib.sha256(BINARY.read_bytes()).hexdigest() == BINARY_SHA256, 'Pinned runtime changed'
    env = {}
    for key in ('PATH', 'HOME', 'USER', 'LANG', 'TMPDIR'):
        value = os.getenv(key)
        if value:
            env[key] = value
    env.update(CBM_CACHE_DIR=str(BASE / 'cache'), CBM_RUNTIME_DIR=str(BASE / 'run'),
               CBM_ALLOWED_ROOT=str(fixture), CBM_WORKERS='2', CBM_MEM_BUDGET_MB='512')
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {'fixture': str(fixture), 'binary': str(BINARY), 'binary_sha256': BINARY_SHA256, 'calls': [], 'passed': False}

    def save():
        output.write_text(json.dumps(report, indent=2) + '\n')

    def call(tool, arguments):
        command = [str(BINARY), 'cli', '--quiet', '--json', tool, json.dumps(arguments)]
        proc = subprocess.run(command, env=env, cwd=fixture, capture_output=True, text=True, timeout=120)
        record = {'command': command, 'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
        report['calls'].append(record)
        save()
        assert proc.returncode == 0, record
        envelope = json.loads(proc.stdout)
        assert not envelope.get('isError'), envelope
        content = envelope.get('structuredContent')
        if content is None:
            content = envelope['content'][0]['text']
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                pass
        record['parsed'] = content
        save()
        return content

    try:
        index = call('index_repository', {'repo_path': str(fixture), 'name': PROJECT, 'mode': 'fast', 'persistence': False})
        assert index['status'] == 'indexed' and index['nodes'] > 0 and index['edges'] > 0, index
        found = call('search_graph', {'project': PROJECT, 'name_pattern': '^(add|greeting)$', 'format': 'json', 'limit': 50})
        names = {row[0] for group in found['groups'] for row in group['rows']}
        assert names == {'add', 'greeting'} and found['total'] == 2 and not found['has_more'], found
        trace = call('trace_path', {'project': PROJECT, 'function_name': 'add', 'direction': 'inbound', 'depth': 2, 'include_evidence': True, 'format': 'json'})
        callers = {row[0] for group in trace['callers']['groups'] for row in group['rows']}
        assert callers == {'calculate', 'multiply'} and trace['callers_total'] == 2, trace
        ts = call('trace_path', {'project': PROJECT, 'function_name': 'greeting', 'direction': 'inbound', 'format': 'json'})
        assert {row[0] for group in ts['callers']['groups'] for row in group['rows']} == {'greetTeam'}, ts
        query = call('query_graph', {'project': PROJECT, 'query': "MATCH (a:Function)-[:CALLS]->(b:Function) WHERE b.name = 'add' RETURN a.name, b.name", 'format': 'json'})
        assert 'calculate' in json.dumps(query) and 'multiply' in json.dumps(query), query
        coverage = call('check_index_coverage', {'project': PROJECT, 'paths': ['math_ops.py', 'app.py', 'greeter.ts'], 'format': 'json'})
        assert 'no_recorded_issue' in json.dumps(coverage), coverage
        reopened = call('search_graph', {'project': PROJECT, 'name_pattern': '^add$', 'format': 'json'})
        assert reopened['total'] == 1, reopened
        assert not (fixture / '.codebase-memory').exists(), 'persistence=false must not export into source'
        report.update(passed=True, node_count=index['nodes'], edge_count=index['edges'],
                      separate_process_persistence=True, tested_languages=['python', 'typescript'], mode='fast')
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        save()
    print(json.dumps({k: report[k] for k in ('passed', 'node_count', 'edge_count', 'tested_languages', 'mode', 'separate_process_persistence')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/fixtures/graph-demo')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run_suite(args.fixture, args.output)
