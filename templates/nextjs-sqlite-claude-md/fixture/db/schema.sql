-- Desired schema. Reference only: never executed. Migrations are the source of truth.
CREATE TABLE items (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  archived_at INTEGER
);
CREATE INDEX items_created_at_idx ON items (created_at);
