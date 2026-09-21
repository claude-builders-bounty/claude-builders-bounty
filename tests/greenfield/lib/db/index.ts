import Database from "better-sqlite3";
const globalForDb = globalThis as unknown as { db?: Database.Database };
export const db = globalForDb.db ?? new Database(process.env.DATABASE_PATH ?? ":memory:");
if (process.env.NODE_ENV !== "production") globalForDb.db = db;
db.pragma("journal_mode = WAL"); db.pragma("foreign_keys = ON"); db.pragma("busy_timeout = 5000");
