CREATE TABLE items (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  created_at INTEGER NOT NULL
);
CREATE INDEX items_created_at_idx ON items (created_at);
