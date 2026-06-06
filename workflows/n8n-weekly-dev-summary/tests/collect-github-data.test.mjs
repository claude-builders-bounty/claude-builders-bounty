#!/usr/bin/env node
/**
 * Regression test for GitHub response collection (n8n splits arrays into items).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const workflow = JSON.parse(
  readFileSync(join(__dirname, '..', 'weekly-dev-summary.json'), 'utf8'),
);

const buildPrompt = workflow.nodes.find((n) => n.name === 'Build Claude Prompt');
const code = buildPrompt?.parameters?.jsCode || '';

const failures = [];
function assert(condition, message) {
  if (!condition) failures.push(message);
}

assert(
  buildPrompt?.parameters?.mode === 'runOnceForAllItems',
  'Build Claude Prompt runs once after merge (avoids duplicate Claude calls)',
);
assert(code.includes('collectRecords'), 'uses collectRecords helper for GitHub nodes');
assert(code.includes(".all()"), 'reads all n8n items from GitHub HTTP nodes');
assert(code.includes('Array.isArray(first)'), 'handles wrapped array responses');

if (failures.length) {
  console.error('FAILED:\n- ' + failures.join('\n- '));
  process.exit(1);
}

console.log('OK: GitHub data collection handles n8n item splitting.');
