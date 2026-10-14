import Database from 'better-sqlite3';

if (process.env.NODE_ENV === 'production') {
  console.error('db:seed refuses to run with NODE_ENV=production');
  process.exit(1);
}

const dbPath = process.env.DATABASE_PATH ?? './data/app.db';
const db = new Database(dbPath);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

const existing = db.prepare('SELECT COUNT(*) AS n FROM items').get().n;
if (existing > 0) {
  console.log(`seed: ${existing} rows already present, nothing to do`);
} else {
  const insert = db.prepare('INSERT INTO items (title, created_at) VALUES (?, ?)');
  const rows = ['First item', 'Second item', 'Third item'];
  db.transaction(() => rows.forEach((title, i) => insert.run(title, Date.now() + i)))();
  console.log(`seed: inserted ${rows.length} rows`);
}
db.close();
