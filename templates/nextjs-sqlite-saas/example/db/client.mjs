import { DatabaseSync } from "node:sqlite";

export function openDatabase(location = ":memory:") {
  const db = new DatabaseSync(location);
  db.exec("PRAGMA foreign_keys = ON");
  return db;
}
