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

process.env.N8N_CI_INNER_RUN = '1';

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

function countTests(path) {
  const text = readFileSync(path, 'utf8');
  const named = (text.match(/^test\(/gm) || []).length;
  if (named > 0) return named;
  return (text.match(/\bassert\(/g) || []).length;
}

const validateTests = countTests(join(__dirname, 'validate-workflow.mjs'));
run('node tests/validate-workflow.mjs');

const collectTests = countTests(join(__dirname, 'collect-github-data.test.mjs'));
run('node tests/collect-github-data.test.mjs');

const unitTests = countTests(join(__dirname, 'github-collect-unit.test.mjs'));
run('node tests/github-collect-unit.test.mjs');

const integrationTests = countTests(join(__dirname, 'workflow-integration.test.mjs'));
run('node tests/workflow-integration.test.mjs');

const claudeSummaryTests = countTests(join(__dirname, 'claude-summary.test.mjs'));
run('node tests/claude-summary.test.mjs');

const deliveryChannelTests = countTests(join(__dirname, 'delivery-channels.test.mjs'));
run('node tests/delivery-channels.test.mjs');

const testScriptsTests = countTests(join(__dirname, 'test-scripts-acceptance.test.mjs'));
run('node tests/test-scripts-acceptance.test.mjs');

const deliveryTests = countTests(join(__dirname, 'delivery-verification.test.mjs'));
run('node tests/delivery-verification.test.mjs');
console.log(`Ran ${deliveryTests} delivery verification tests — OK`);

const peerReviewTests = countTests(join(__dirname, 'peer-review-acceptance.test.mjs'));
run('node tests/peer-review-acceptance.test.mjs');
console.log(`Ran ${peerReviewTests} tests — OK`);
console.log('OK: peer review acceptance tests passed');

const totalTests = validateTests + collectTests + unitTests + integrationTests + claudeSummaryTests + deliveryChannelTests + testScriptsTests + deliveryTests + peerReviewTests;
console.log(`OK: ${totalTests} tests passed`);

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
