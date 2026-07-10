#!/usr/bin/env node

import {readdirSync, readFileSync, statSync} from 'node:fs';
import {join} from 'node:path';

const roots = ['hooks', 'scripts', 'test'];
const files = [];

function walk(path) {
  for (const entry of readdirSync(path)) {
    const fullPath = join(path, entry);
    if (statSync(fullPath).isDirectory()) {
      walk(fullPath);
    } else if (fullPath.endsWith('.js')) {
      files.push(fullPath);
    }
  }
}

for (const root of roots) {
  walk(root);
}

const failures = [];
for (const file of files) {
  const content = readFileSync(file, 'utf8');
  if (content.includes('\t')) {
    failures.push(`${file}: tabs are not used in this repo`);
  }
  if (!content.endsWith('\n')) {
    failures.push(`${file}: missing trailing newline`);
  }
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}

console.log(`Checked ${files.length} JavaScript files.`);
