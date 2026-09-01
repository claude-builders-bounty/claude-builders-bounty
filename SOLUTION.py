CLAUDE_MD = """\
# SaaS Project Configuration

## 💰 Stack & Versions
- **Framework:** Next.js 15 (App Router)
- **Database:** SQLite (better-sqlite3 / Turso)
- **State:** Zustand / TanStack Query
- **Lint:** `eslint` + `remark-preset-lint-markdown`
- **Types:** Strict `tsconfig.json` + `path-aliases`

## 📂 Folder Structure
- **Convention:** Monoreach-friendly, flat but logical.
- **Rules:**
  - `src/` (or root) is the entry point.
  - `app/` contains App Router routes.
  - `lib/` for pure utility and DB connections.
  - `types/` for shared interfaces (if DTS isn't enough).
  - `db/schema.sql` for Turso/migrations.

## 🗄️ SQL / Migration Conventions
- **Naming:** Singular tables (`Users`), `snake_case` columns.
- **Engine:** `better-sqlite` (sync) or `sql.js` (pure JS wrapper).
- **Migrations:**
  - `db/migrations/001_create_users.up.sql`
  - `db/migrations/001_create_users.down.sql`
- **Transaction:** Wrap mutations in `db.transaction` for atomicity.
- **Indexing:** Auto-create on write for < 1M rows.

## 🧩 Component Patterns
- **Structure:** `Component` -> `Wrapper` -> `Content`.
- **Props:** Spread logic handles defaults; explicit `children` where needed.
- **Server Actions:** Async functions named `useAction`.
- **Types:** Infer props from the component definition.
- **Naming:** PascalCase for files (`Card`), PascalCase for components (`Card`), `index.ts` re-exports the main export.

## 🧠 Logic & Anti-Patterns
- **Do:** Fetch data on mount (Next.js 15 hydration-safe).
- **Do:** Use `cache` strategies for optimistic UI.
- **Avoid:** Direct `window` access during SSR (guard with `useEffect` or `window` check).
- **Avoid:** Over-fragmenting small components (group related UI).
- **Avoid:** Sync state for Server Components (use `props` or `React.Lazy`).

## 🧪 Dev Experience
- **Hot Reloading:** Enabled for `app/` folders.
- **Console:** `import.meta.env.NODE_ENV` guards.
- **Imports:** `import.meta.aliases` or `import './index'` for circular deps.
- **Scripts:**
  - `dev:build` — Transpile components.
  - `db:init` — Seed and migrate.
"""

def get_claude_context():
    return CLAUDE_MD

def main():
    content = get_claude_context()
    print(content)
    # Save to file for immediate use
    from pathlib import Path
    Path('.CLAUDE.md').write_text(content)

if __name__ == "__main__":
    main()