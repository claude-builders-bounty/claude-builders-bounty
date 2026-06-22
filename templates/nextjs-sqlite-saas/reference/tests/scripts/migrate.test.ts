import { describe, expect, it } from "vitest";
import Database from "better-sqlite3";
import {
  applyPendingMigrations,
  ensureMigrationsTable,
  listMigrationFiles,
} from "../../scripts/migrate";

describe("scripts/migrate", () => {

  it("lists migration files in lexicographic order", () => {
    const files = listMigrationFiles();
    expect(files.length).toBeGreaterThan(0);
    expect(files).toEqual([...files].sort());
  });

  it("applies pending migrations and passes integrity check", () => {
    const db = new Database(":memory:");
    db.pragma("foreign_keys = ON");
    applyPendingMigrations(db);

    const files = listMigrationFiles();
    const recorded = (
      db.prepare("SELECT COUNT(*) as count FROM _migrations").get() as { count: number }
    ).count;
    expect(recorded).toBe(files.length);
    db.close();
  });

  it("skips already-applied migrations on re-run", () => {
    const db = new Database(":memory:");
    db.pragma("foreign_keys = ON");
    applyPendingMigrations(db);
    applyPendingMigrations(db);

    const files = listMigrationFiles();
    const recorded = (
      db.prepare("SELECT COUNT(*) as count FROM _migrations").get() as { count: number }
    ).count;
    expect(recorded).toBe(files.length);
    db.close();
  });

  it("ensureMigrationsTable is idempotent", () => {
    const db = new Database(":memory:");
    ensureMigrationsTable(db);
    ensureMigrationsTable(db);
    const row = db
      .prepare("SELECT name FROM sqlite_master WHERE type = 'table' AND name = '_migrations'")
      .get();
    expect(row).toBeTruthy();
    db.close();
  });
});
