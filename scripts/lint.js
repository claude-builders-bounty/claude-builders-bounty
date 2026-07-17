import { readFileSync } from 'node:fs';
import { globSync } from 'node:fs';

const files = globSync('{bin,lib,test,scripts}/**/*.js');
const failures = [];

for (const file of files) {
  const source = readFileSync(file, 'utf8');
  if (/\t/.test(source)) failures.push(`${file}: contains tabs`);
  const lines = source.split('\n');
  if (lines.some((line) => /[ \t]+$/.test(line))) failures.push(`${file}: contains trailing whitespace`);
  if (!source.endsWith('\n')) failures.push(`${file}: missing trailing newline`);
}

if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}

console.log(`lint passed for ${files.length} file(s)`);
