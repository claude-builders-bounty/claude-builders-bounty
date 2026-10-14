import Database from 'better-sqlite3';

/**
 * Prints a JSON snapshot of the database. Used by the test suite so that the test
 * process never loads the native module (better-sqlite3 asserts during teardown
 * when a handle is still open, which makes flaky suites).
 */
const dbPath = process.env.DATABASE_PATH ?? './data/app.db';
const db = new Database(dbPath, { readonly: true });
try {
  const items = db.prepare('SELECT id, title, created_at, archived_at FROM items ORDER BY id').all();
  console.log(JSON.stringify({
    tables: db.prepare("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").all().map((r) => r.name),
    itemColumns: db.prepare('PRAGMA table_info(items)').all().map((c) => c.name),
    itemIndexes: db
      .prepare("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'items' ORDER BY name")
      .all()
      .map((r) => r.name),
    itemCount: items.length,
    firstItem: items[0] ?? null,
    journalMode: String(db.pragma('journal_mode', { simple: true })).toLowerCase(),
  }));
} finally {
  db.close();
}
