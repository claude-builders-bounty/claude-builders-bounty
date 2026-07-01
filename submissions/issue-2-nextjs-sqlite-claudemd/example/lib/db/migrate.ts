import Database from "better-sqlite3";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { env } from "@/lib/env";

// Applies pending migrations in filename order, each inside a transaction.
// Applied files are recorded in _migrations so re-runs are no-ops (idempotent).
const MIGRATIONS_DIR = join(import.meta.dirname, "migrations");

export function migrate(dbPath = env.DATABASE_PATH) {
  const db = new Database(dbPath);
  db.pragma("foreign_keys = ON");
  db.exec(
    `CREATE TABLE IF NOT EXISTS _migrations (
       name TEXT PRIMARY KEY,
       applied_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
     )`,
  );

  const applied = new Set<string>(
    db.prepare("SELECT name FROM _migrations").all().map((r: any) => r.name),
  );
  const files = readdirSync(MIGRATIONS_DIR)
    .filter((f) => f.endsWith(".sql"))
    .sort(); // 0001_… < 0002_… — lexical order is correct because we zero-pad

  let count = 0;
  for (const file of files) {
    if (applied.has(file)) continue;
    const sql = readFileSync(join(MIGRATIONS_DIR, file), "utf8");
    const run = db.transaction(() => {
      db.exec(sql);
      db.prepare("INSERT INTO _migrations (name) VALUES (?)").run(file);
    });
    run(); // a throw here rolls the whole file back and aborts
    console.log(`applied ${file}`);
    count++;
  }
  console.log(count ? `${count} migration(s) applied` : "up to date");
  db.close();
}

// `npm run db:migrate`
if (import.meta.url === `file://${process.argv[1]}`) migrate();
