"""Read-only MCP reconnect check using the existing Hermes Python mcp client."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))) / 'tools/codebase-memory'
BINARY = BASE / 'runtime/v0.11.0/codebase-memory-mcp'
SHA256 = 'a67b7ccead5d2ca852051f8619458ab96af41393257b56fb36e523a110265d48'


async def probe(fixture, output):
    assert hashlib.sha256(BINARY.read_bytes()).hexdigest() == SHA256
    fixture = fixture.resolve(strict=True)
    assert fixture != Path.home() and fixture != Path('/'), 'Refuse broad root'
    assert {p.name for p in fixture.iterdir()} == {'math_ops.py', 'app.py', 'greeter.ts'}, 'Use only the supplied fixture'
    env = {k: os.environ[k] for k in ('PATH', 'HOME', 'USER', 'LANG', 'TMPDIR') if k in os.environ}
    env.update(CBM_CACHE_DIR=str(BASE / 'cache'), CBM_RUNTIME_DIR=str(BASE / 'run'),
               CBM_ALLOWED_ROOT=str(fixture), CBM_WORKERS='2', CBM_MEM_BUDGET_MB='512')
    params = StdioServerParameters(command=str(BINARY), args=['--ui=false', '--tool-profile=analysis'], env=env, cwd=str(fixture))
    report = {'binary': str(BINARY), 'fixture': str(fixture), 'sessions': [], 'passed': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        for _ in range(2):
            async with stdio_client(params) as (reader, writer):
                async with ClientSession(reader, writer) as session:
                    init = await session.initialize()
                    tools = await session.list_tools()
                    names = sorted(t.name for t in tools.tools)
                    assert 'search_graph' in names and not {'delete_project', 'index_repository', 'manage_adr', 'ingest_traces'} & set(names), names
                    result = await session.call_tool('search_graph', {'project': 'hermes-graph-fixture', 'name_pattern': '^add$', 'format': 'json'})
                    data = result.model_dump(mode='json', by_alias=True)
                    report['sessions'].append({'server': init.model_dump(mode='json', by_alias=True), 'tools': names, 'result': data})
                    output.write_text(json.dumps(report, indent=2) + '\n')
                    assert data.get('isError') is False, data
                    parsed = data.get('structuredContent') or json.loads(data['content'][0]['text'])
                    assert parsed['total'] == 1 and not parsed['has_more'], parsed
        report['passed'] = True
    except Exception as error:
        report['error'] = repr(error)
        raise
    finally:
        output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'stdio_sessions': len(report['sessions']), 'tools': report['sessions'][0]['tools']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=Path(__file__).resolve().parents[1] / 'assets/fixtures/graph-demo')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(asyncio.wait_for(probe(args.fixture, args.output), timeout=120))
