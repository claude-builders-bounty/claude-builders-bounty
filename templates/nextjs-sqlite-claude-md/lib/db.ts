import Database from 'better-sqlite3';
import { mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

// Single connection for the whole process. better-sqlite3 is synchronous,
// so one handle is safe and avoids pool overhead.
const DB_PATH = process.env.DATABASE_PATH ?? './dev.db';
mkdirSync(dirname(DB_PATH), { recursive: true });

export const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL'); // safe concurrent reads
db.pragma('foreign_keys = ON'); // enforce FK constraints

// Runs every migration in src/migrations in lexical order, once each.
export function runMigrations(): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      name TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);
  const applied = new Set(
    db.prepare('SELECT name FROM _migrations').all().map((r: any) => r.name)
  );
  // Caller feeds sorted .sql file names + their contents.
  // (Kept simple: pass an array of { name, sql }.)
  for (const { name, sql } of PENDING_MIGRATIONS) {
    if (applied.has(name)) continue;
    const tx = db.transaction(() => {
      db.exec(sql);
      db.prepare('INSERT INTO _migrations (name) VALUES (?)').run(name);
    });
    tx();
  }
}

// Populated by run-migrations.ts after importing the sorted SQL files.
export let PENDING_MIGRATIONS: { name: string; sql: string }[] = [];
export function setMigrations(m: { name: string; sql: string }[]): void {
  PENDING_MIGRATIONS = m;
}
