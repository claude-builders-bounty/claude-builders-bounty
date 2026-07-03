import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { getDb, resetDbForTests } from "@/lib/db";

const MIGRATIONS_DIR = join(process.cwd(), "src/db/migrations");

export function applyAllMigrations(): void {
  resetDbForTests();
  const db = getDb();
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      filename TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    );
  `);

  const files = readdirSync(MIGRATIONS_DIR)
    .filter((f) => f.endsWith(".sql"))
    .sort();

  const insert = db.prepare("INSERT INTO _migrations (filename) VALUES (?)");
  for (const filename of files) {
    db.exec(readFileSync(join(MIGRATIONS_DIR, filename), "utf8"));
    insert.run(filename);
  }
}

export function seedOrganization(orgId: string, slug: string): void {
  const db = getDb();
  db.prepare(
    `INSERT INTO organizations (id, slug)
     VALUES (?, ?)`,
  ).run(orgId, slug);
}
