# Opinionated Next.js 15 App Router + SQLite SaaS `CLAUDE.md`

A production-ready, highly opinionated `CLAUDE.md` template designed for modern SaaS architectures running **Next.js 15 App Router**, **React 19**, and **SQLite** (via Turso / `better-sqlite3` and Drizzle ORM).

---

## 🚀 How to Use in a Greenfield Project

1. Copy [`CLAUDE.md`](./CLAUDE.md) directly to the root of your Next.js SaaS repository:
   ```bash
   cp templates/nextjs-sqlite-saas/CLAUDE.md ./CLAUDE.md
   ```
2. Start Claude Code in your project directory:
   ```bash
   claude
   ```
3. Claude Code immediately understands:
   - File placement rules (Server Components vs Client Components)
   - SQLite PRAGMA invariants (WAL mode, Foreign Keys ON)
   - NanoID / UUIDv7 primary keys
   - Zod-validated Server Actions
   - Strict avoidance of internal API route bloat and client data-fetching waterfalls

---

## 🎯 Key Design Choices & Rationale

- **Server-First Data Access:** Because SQLite is an embedded file or edge replica, queries run in microseconds. Fetching directly inside Next.js Server Components avoids the latency penalty of HTTP internal APIs.
- **WAL Mode & Foreign Key Safety:** Standard SQLite lacks foreign key enforcement out-of-the-box unless `PRAGMA foreign_keys = ON;` is explicitly executed per connection. This template guarantees that invariant.
- **Anti-Enumeration NanoIDs:** Auto-increment integers are strictly forbidden for public resources to protect customer privacy and prevent URL brute-forcing.
- **Zod & Server Actions:** Mutations follow modern React 19 / Next.js 15 patterns, returning structured status objects instead of crashing with unhandled exceptions.
