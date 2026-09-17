import Database from 'better-sqlite3';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
export function migrate(db, dir) {
 const files = fs.readdirSync(dir).filter(n => n.endsWith('.sql'));
 const versions = new Set();
 const migrations = files.map(name => {
  const match = /^(\d{4})_[a-z0-9_]+\.sql$/.exec(name);
  if (!match) throw Error('Invalid migration filename: ' + name);
  const version = Number(match[1]);
  if (versions.has(version)) throw Error('Duplicate migration version: ' + version);
  versions.add(version);
  const sql = fs.readFileSync(path.join(dir, name), 'utf8');
  return { version, name, sql, hash: createHash('sha256').update(sql).digest('hex') };
 }).sort((a, b) => a.version - b.version);
 return db.transaction(() => {
  db.exec('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, filename TEXT NOT NULL, checksum TEXT NOT NULL, applied_at_ms INTEGER NOT NULL)');
  const applied = db.prepare('SELECT version, filename, checksum FROM schema_migrations ORDER BY version').all();
  for (const row of applied) {
   const current = migrations.find(m => m.version === row.version);
   if (!current || row.filename !== current.name || row.checksum !== current.hash) throw Error('Applied migration changed or disappeared: ' + row.version);
  }
  let count = 0;
  for (const m of migrations) {
   if (applied.some(row => row.version === m.version)) continue;
   if (applied.some(row => row.version > m.version)) throw Error('Out-of-order migration: ' + m.version);
   db.exec(m.sql);
   db.prepare('INSERT INTO schema_migrations VALUES (?, ?, ?, ?)').run(m.version, m.name, m.hash, Date.now());
   count++;
  }
  return count;
 }).immediate();
}
if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
 const dbPath = path.resolve(process.env.DATABASE_PATH || '.data/app.sqlite');
 fs.mkdirSync(path.dirname(dbPath), { recursive: true });
 const db = new Database(dbPath);
 try {
  db.pragma('foreign_keys = ON'); db.pragma('journal_mode = WAL'); db.pragma('busy_timeout = 5000');
  console.log('Applied migrations:', migrate(db, path.resolve('migrations')));
 } finally { db.close(); }
}
