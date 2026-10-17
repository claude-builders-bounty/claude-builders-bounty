#!/usr/bin/env bash
# Creates the exact tree CLAUDE.md describes, so the doc can be checked against reality.
#   bash scaffold.sh [target-dir]      (default: ./_scaffold)
set -euo pipefail

TARGET="${1:-_scaffold}"
[ -e "$TARGET" ] && rm -rf "$TARGET"
mkdir -p "$TARGET"
cd "$TARGET"

# --- directories -----------------------------------------------------------------
mkdir -p "app/(marketing)" "app/(app)" "app/api/stripe/webhook" \
         components/ui components/invoices \
         db/migrations db/queries \
         lib tests/unit tests/e2e data

# --- app -------------------------------------------------------------------------
cat > app/layout.tsx <<'EOF'
export const metadata = { title: "App" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
EOF

cat > "app/(marketing)/page.tsx" <<'EOF'
export default function Home() {
  return <main>Marketing</main>;
}
EOF

cat > "app/(app)/layout.tsx" <<'EOF'
import { requireUser } from "@/lib/auth";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  await requireUser();
  return <div>{children}</div>;
}
EOF

cat > "app/(app)/page.tsx" <<'EOF'
export default function Dashboard() {
  return <main>Dashboard</main>;
}
EOF

cat > app/api/stripe/webhook/route.ts <<'EOF'
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.text();
  return NextResponse.json({ received: body.length > 0 });
}
EOF

# --- components ------------------------------------------------------------------
cat > components/ui/button.tsx <<'EOF'
export function Button(props: React.ComponentProps<"button">) {
  return <button className="rounded bg-black px-3 py-2 text-white" {...props} />;
}
EOF

cat > components/invoices/invoice-list.tsx <<'EOF'
import type { Invoice } from "@/db/queries/invoices";

export function InvoiceList({ invoices }: { invoices: Invoice[] }) {
  return (
    <ul>
      {invoices.map((i) => (
        <li key={i.id}>{i.total_cents}</li>
      ))}
    </ul>
  );
}
EOF

# --- db --------------------------------------------------------------------------
cat > db/client.ts <<'EOF'
import Database from "better-sqlite3";
import { env } from "@/lib/env";

const g = globalThis as { __db?: Database.Database };

export const db =
  g.__db ??
  (() => {
    const d = new Database(env.DATABASE_PATH);
    d.pragma("journal_mode = WAL");
    d.pragma("foreign_keys = ON");
    d.pragma("busy_timeout = 5000");
    return d;
  })();

if (process.env.NODE_ENV !== "production") g.__db = db;
EOF

cat > db/migrate.ts <<'EOF'
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { db } from "./client";

db.exec("CREATE TABLE IF NOT EXISTS _migrations (name TEXT PRIMARY KEY, applied_at TEXT NOT NULL)");

const applied = new Set(
  (db.prepare("SELECT name FROM _migrations").all() as { name: string }[]).map((r) => r.name)
);
const dir = join(process.cwd(), "db", "migrations");
const pending = readdirSync(dir)
  .filter((f) => f.endsWith(".sql") && !applied.has(f))
  .sort();

for (const file of pending) {
  const sql = readFileSync(join(dir, file), "utf8");
  db.transaction(() => {
    db.exec(sql);
    db.prepare("INSERT INTO _migrations (name, applied_at) VALUES (?, ?)").run(
      file,
      new Date().toISOString()
    );
  })();
  console.log(`applied ${file}`);
}
console.log(pending.length ? `${pending.length} applied` : "up to date");
EOF

