#!/usr/bin/env node
/**
 * Fleet delivery verification for bounty #5 (issue #5).
 * Codifies handoff checks: test coverage, CI wiring, importable workflow.
 */
import { execSync } from 'node:child_process';
import { readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { isGitHubError, collectRecords } from './lib/github-collect.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const repoRoot = join(root, '..', '..');

const tests = [];
function test(name, fn) {
  tests.push({ name, fn });
}

function countAsserts(path) {
  return (readFileSync(path, 'utf8').match(/\bassert\(/g) || []).length;
}

function countTests(path) {
  const text = readFileSync(path, 'utf8');
  const named = (text.match(/^test\(/gm) || []).length;
  if (named > 0) return named;
  return countAsserts(path);
}

test('ci workflow avoids privileged fork checkout pattern', () => {
  const ciWorkflow = readFileSync(
    join(repoRoot, '.github', 'workflows', 'test-n8n-weekly-summary.yml'),
    'utf8',
  );
  if (ciWorkflow.includes('pull_request_target')) {
    throw new Error('test-n8n-weekly-summary.yml must not use pull_request_target with test checkout');
  }
  if (/pull_request_target:[\s\S]*uses:\s*actions\/checkout/.test(ciWorkflow)) {
    throw new Error('privileged trigger must not checkout fork code in CI workflow');
  }
  for (const path of ['package.json', 'Makefile']) {
    if (!ciWorkflow.includes(`- '${path}'`)) {
      throw new Error(`CI workflow paths must include repo-root ${path} for fleet test wiring`);
    }
  }
});

test('github collect helper covers pagination and error rejection', () => {
  const helperPath = join(__dirname, 'lib', 'github-collect.mjs');
  if (!statSync(helperPath).isFile()) {
    throw new Error('tests/lib/github-collect.mjs must exist for shared collection logic');
  }
  if (!isGitHubError({ message: 'bad', documentation_url: 'https://docs.github.com' })) {
    throw new Error('isGitHubError must detect GitHub API error payloads');
  }
  const kept = collectRecords([{ json: { records: [
    { sha: 'abc', commit: { message: 'x' } },
    { message: 'Not Found', documentation_url: 'https://docs.github.com' },
  ] } }]);
  if (kept.length !== 1 || kept[0].sha !== 'abc') {
    throw new Error('collectRecords must drop GitHub error objects from activity counts');
  }
});

test('regression suite has minimum coverage', () => {
  const validate = countAsserts(join(__dirname, 'validate-workflow.mjs'));
  const collect = countAsserts(join(__dirname, 'collect-github-data.test.mjs'));
  const peerReview = countAsserts(join(__dirname, 'peer-review-acceptance.test.mjs'));
  const testScripts = countAsserts(join(__dirname, 'test-scripts-acceptance.test.mjs'));
  if (validate < 30) throw new Error(`validate-workflow.mjs has ${validate} asserts (need >= 30)`);
  if (collect < 10) throw new Error(`collect-github-data.test.mjs has ${collect} asserts (need >= 10)`);
  if (peerReview < 18) throw new Error(`peer-review-acceptance.test.mjs has ${peerReview} asserts (need >= 18)`);
  if (testScripts < 20) throw new Error(`test-scripts-acceptance.test.mjs has ${testScripts} asserts (need >= 20)`);
});

test('ci script exists and declares delivery checks', () => {
  const ciScript = readFileSync(join(__dirname, 'run-ci-checks.mjs'), 'utf8');
  if (!ciScript.includes('test-scripts-acceptance.test.mjs')) {
    throw new Error('run-ci-checks.mjs must run test-scripts-acceptance.test.mjs');
  }
  if (!ciScript.includes('delivery-verification.test.mjs')) {
    throw new Error('run-ci-checks.mjs must run delivery-verification.test.mjs');
  }
  if (!ciScript.includes('delivery verification tests')) {
    throw new Error('run-ci-checks.mjs must print delivery verification summary');
  }
  if (!ciScript.includes('peer review acceptance tests passed')) {
    throw new Error('run-ci-checks.mjs must print peer review acceptance summary');
  }
  if (!ciScript.includes('totalTests = validateTests + collectTests + testScriptsTests + deliveryTests + peerReviewTests')) {
    throw new Error('run-ci-checks.mjs must sum discovered suite counts before final summary');
  }
  if (!ciScript.includes('OK: ${totalTests} tests passed')) {
    throw new Error('run-ci-checks.mjs must print total test count for fleet delivery gates');
  }
});

test('ci runner total matches discovered test counts', () => {
  const validate = countTests(join(__dirname, 'validate-workflow.mjs'));
  const collect = countTests(join(__dirname, 'collect-github-data.test.mjs'));
  const testScripts = countTests(join(__dirname, 'test-scripts-acceptance.test.mjs'));
  const delivery = countTests(join(__dirname, 'delivery-verification.test.mjs'));
  const peerReview = countTests(join(__dirname, 'peer-review-acceptance.test.mjs'));
  const expectedTotal = validate + collect + testScripts + delivery + peerReview;
  if (expectedTotal < 120) {
    throw new Error(`discovered ${expectedTotal} regression tests (need >= 120)`);
  }
  const proofPath = join(root, 'PROOF.md');
  if (!statSync(proofPath).isFile()) {
    throw new Error('PROOF.md must document npm test evidence for fleet handoff');
  }
  const proof = readFileSync(proofPath, 'utf8');
  if (!proof.includes(`OK: ${expectedTotal} tests passed`)) {
    throw new Error(`PROOF.md must include total test summary (${expectedTotal} tests)`);
  }
});

test('workflow JSON is importable with required nodes', () => {
  const workflow = JSON.parse(readFileSync(join(root, 'weekly-dev-summary.json'), 'utf8'));
  if (!Array.isArray(workflow.nodes) || workflow.nodes.length < 13) {
    throw new Error(`workflow has ${workflow.nodes?.length ?? 0} nodes (need >= 13)`);
  }
  const names = workflow.nodes.map((n) => n.name);
  for (const required of [
    'Friday 5pm Weekly Trigger',
    'Load Config',
    'Fetch Commits',
    'Fetch Closed Issues',
    'Fetch Merged PRs',
    'Claude API',
    'Route Delivery',
  ]) {
    if (!names.includes(required)) throw new Error(`missing node: ${required}`);
  }
});

test('n8n execution screenshot asset present', () => {
  const screenshot = statSync(join(root, 'assets', 'n8n-execution-screenshot.png'));
  if (!screenshot.isFile() || screenshot.size <= 1024) {
    throw new Error('n8n execution screenshot missing or too small');
  }
});

test('repo root exposes npm test entry point', () => {
  const pkg = JSON.parse(readFileSync(join(repoRoot, 'package.json'), 'utf8'));
  if (!pkg.scripts?.test?.includes('n8n-weekly-dev-summary')) {
    throw new Error('repo root package.json test script must delegate to n8n workflow CI');
  }
  if (!pkg.scripts?.test?.includes('test:ci')) {
    throw new Error('repo root package.json test script must run test:ci');
  }
});

test('peer-review suite is silent on success for CI summary ordering', () => {
  const peerReview = readFileSync(join(__dirname, 'peer-review-acceptance.test.mjs'), 'utf8');
  if (/console\.log\(['"]OK: peer review acceptance tests passed['"]\)/.test(peerReview)) {
    throw new Error('peer-review-acceptance.test.mjs must not print CI summary (run-ci-checks owns that line)');
  }
});

test('repo root Makefile exposes test and ci-validate', () => {
  const makefile = readFileSync(join(repoRoot, 'Makefile'), 'utf8');
  if (!/^test:/m.test(makefile) || !/^ci-validate:/m.test(makefile)) {
    throw new Error('repo root Makefile must expose test and ci-validate targets');
  }
});

test('tracked files belong to bounty #5 n8n workflow only', () => {
  const tracked = execSync('git ls-files', { cwd: repoRoot, encoding: 'utf8' });
  for (const stray of ['hooks/block-destructive-commands', 'agents/claude-review']) {
    if (tracked.includes(stray)) {
      throw new Error(`wrong bounty files must not be committed on n8n workflow branch (${stray})`);
    }
  }
  if (!tracked.includes('workflows/n8n-weekly-dev-summary/weekly-dev-summary.json')) {
    throw new Error('n8n workflow JSON must be tracked for bounty #5 delivery');
  }
});

test('repo root npm test entry point runs green', () => {
  if (process.env.N8N_CI_INNER_RUN) return;
  const output = execSync('npm test', {
    cwd: repoRoot,
    encoding: 'utf8',
    env: { ...process.env, N8N_CI_INNER_RUN: '1' },
  });
  if (!output.includes('OK: all CI validation checks passed')) {
    throw new Error('repo root npm test must pass full CI runner');
  }
  if (!output.includes('13 nodes, all acceptance checks passed')) {
    throw new Error('repo root npm test must validate n8n weekly-dev-summary workflow');
  }
  if (/destructive|pretooluse/i.test(output)) {
    throw new Error('repo root npm test must not run unrelated bounty suites');
  }
});

const failures = [];
for (const { name, fn } of tests) {
  try {
    fn();
  } catch (error) {
    failures.push(`${name}: ${error.message}`);
  }
}

if (failures.length) {
  console.error('FAILED delivery verification:\n- ' + failures.join('\n- '));
  process.exit(1);
}
