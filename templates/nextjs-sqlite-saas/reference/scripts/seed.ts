// scripts/seed.ts — dev-only fixtures; never run against production data
import Database from "better-sqlite3";
import { env } from "../src/lib/env";

export function assertSeedAllowed(): void {
  if (process.env.NODE_ENV === "production") {
    console.error("db:seed is blocked in production");
    process.exit(1);
  }
}

export function seedDevOrganizations(db: Database.Database): void {
  db.prepare(
    `INSERT INTO organizations (id, slug) VALUES (?, ?)
     ON CONFLICT(id) DO NOTHING`,
  ).run("org-dev-1", "acme");
}

export function runSeed(): void {
  assertSeedAllowed();
  const filePath = env.DATABASE_URL.replace(/^file:/, "");
  const db = new Database(filePath);
  db.pragma("foreign_keys = ON");
  seedDevOrganizations(db);
  db.close();
}

const isDirectRun = process.argv[1]?.endsWith("scripts/seed.ts");
if (isDirectRun) {
  runSeed();
}
