import test, { after } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

// One database per process: `node --test` runs each file in its own child process.
const dbPath = `./data/test-${process.pid}.db`;
const cleanup = () => ['', '-wal', '-shm'].forEach((suffix) => fs.rmSync(`${dbPath}${suffix}`, { force: true }));

function run(script, env = {}) {
  return execFileSync('node', [script], { encoding: 'utf8', env: { ...process.env, DATABASE_PATH: dbPath, ...env } });
}

function migrate() { return run('scripts/migrate.mjs'); }
function seed() { return run('scripts/seed.mjs'); }
function inspect() { return JSON.parse(run('scripts/inspect.mjs')); }

test('migrations apply, are ordered and are idempotent', () => {
  cleanup();
  assert.match(migrate(), /2 applied/);
  assert.match(migrate(), /0 applied/);

  const snapshot = inspect();
  assert.ok(snapshot.tables.includes('items'), 'items table should exist');
  assert.ok(snapshot.tables.includes('_migrations'), '_migrations table should exist');
  assert.deepEqual(snapshot.itemColumns, ['id', 'title', 'created_at', 'archived_at']);
  assert.ok(snapshot.itemIndexes.includes('items_created_at_idx'), 'created_at index should exist');
});

test('seed inserts rows once and refuses in production', () => {
  cleanup();
  migrate();
  assert.match(seed(), /inserted 3 rows/);
  assert.match(seed(), /already present/);
  assert.throws(() => run('scripts/seed.mjs', { NODE_ENV: 'production' }));

  const snapshot = inspect();
  assert.equal(snapshot.itemCount, 3);
  assert.equal(typeof snapshot.firstItem.created_at, 'number');
  assert.equal(snapshot.firstItem.archived_at, null, 'archived_at should default to NULL');
});

test('timestamps are epoch milliseconds, not text or seconds', () => {
  cleanup();
  migrate();
  seed();
  const { created_at: ts } = inspect().firstItem;
  assert.ok(ts > Date.now() - 60_000, 'should be epoch ms (seconds would be ~1000x smaller)');
  assert.ok(ts < Date.now() + 60_000, 'should not be in the future');
});

test('WAL is enabled and the documented pragmas live in lib/db.ts', () => {
  cleanup();
  migrate();
  assert.equal(inspect().journalMode, 'wal', 'journal_mode=WAL should persist in the file');

  const dbSource = fs.readFileSync(path.join(process.cwd(), 'lib', 'db.ts'), 'utf8');
  assert.match(dbSource, /pragma\('journal_mode = WAL'\)/, 'lib/db.ts must enable WAL');
  assert.match(dbSource, /pragma\('foreign_keys = ON'\)/, 'lib/db.ts must enable foreign keys');
});

after(() => cleanup());
