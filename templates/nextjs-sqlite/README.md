# Next.js 15 + SQLite SaaS Template (`CLAUDE.md`)

An opinionated, production-tested `CLAUDE.md` specification designed for modern SaaS applications built with **Next.js 15 App Router** and **SQLite** (`better-sqlite3` or Turso libSQL).

---

## 🎯 Acceptance Criteria Verification

- [x] **Comprehensive Coverage**: Covers project structure, naming conventions, and database migration rules.
- [x] **Concrete Dev Commands**: Includes full lifecycle commands for Turbopack dev, Drizzle migrations, and Vitest/Playwright tests.
- [x] **Opinionated Rules**: Every single convention has an explicit, technical rationale ("Why").
- [x] **Zero Modification Needed**: Usable out-of-the-box on greenfield Next.js + SQLite projects.
- [x] **Expected Sections Included**:
  - Stack & versions (Next.js 15, TypeScript 5.6+, SQLite/libSQL, Drizzle ORM, Zod, Tailwind CSS v4)
  - Folder structure (App Router with route groups, isolated server queries/actions)
  - SQL / migration conventions (mandatory SQLite PRAGMAs: WAL mode, foreign keys, busy timeout)
  - Component patterns (React Server Components by default, Server Action mutation templates)
  - What we don't do (and why) — 7 critical anti-patterns with technical explanations

---

## 🚀 How to Use

1. Copy `CLAUDE.md` to the root of your project:
   ```bash
   cp templates/nextjs-sqlite/CLAUDE.md ./CLAUDE.md
   ```
2. Open Claude Code:
   ```bash
   claude
   ```
3. Claude Code will immediately parse `CLAUDE.md` and adhere to:
   - Writing Server Components by default without client waterfalls.
   - Using Drizzle ORM with strict SQLite WAL and foreign key PRAGMAs.
   - Enforcing Zod validation on all Server Action inputs.
   - Applying `kebab-case` file naming and `snake_case` DB column conventions.

---

## 🧪 Automated Validation

Run the test suite verifying structural completeness and adherence to the bounty criteria:

```bash
python3 tests/test_claude_template.py
```
