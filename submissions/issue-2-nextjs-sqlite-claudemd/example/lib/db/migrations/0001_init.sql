-- 0001_init: initial schema. Forward-only, immutable once merged.
CREATE TABLE users (
  id         TEXT PRIMARY KEY,
  email      TEXT NOT NULL UNIQUE,
  name       TEXT,
  is_active  INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000),
  updated_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);

CREATE TABLE sessions (
  id         TEXT PRIMARY KEY,
  user_id    TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at INTEGER NOT NULL,
  created_at INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);
CREATE INDEX idx_sessions_user_id ON sessions(user_id);

CREATE TABLE subscriptions (
  id                  TEXT PRIMARY KEY,
  user_id             TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status              TEXT NOT NULL,
  price_cents         INTEGER NOT NULL,
  current_period_end  INTEGER NOT NULL,
  created_at          INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
