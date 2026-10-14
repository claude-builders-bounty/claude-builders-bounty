import fs from 'node:fs';
import path from 'node:path';
import Database from 'better-sqlite3';

const dbPath = process.env.DATABASE_PATH ?? './data/app.db';
fs.mkdirSync(path.dirname(dbPath), { recursive: true });

const db = new Database(dbPath);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
db.exec('CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at INTEGER NOT NULL)');

const dir = path.join(process.cwd(), 'db', 'migrations');
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort();
const applied = new Set(db.prepare('SELECT name FROM _migrations').all().map((row) => row.name));

const apply = db.transaction((file) => {
  db.exec(fs.readFileSync(path.join(dir, file), 'utf8'));
  db.prepare('INSERT INTO _migrations (name, applied_at) VALUES (?, ?)').run(file, Date.now());
});

let count = 0;
for (const file of files) {
  if (applied.has(file)) continue;
  apply(file);
  count += 1;
  console.log(`applied ${file}`);
}
console.log(`migrate: ${count} applied, ${files.length} total (${dbPath})`);
db.close();
