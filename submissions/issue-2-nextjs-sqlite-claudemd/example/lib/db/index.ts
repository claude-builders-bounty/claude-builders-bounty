import Database from "better-sqlite3";
import { env } from "@/lib/env";

// Single shared connection. better-sqlite3 is synchronous, so no pool is needed.
export const db = new Database(env.DATABASE_PATH);

// Pragmas that must be set on every connection:
db.pragma("journal_mode = WAL"); // concurrent reads during writes
db.pragma("foreign_keys = ON"); // SQLite disables FK enforcement by default
