#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const target = process.argv[2] || 'generated-changelog-smoke.md';
const changelog = readFileSync(target, 'utf8');

const required = [
  '# Changelog',
  'Generated for ',
  '## ',
];

const problems = [];

for (const token of required) {
  if (!changelog.includes(token)) {
    problems.push('Missing required changelog content: ' + token);
  }
}

if (!/### (Features|Fixes|Documentation|Tests|Maintenance|Other)/.test(changelog) &&
    !/- No commits found for this range\./.test(changelog)) {
  problems.push('Missing a recognized category section or no-commits fallback.');
}

if (!/\([0-9a-f]{7,}, \d{4}-\d{2}-\d{2}, .+\)/.test(changelog) &&
    !/- No commits found for this range\./.test(changelog)) {
  problems.push('Commit entries should include short hash, date, and author metadata.');
}

if (problems.length > 0) {
  console.error('Changelog verification failed for ' + target + ':');
  for (const problem of problems) {
    console.error('- ' + problem);
  }
  process.exit(1);
}

console.log('Changelog verification passed for ' + target + '.');
