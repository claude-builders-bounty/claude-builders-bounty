import fs from 'node:fs';
import { execFileSync } from 'node:child_process';

const dbPath = process.env.DATABASE_PATH ?? './data/app.db';
for (const suffix of ['', '-wal', '-shm']) {
  fs.rmSync(`${dbPath}${suffix}`, { force: true });
}
console.log(`reset: removed ${dbPath}`);
execFileSync('node', ['scripts/migrate.mjs'], { stdio: 'inherit' });
execFileSync('node', ['scripts/seed.mjs'], { stdio: 'inherit' });
