#!/usr/bin/env node
/**
 * Mirrors .github/workflows/test-n8n-weekly-summary.yml validation steps locally.
 */
import { execSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const repoRoot = join(root, '..', '..');

const cursorAgent = ['cursoragent', '@', 'cursor', '.', 'com'].join('');
const madeWith = ['Made with', ' ', 'Cursor'].join('');
const coAuthored = ['Co-authored-by:', ' ', 'Cursor'].join('');
const madeWithTrailer = ['Made-with:', ' ', 'Cursor'].join('');
const forbiddenSource = new RegExp(
  [cursorAgent, madeWith, coAuthored].map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
);
const forbiddenCommit = new RegExp(
  `^(${coAuthored.replace(/ /g, ' ')}|${madeWithTrailer.replace(/ /g, ' ')})|${cursorAgent.replace(/\./g, '\\.')}|^${madeWith.replace(/ /g, ' ')}`,
  'm',
);

function run(cmd, cwd = root) {
  execSync(cmd, { cwd, stdio: 'inherit' });
}

run('npm test');
run('jq empty weekly-dev-summary.json');

const sources = execSync('git ls-files', { cwd: root, encoding: 'utf8' })
  .trim()
  .split('\n')
  .filter((rel) => rel && !rel.startsWith('tests/'));

for (const rel of sources) {
  const text = readFileSync(join(root, rel), 'utf8');
  if (forbiddenSource.test(text)) {
    console.error(`Forbidden agent attribution in ${rel}`);
    process.exit(1);
  }
}

const headMessage = execSync('git log -1 --format=%B', { cwd: repoRoot, encoding: 'utf8' });
if (forbiddenCommit.test(headMessage)) {
  console.error('Forbidden agent attribution in HEAD commit message');
  process.exit(1);
}

run('git diff --check', repoRoot);
console.log('OK: all CI validation checks passed');
