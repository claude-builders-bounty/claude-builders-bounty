#!/usr/bin/env node
/**
 * Static acceptance checks for all workflow test scripts.
 * Codifies peer-review requirements: coverage, structure, secret hygiene.
 */
import { readFileSync, statSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

const requiredScripts = [
  { file: 'validate-workflow.mjs', mustInclude: ['weekly-dev-summary.json', 'assert('] },
  { file: 'collect-github-data.test.mjs', mustInclude: ['collectRecords', 'Merge GitHub Results'] },
  { file: 'delivery-verification.test.mjs', mustInclude: ['Fleet delivery verification', 'test('] },
  { file: 'peer-review-acceptance.test.mjs', mustInclude: ['Peer-review acceptance', 'assert('] },
  { file: 'run-ci-checks.mjs', mustInclude: ['validate-workflow.mjs', 'delivery-verification.test.mjs'] },
  { file: 'github-fetch.test.mjs', mustInclude: ['GITHUB_TOKEN', 'api.github.com'] },
  { file: 'capture-execution-screenshot.mjs', mustInclude: ['playwright', 'n8n-execution-screenshot.png'] },
  { file: 'run-n8n-e2e.mjs', mustInclude: ['mockPort', 'weekly-dev-summary.e2e.json'] },
];

const forbiddenSecrets = ['sk-ant-', 'ghp_', 'gho_', 'discord.com/api/webhooks/'];
const secretScanExempt = new Set(['validate-workflow.mjs']);

for (const { file, mustInclude } of requiredScripts) {
  const path = join(__dirname, file);
  assert(statSync(path).isFile(), `${file} exists under tests/`);
  const text = readFileSync(path, 'utf8');
  assert(text.startsWith('#!/usr/bin/env node'), `${file} has node shebang`);
  for (const snippet of mustInclude) {
    assert(text.includes(snippet), `${file} covers ${snippet}`);
  }
  if (!secretScanExempt.has(file)) {
    for (const secret of forbiddenSecrets) {
      assert(!text.includes(secret), `${file} does not embed ${secret}`);
    }
  }
}

const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
assert(pkg.scripts?.test?.includes('validate-workflow.mjs'), 'npm test runs validate-workflow.mjs');
assert(pkg.scripts?.test?.includes('collect-github-data.test.mjs'), 'npm test runs collect-github-data.test.mjs');
assert(pkg.scripts?.test?.includes('delivery-verification.test.mjs'), 'npm test runs delivery-verification.test.mjs');
assert(pkg.scripts?.test?.includes('peer-review-acceptance.test.mjs'), 'npm test runs peer-review-acceptance.test.mjs');
assert(pkg.scripts?.['test:ci']?.includes('run-ci-checks.mjs'), 'npm run test:ci runs unified CI runner');
assert(pkg.scripts?.['test:github']?.includes('github-fetch.test.mjs'), 'npm run test:github runs GitHub API test');
assert(pkg.scripts?.['test:e2e']?.includes('run-n8n-e2e.mjs'), 'npm run test:e2e runs n8n e2e runner');

const expectedDirs = ['tests', 'assets'];
for (const dir of expectedDirs) {
  assert(statSync(join(root, dir)).isDirectory(), `${dir}/ directory present`);
}
assert(statSync(join(root, 'weekly-dev-summary.json')).isFile(), 'weekly-dev-summary.json at workflow root');
assert(statSync(join(root, 'README.md')).isFile(), 'README.md at workflow root');

const githubFetch = readFileSync(join(__dirname, 'github-fetch.test.mjs'), 'utf8');
assert(
  githubFetch.includes('process.env.GITHUB_TOKEN') && githubFetch.includes('gh auth token'),
  'github-fetch.test.mjs resolves token from env or gh CLI (no hardcoded credentials)',
);

const capture = readFileSync(join(__dirname, 'capture-execution-screenshot.mjs'), 'utf8');
assert(
  capture.includes('localhost:5678') && capture.includes('screenshot'),
  'capture-execution-screenshot.mjs targets local n8n and writes screenshot asset',
);
assert(
  readFileSync(join(root, 'README.md'), 'utf8').includes('test-scripts-acceptance') ||
    readFileSync(join(root, 'README.md'), 'utf8').includes('npm test'),
  'README documents how to run validation tests',
);

if (failures.length) {
  console.error('FAILED test-scripts acceptance:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log(`OK: ${requiredScripts.length} test scripts validated.`);
