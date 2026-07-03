import { describe, it, expect } from "vitest";
import Database from "better-sqlite3";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

describe("migrations", () => {
  it("applies all SQL files and records them in _migrations", () => {
    const db = new Database(":memory:");
    db.exec(`
      CREATE TABLE _migrations (
        filename TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
      );
    `);
    const migrationsDir = join(process.cwd(), "src/db/migrations");
    const files = readdirSync(migrationsDir)
      .filter((f) => f.endsWith(".sql"))
      .sort();
    const insert = db.prepare("INSERT INTO _migrations (filename) VALUES (?)");
    for (const filename of files) {
      db.exec(readFileSync(join(migrationsDir, filename), "utf8"));
      insert.run(filename);
    }
    const count = (
      db.prepare("SELECT COUNT(*) as count FROM _migrations").get() as { count: number }
    ).count;
    expect(count).toBe(files.length);
  });
});
