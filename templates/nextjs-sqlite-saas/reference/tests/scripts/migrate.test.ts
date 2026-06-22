import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import Database from "better-sqlite3";
import {
  applyPendingMigrations,
  ensureMigrationsTable,
  listMigrationFiles,
} from "../../scripts/migrate";

describe("scripts/migrate", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

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

  it("getMigrationStatus reports applied vs pending for file database", async () => {
    const dir = mkdtempSync(join(tmpdir(), "migrate-status-"));
    const dbPath = join(dir, "test.db");
    vi.stubEnv("DATABASE_URL", `file:${dbPath}`);

    const { getMigrationStatus, applyPendingMigrations, listMigrationFiles } = await import(
      "../../scripts/migrate"
    );
    const files = listMigrationFiles();

    expect(getMigrationStatus()).toEqual({ applied: [], pending: files });

    const db = new Database(dbPath);
    db.pragma("foreign_keys = ON");
    applyPendingMigrations(db);
    db.close();

    expect(getMigrationStatus()).toEqual({ applied: files, pending: [] });
    rmSync(dir, { recursive: true, force: true });
  });
});
