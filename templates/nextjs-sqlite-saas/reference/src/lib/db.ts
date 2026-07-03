import Database from "better-sqlite3";
import { env } from "./env";

// Singleton connection — reference app uses better-sqlite3 only (file: or :memory:).
// Production apps swap this module to support libsql:// via env.DATABASE_URL.
let instance: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!instance) {
    if (env.DATABASE_URL === ":memory:") {
      instance = new Database(":memory:");
    } else if (env.DATABASE_URL.startsWith("file:")) {
      const filePath = env.DATABASE_URL.replace(/^file:/, "");
      instance = new Database(filePath);
    } else {
      throw new Error("Reference app supports file: or :memory: DATABASE_URL only");
    }
    // WAL improves concurrent read/write in dev; foreign_keys enforces migration integrity.
    instance.pragma("journal_mode = WAL");
    instance.pragma("foreign_keys = ON");
  }
  return instance;
}

/** Test-only hook to reset the singleton between suites. */
export function resetDbForTests(): void {
  if (instance) {
    instance.close();
    instance = null;
  }
}
