import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';

try {
  const [input, source] = process.argv.slice(2);
  if (!input || !source || process.argv.length !== 4) throw new Error('Usage: node extract.mjs LOCAL_HTML HTTPS_SOURCE_URL');
  let sourceUrl;
  try { sourceUrl = new URL(source); } catch { throw new Error('Invalid source URL'); }
  if (sourceUrl.protocol !== 'https:' || sourceUrl.username || sourceUrl.password || /[\s\\]/.test(source)) throw new Error('Source URL must be credential-free HTTPS');
  const home = process.env.HERMES_HOME || join(homedir(), '.hermes');
  const runtime = join(home, 'tools', 'clean-web-content');
  const requireRuntime = createRequire(join(runtime, 'package.json'));
  const version = JSON.parse(readFileSync(join(runtime, 'node_modules/defuddle/package.json'), 'utf8')).version;
  const domVersion = JSON.parse(readFileSync(join(runtime, 'node_modules/linkedom/package.json'), 'utf8')).version;
  if (version !== '0.19.4' || domVersion !== '0.18.12') throw new Error('Runtime pin mismatch; review before upgrading');
  let networkCalls = 0;
  const deniedFetch = async () => { networkCalls++; throw new Error('Network disabled during local extraction'); };
  globalThis.fetch = deniedFetch;
  const { parseHTML } = requireRuntime('linkedom');
  const { Defuddle } = await import(pathToFileURL(join(runtime, 'node_modules/defuddle/dist/node.js')).href);
  const bytes = readFileSync(input);
  const { document } = parseHTML(bytes.toString('utf8'));
  const title = document.querySelector('title')?.textContent?.trim() || '';
  if (/^(just a moment[.!…]*|access denied|attention required.*|sign in|log in|login|verify you are human)$/i.test(title)) throw new Error('Blocked or login challenge, not article content');
  const diagnostics = [];
  const originalWarn = console.warn;
  const originalError = console.error;
  const collectDiagnostic = (...parts) => diagnostics.push(parts.map(x => String(x)).join(' ').slice(0, 2000));
  console.warn = collectDiagnostic;
  console.error = collectDiagnostic;
  let result;
  try {
    result = await Defuddle(document, source, { markdown: true, useAsync: false, includeReplies: false, fetch: deniedFetch });
  } finally {
    console.warn = originalWarn;
    console.error = originalError;
  }
  if (diagnostics.length) throw new Error('Upstream diagnostics require manual review: ' + diagnostics.join('; '));
  if (networkCalls) throw new Error('Unexpected network attempt during extraction');
  if (!result.content || !result.content.trim() || !result.wordCount) throw new Error('Empty extraction: no article content found');
  result.evidence = { sourceUrl: source, inputSha256: createHash('sha256').update(bytes).digest('hex'), runtime: 'defuddle', runtimeVersion: version, domVersion, useAsync: false, includeReplies: false, networkCalls };
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(JSON.stringify({ status: 'failed', error: error.message }));
  process.exitCode = 1;
}
