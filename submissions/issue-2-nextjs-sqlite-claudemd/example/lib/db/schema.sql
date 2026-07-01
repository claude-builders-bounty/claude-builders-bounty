-- Canonical schema for a fresh database. Kept in sync with migrations/.
-- Timestamps: INTEGER epoch-millis. Money: INTEGER minor units. Booleans: 0/1.

CREATE TABLE users (
  id         TEXT PRIMARY KEY,               -- app-generated id (e.g. nanoid)
  email      TEXT NOT NULL UNIQUE,
  name       TEXT,
  is_active  INTEGER NOT NULL DEFAULT 1,      -- boolean 0/1
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
  id              TEXT PRIMARY KEY,
  user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status          TEXT NOT NULL,             -- 'trialing' | 'active' | 'canceled'
  price_cents     INTEGER NOT NULL,          -- money as integer minor units
  current_period_end INTEGER NOT NULL,
  created_at      INTEGER NOT NULL DEFAULT (unixepoch() * 1000)
);
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