cat > db/migrations/0001_init.sql <<'EOF'
-- the runner opens the transaction; do not add BEGIN/COMMIT here
CREATE TABLE IF NOT EXISTS users (
  id          TEXT PRIMARY KEY,
  email       TEXT NOT NULL UNIQUE,
  is_active   INTEGER NOT NULL DEFAULT 1,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

CREATE TABLE IF NOT EXISTS invoices (
  id          TEXT PRIMARY KEY,
  user_id     TEXT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
  total_cents INTEGER NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices (user_id);
EOF

cat > db/queries/users.ts <<'EOF'
import { db } from "@/db/client";

export type User = { id: string; email: string; is_active: 0 | 1; created_at: string };

const byId = db.prepare("SELECT id, email, is_active, created_at FROM users WHERE id = ?");

export const getUser = (id: string) => byId.get(id) as User | undefined;
EOF

cat > db/queries/invoices.ts <<'EOF'
import { db } from "@/db/client";

export type Invoice = { id: string; user_id: string; total_cents: number; created_at: string };

const listByUser = db.prepare(
  "SELECT id, user_id, total_cents, created_at FROM invoices WHERE user_id = ? ORDER BY created_at DESC"
);

export const listInvoices = (userId: string) => listByUser.all(userId) as Invoice[];
EOF

cat > db/new.mjs <<'EOF'
import { mkdirSync, readdirSync, writeFileSync } from "node:fs";

const name = (process.argv[2] ?? "change").replace(/[^a-z0-9_]/gi, "_").toLowerCase();
mkdirSync("db/migrations", { recursive: true });
const n = String(readdirSync("db/migrations").filter((f) => f.endsWith(".sql")).length + 1).padStart(4, "0");
const file = `db/migrations/${n}_${name}.sql`;
writeFileSync(file, "-- the runner opens the transaction; do not add BEGIN/COMMIT here\n\n");
console.log(file);
EOF

cat > db/reset.mjs <<'EOF'
import { rmSync } from "node:fs";

for (const f of ["data/app.db", "data/app.db-wal", "data/app.db-shm"]) rmSync(f, { force: true });
console.log("database removed");
EOF

# --- lib -------------------------------------------------------------------------
cat > lib/env.ts <<'EOF'
import { z } from "zod";

const schema = z.object({
  DATABASE_PATH: z.string().default("data/app.db"),
  SESSION_SECRET: z.string().min(16),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
});

export const env = schema.parse(process.env);
EOF

cat > lib/auth.ts <<'EOF'
import { cookies } from "next/headers";
import { db } from "@/db/client";

export async function requireUser() {
  const token = (await cookies()).get("session")?.value;
  if (!token) return null;
  return db.prepare("SELECT id, email FROM sessions WHERE token = ?").get(token) ?? null;
}
EOF

cat > lib/result.ts <<'EOF'
export type Result<T, E = string> = { ok: true; value: T } | { ok: false; error: E };

export const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
export const err = <E>(error: E): Result<never, E> => ({ ok: false, error });
EOF

# --- tests -----------------------------------------------------------------------
cat > tests/unit/result.test.ts <<'EOF'
import test from "node:test";
import assert from "node:assert/strict";
import { ok, err } from "../../lib/result";

test("ok and err discriminate", () => {
  assert.equal(ok(1).ok, true);
  assert.equal(err("x").ok, false);
});
EOF

cat > tests/e2e/smoke.spec.ts <<'EOF'
import { test, expect } from "@playwright/test";

test("marketing page renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("main")).toBeVisible();
});
EOF

# --- root config -----------------------------------------------------------------
cat > package.json <<'EOF'
{
  "name": "saas-app",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "typecheck": "tsc --noEmit",
    "lint": "eslint .",
    "test": "node --import tsx --test \"tests/unit/**/*.test.ts\"",
    "test:e2e": "playwright test",
    "db:migrate": "node --env-file-if-exists=.env --import tsx db/migrate.ts",
    "db:reset": "node db/reset.mjs && npm run db:migrate",
    "db:new": "node db/new.mjs"
  },
  "dependencies": {
    "better-sqlite3": "^11.5.0",
    "next": "^15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "@playwright/test": "^1.49.0",
    "@types/better-sqlite3": "^7.6.11",
    "@types/node": "^22.10.0",
    "@types/react": "^19.0.0",
    "tsx": "^4.19.0",
    "typescript": "^5.7.0"
  }
}
EOF

cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noEmit": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "jsx": "preserve",
    "paths": { "@/*": ["./*"] }
  },
  "include": ["**/*.ts", "**/*.tsx"]
}
EOF

cat > .env.example <<'EOF'
DATABASE_PATH=data/app.db
SESSION_SECRET=change-me-to-at-least-16-chars
EOF

cp .env.example .env

cat > .gitignore <<'EOF'
node_modules
.next
data/*.db*
.env
EOF

echo "scaffolded $TARGET: $(find . -type f | wc -l) files"
