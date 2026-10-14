import Database from 'better-sqlite3';

const dbPath = process.env.DATABASE_PATH ?? './data/app.db';

let db: Database.Database | null = null;

/** The only place in the codebase that opens the database. */
export function getDb(): Database.Database {
  if (!db) {
    db = new Database(dbPath);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
  }
  return db;
}
