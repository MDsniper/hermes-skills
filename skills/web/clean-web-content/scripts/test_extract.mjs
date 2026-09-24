import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';
import { mkdirSync, writeFileSync } from 'node:fs';
const skill = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = resolve(process.argv[2] || './extraction-checks');
mkdirSync(out, { recursive: true });
const rows = [];
function run(name, fixture, url) {
  const args = [join(skill, 'scripts/extract.mjs'), join(skill, 'assets', fixture), url];
  const r = spawnSync(process.execPath, args, { encoding: 'utf8', timeout: 30000 });
  writeFileSync(join(out, `${name}.stdout`), r.stdout || '');
  writeFileSync(join(out, `${name}.stderr`), r.stderr || '');
  return r;
}
function check(name, fn) {
  try { fn(); rows.push({ name, status: 'pass' }); }
  catch (e) { rows.push({ name, status: 'fail', error: String(e) }); }
}
check('article-content-and-metadata', () => {
  const r = run('article', 'article.html', 'https://example.com/articles/test');
  assert.equal(r.status, 0, r.stderr);
  const d = JSON.parse(r.stdout);
  assert.equal(d.title, 'Field Notes on Reliable Extraction');
  assert.equal(d.author, 'Ada Example');
  assert.match(d.published, /2026-09-24/);
  for (const s of ['ARTICLE_START_SENTINEL','MIDDLE_SENTINEL','ARTICLE_END_SENTINEL','café','日本語','print("hello, extraction")','granite','flexible','https://example.com/reference']) assert.ok(d.content.replaceAll('\\_', '_').includes(s), s);
  for (const s of ['NAVIGATION_SENTINEL','SIDEBAR_SENTINEL','FOOTER_SENTINEL','HIDDEN_SENTINEL','EXECUTION_SENTINEL','DOCUMENT_SCRIPT_MUST_NOT_RUN']) assert.ok(!d.content.replaceAll('\\_', '_').includes(s), s);
  assert.ok(d.wordCount > 80);
  assert.equal(d.evidence.runtimeVersion, '0.19.4');
  assert.equal(d.evidence.useAsync, false);
  assert.equal(d.evidence.networkCalls, 0);
  assert.match(d.evidence.inputSha256, /^[0-9a-f]{64}$/);
  writeFileSync(join(out, 'article.md'), d.content);
});
check('empty-is-not-success', () => {
  const r = run('empty', 'empty.html', 'https://example.com/empty');
  assert.equal(r.status, 1);
  assert.equal(r.stdout.trim(), '');
  assert.match(r.stderr, /empty/i);
});
check('challenge-is-not-an-article', () => {
  const r = run('blocked', 'blocked.html', 'https://example.com/blocked');
  assert.equal(r.status, 1);
  assert.equal(r.stdout.trim(), '');
  assert.match(r.stderr, /blocked|challenge/i);
});
check('reject-credentialed-or-nonhttps-source', () => {
  for (const url of ['file:///local/article', 'https://user:secret@example.com/article', 'http://example.com/article']) {
    const r = run('invalid-source-' + url.split(':')[0], 'article.html', url);
    assert.equal(r.status, 1);
    assert.equal(r.stdout.trim(), '');
    assert.match(r.stderr, /source URL/i);
  }
});
check('upstream-error-is-not-success', () => {
  const r = run('colon-id', 'colon-id.html', 'https://example.com/stream');
  assert.equal(r.status, 1);
  assert.equal(r.stdout.trim(), '');
  assert.match(r.stderr, /diagnostic|processing document/i);
});
writeFileSync(join(out, 'results.json'), JSON.stringify(rows, null, 2));
console.log(JSON.stringify(rows, null, 2));
process.exitCode = rows.every(r => r.status === 'pass') ? 0 : 1;
