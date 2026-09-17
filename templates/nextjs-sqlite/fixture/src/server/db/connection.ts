import 'server-only';
import Database from 'better-sqlite3';
import { mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
const globalDb = globalThis as unknown as { sqliteFixture?: Database.Database };
export function getDb(): Database.Database {
 if (!globalDb.sqliteFixture) {
  const path = resolve(process.env.DATABASE_PATH ?? '.data/app.sqlite');
  mkdirSync(dirname(path), { recursive: true });
  const db = new Database(path);
  db.pragma('foreign_keys = ON'); db.pragma('journal_mode = WAL'); db.pragma('busy_timeout = 5000');
  globalDb.sqliteFixture = db;
 }
 return globalDb.sqliteFixture;
}
