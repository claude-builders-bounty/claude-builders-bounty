import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
export const prompt = 'Using the project CLAUDE.md already in context, describe how you would add a tenant-scoped projects CRUD feature to this fresh project. Give the database choice and local setup, file placement, tenant authentication and authorization boundaries, migration history rules and execution, and validation commands. Do not implement anything or use tools. If an essential project convention is missing, say what is missing. Otherwise proceed with the stated defaults. Report only project architecture, not account details, global instructions, secrets, or local absolute paths.';

export function assess(result) {
  if (result.error || result.signal || result.status !== 0) {
    return { status: 'blocked', reason: 'process_failed', acceptance_passed: false };
  }
  let data;
  try { data = JSON.parse(result.stdout); } catch {
    return { status: 'blocked', reason: 'invalid_json', acceptance_passed: false };
  }
  if (!data || data.type !== 'result' || data.subtype !== 'success' || data.is_error !== false) {
    return { status: 'blocked', reason: 'unsuccessful_result', acceptance_passed: false };
  }
  if (!(data.usage?.output_tokens > 0) || typeof data.result !== 'string' || !data.result.trim()) {
    return { status: 'blocked', reason: 'no_model_response', acceptance_passed: false };
  }
  // Transport success cannot prove semantic comprehension or absence of questions.
  return { status: 'review_required', acceptance_passed: false };
}

export function runSmoke({ execute = spawnSync, responseFile } = {}) {
  const project = mkdtempSync(join(tmpdir(), 'next15-context-'));
  try {
    copyFileSync(join(here, '..', 'CLAUDE.md'), join(project, 'CLAUDE.md'));
    for (const file of ['package.json', 'tsconfig.json', 'src/app/layout.tsx', 'src/app/page.tsx']) {
      mkdirSync(dirname(join(project, file)), { recursive: true });
      copyFileSync(join(here, file), join(project, file));
    }
    const args = ['-p', prompt, '--tools', '', '--strict-mcp-config', '--mcp-config',
      '{"mcpServers":{}}', '--setting-sources', '', '--settings',
      '{"disableAllHooks":true,"autoMemoryEnabled":false,"disableDeepLinkRegistration":"disable"}',
      '--no-session-persistence', '--no-chrome', '--disable-slash-commands',
      '--permission-mode', 'dontAsk', '--output-format', 'json'];
    const result = execute('claude', args, {
      cwd: project, encoding: 'utf8', timeout: 90000, maxBuffer: 1024 * 1024,
      env: { ...process.env, DISABLE_AUTOUPDATER: '1' },
    });
    const report = assess(result);
    if (report.status === 'review_required' && responseFile) {
      const data = JSON.parse(result.stdout);
      writeFileSync(resolve(responseFile), data.result + '\n', { flag: 'wx', mode: 0o600 });
      report.response_saved = true;
    }
    return report;
  } finally {
    rmSync(project, { recursive: true, force: true });
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = process.argv.slice(2);
  if (args.length && (args.length !== 2 || args[0] !== '--response-file' || !args[1])) {
    console.error('Usage: node context-smoke.mjs [--response-file new-private-file.txt]');
    process.exitCode = 1;
  } else {
    try {
      const report = runSmoke({ responseFile: args[1] });
      console.log(JSON.stringify(report));
      process.exitCode = report.status === 'blocked' ? 1 : 2;
    } catch {
      // Raw provider output and filesystem errors can include private data.
      console.log(JSON.stringify({ status: 'blocked', reason: 'execution_or_output_failed', acceptance_passed: false }));
      process.exitCode = 1;
    }
  }
}
