// lib/db/client.ts
//
// The ONE place in the codebase that knows which SQLite driver is active.
// All other code imports `db` from here and uses Drizzle's driver-agnostic
// query API. Never branch on the driver outside this file.

import { drizzle as drizzleBetter } from "drizzle-orm/better-sqlite3";
import { drizzle as drizzleLibsql } from "drizzle-orm/libsql";
import { migrate as migrateBetter } from "drizzle-orm/better-sqlite3/migrator";
import { migrate as migrateLibsql } from "drizzle-orm/libsql/migrator";
import Database from "better-sqlite3";
import { createClient } from "@libsql/client";

import * as schema from "./schema";

const isLibsql = !!process.env.TURSO_DATABASE_URL;

export const db = (() => {
  if (isLibsql) {
    const client = createClient({
      url: process.env.TURSO_DATABASE_URL!,
      authToken: process.env.TURSO_AUTH_TOKEN,
    });
    return drizzleLibsql(client, { schema });
  }
  const dbPath = process.env.DATABASE_URL?.replace(/^file:/, "") ?? "dev.db";
  const sqlite = new Database(dbPath);
  // Mandatory per CLAUDE.md — SQLite ignores foreign keys by default.
  sqlite.pragma("foreign_keys = ON");
  // WAL improves concurrent read perf significantly for SaaS workloads.
  sqlite.pragma("journal_mode = WAL");
  return drizzleBetter(sqlite, { schema });
})();

/**
 * Run pending migrations. Call once on app boot.
 * Safe to call multiple times — drizzle-kit tracks applied migrations.
 */
export async function migrate(): Promise<void> {
  const folder = "./lib/db/migrations";
  if (isLibsql) {
    // @ts-expect-error — drizzle's migrator union types don't narrow cleanly
    await migrateLibsql(db, { migrationsFolder: folder });
  } else {
    // @ts-expect-error — same
    migrateBetter(db, { migrationsFolder: folder });
  }
}

export type Db = typeof db;
