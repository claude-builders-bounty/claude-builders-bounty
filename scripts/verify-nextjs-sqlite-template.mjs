#!/usr/bin/env node
import { readFileSync } from 'node:fs';

const template = readFileSync('templates/nextjs-sqlite-saas/CLAUDE.md', 'utf8');

const requiredSections = [
  '## Project Shape',
  '## Commands',
  '## Naming',
  '## Data And SQLite',
  '## Migrations',
  '## Auth And Sessions',
  '## Billing',
  '## Testing',
  '## Patterns To Follow',
  '## Patterns To Avoid',
  '## Before Finishing A Change',
];

const requiredPhrases = [
  'Next.js App Router',
  'SQLite',
  'prepared statements',
  'transactions',
  'tenant-owned query',
  'workspace/account ownership checks',
  'Migrations are append-only after merge',
  'Do not run production migrations from build scripts',
  'Do not trust client-sent user IDs',
  'webhook signatures',
  'idempotent',
  'Running worker infrastructure during next build',
];

const forbiddenGenericMarkers = [
  '[PROJECT_NAME]',
  '[TODO]',
  'your project here',
  'lorem ipsum',
];

const problems = [];

for (const section of requiredSections) {
  if (!template.includes(section)) {
    problems.push('Missing required section: ' + section);
  }
}

for (const phrase of requiredPhrases) {
  if (!template.includes(phrase)) {
    problems.push('Missing required guidance: ' + phrase);
  }
}

for (const marker of forbiddenGenericMarkers) {
  if (template.toLowerCase().includes(marker.toLowerCase())) {
    problems.push('Template still contains generic placeholder: ' + marker);
  }
}

if (!/## Patterns To Avoid[\s\S]*because|## Patterns To Avoid[\s\S]*why|Do not/.test(template)) {
  problems.push('Anti-pattern section must include concrete reasons or clear prohibitions.');
}

if (problems.length > 0) {
  console.error('Next.js SQLite CLAUDE.md verification failed:');
  for (const problem of problems) {
    console.error('- ' + problem);
  }
  process.exit(1);
}

console.log('Next.js SQLite CLAUDE.md verification passed.');
