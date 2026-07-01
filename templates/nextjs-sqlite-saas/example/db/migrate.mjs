import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const migrationsUrl = new URL("./migrations/", import.meta.url);

export function migrate(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      name TEXT PRIMARY KEY,
      applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
    )
  `);

  const applied = new Set(
    db.prepare("SELECT name FROM _migrations ORDER BY name").all().map((row) => row.name),
  );
  const migrationDir = fileURLToPath(migrationsUrl);
  const files = readdirSync(migrationDir).filter((file) => file.endsWith(".sql")).sort();
  const appliedNow = [];

  for (const file of files) {
    if (applied.has(file)) continue;

    const sql = readFileSync(new URL(file, migrationsUrl), "utf8");
    db.exec("BEGIN");
    try {
      db.exec(sql);
      db.prepare("INSERT INTO _migrations (name) VALUES (?)").run(file);
      db.exec("COMMIT");
      appliedNow.push(file);
    } catch (error) {
      db.exec("ROLLBACK");
      throw error;
    }
  }

  return appliedNow;
}
