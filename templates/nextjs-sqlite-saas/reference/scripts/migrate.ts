// scripts/migrate.ts — applies pending SQL migrations; never run on dev server startup
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import Database from "better-sqlite3";
import { env } from "../src/lib/env";

const MIGRATIONS_DIR = join(process.cwd(), "src/db/migrations");

export function ensureMigrationsTable(db: Database.Database): void {
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      filename TEXT NOT NULL UNIQUE,
      applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );
  `);
}

export function listMigrationFiles(): string[] {
  return readdirSync(MIGRATIONS_DIR)
    .filter((f) => f.endsWith(".sql"))
    .sort();
}

export function applyPendingMigrations(db: Database.Database): void {
  ensureMigrationsTable(db);
  const applied = new Set(
    (db.prepare("SELECT filename FROM _migrations").all() as { filename: string }[]).map(
      (row) => row.filename,
    ),
  );
  const files = listMigrationFiles();

  for (const filename of files) {
    if (applied.has(filename)) continue;
    const sql = readFileSync(join(MIGRATIONS_DIR, filename), "utf8");
    db.transaction(() => {
      db.exec(sql);
      db.prepare("INSERT INTO _migrations (filename) VALUES (?)").run(filename);
    })();
  }

  const recorded = (
    db.prepare("SELECT COUNT(*) as count FROM _migrations").get() as { count: number }
  ).count;
  if (recorded !== files.length) {
    throw new Error(
      "Migration integrity check failed: " + recorded + " applied vs " + files.length + " files",
    );
  }
}

function openDatabaseFromEnv(): Database.Database {
  if (env.DATABASE_URL === ":memory:") {
    throw new Error("db:migrate requires file: DATABASE_URL, not :memory:");
  }
  const filePath = env.DATABASE_URL.replace(/^file:/, "");
  const db = new Database(filePath);
  db.pragma("foreign_keys = ON");
  return db;
}

export function runMigrations(): void {
  const db = openDatabaseFromEnv();
  try {
    applyPendingMigrations(db);
  } finally {
    db.close();
  }
}

export function getMigrationStatus(): { applied: string[]; pending: string[] } {
  const db = openDatabaseFromEnv();
  try {
    ensureMigrationsTable(db);
    const applied = (
      db.prepare("SELECT filename FROM _migrations ORDER BY filename").all() as {
        filename: string;
      }[]
    ).map((row) => row.filename);
    const files = listMigrationFiles();
    const appliedSet = new Set(applied);
    return { applied, pending: files.filter((f) => !appliedSet.has(f)) };
  } finally {
    db.close();
  }
}

function printMigrationStatus(): void {
  const { applied, pending } = getMigrationStatus();
  console.log("Applied:", applied.length ? applied.join(", ") : "(none)");
  console.log("Pending:", pending.length ? pending.join(", ") : "(none)");
}

const isDirectRun = process.argv[1]?.endsWith("scripts/migrate.ts");
if (isDirectRun) {
  if (process.argv.includes("--status")) {
    printMigrationStatus();
  } else {
    runMigrations();
  }
}
