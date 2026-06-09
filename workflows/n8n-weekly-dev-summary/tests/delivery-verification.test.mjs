#!/usr/bin/env node
/**
 * Fleet delivery verification for bounty #5 (issue #5).
 * Codifies handoff checks: test coverage, CI wiring, importable workflow.
 */
import { readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

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

test('regression suite has minimum coverage', () => {
  const validate = countAsserts(join(__dirname, 'validate-workflow.mjs'));
  const collect = countAsserts(join(__dirname, 'collect-github-data.test.mjs'));
  const peerReview = countAsserts(join(__dirname, 'peer-review-acceptance.test.mjs'));
  if (validate < 30) throw new Error(`validate-workflow.mjs has ${validate} asserts (need >= 30)`);
  if (collect < 10) throw new Error(`collect-github-data.test.mjs has ${collect} asserts (need >= 10)`);
  if (peerReview < 15) throw new Error(`peer-review-acceptance.test.mjs has ${peerReview} asserts (need >= 15)`);
});

test('ci script exists and declares delivery checks', () => {
  const ciScript = readFileSync(join(__dirname, 'run-ci-checks.mjs'), 'utf8');
  if (!ciScript.includes('delivery-verification.test.mjs')) {
    throw new Error('run-ci-checks.mjs must run delivery-verification.test.mjs');
  }
  if (!ciScript.includes('delivery verification tests')) {
    throw new Error('run-ci-checks.mjs must print delivery verification summary');
  }
  if (!ciScript.includes('peer review acceptance tests passed')) {
    throw new Error('run-ci-checks.mjs must print peer review acceptance summary');
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
});

test('repo root Makefile exposes test and ci-validate', () => {
  const makefile = readFileSync(join(repoRoot, 'Makefile'), 'utf8');
  if (!/^test:/m.test(makefile) || !/^ci-validate:/m.test(makefile)) {
    throw new Error('repo root Makefile must expose test and ci-validate targets');
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
