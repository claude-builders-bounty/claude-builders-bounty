import {readFileSync} from 'node:fs';
import {join} from 'node:path';

const file = readFileSync(join(process.cwd(), 'CLAUDE.md'), 'utf8');

const requiredSnippets = [
  '# CLAUDE.md',
  'Next.js 15 App Router',
  'SQLite',
  'better-sqlite3',
  'Turso',
  'Folder Structure',
  'Naming Conventions',
  'Database And Migration Rules',
  'SQL Rules',
  'Component Patterns',
  'Commands',
  'What We Do Not Do',
  'Why',
  'migration',
  'server component',
  'client component',
];

const missing = requiredSnippets.filter((snippet) => !file.includes(snippet));

if (missing.length > 0) {
  console.error(`CLAUDE.md is missing required guidance: ${missing.join(', ')}`);
  process.exit(1);
}

const sectionCount = file.match(/^## /gm)?.length ?? 0;
if (sectionCount < 8) {
  console.error(`CLAUDE.md should be opinionated and structured; found only ${sectionCount} top-level sections.`);
  process.exit(1);
}

console.log('CLAUDE.md validation passed');
