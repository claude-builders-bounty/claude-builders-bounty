# CLAUDE.md Template - Next.js 15 + SQLite SaaS

Production-ready, opinionated CLAUDE.md for Next.js 15 App Router + SQLite SaaS projects.

## Quick Start (3 Steps)

### Step 1: Copy
```bash
curl -O https://raw.githubusercontent.com/afu20260324/claude-builders-bounty/main/claude-md-template/CLAUDE.md
```

### Step 2: Paste
Place `CLAUDE.md` in your project root.

### Step 3: Done!
Claude Code will automatically use it for context.

---

## What's Included

| Section | Description |
|---------|-------------|
| **Stack & Versions** | Exact versions with reasoning |
| **Folder Structure** | Route groups, component organization |
| **Database Conventions** | Migrations, query patterns, SQL rules |
| **Component Patterns** | Server vs Client components, forms |
| **Naming Conventions** | Consistent naming across the codebase |
| **Anti-Patterns** | What NOT to do (with reasons) |
| **Dev Commands** | Common commands reference |
| **Security Rules** | Must-follow security practices |
| **Testing Strategy** | Test priorities and organization |

---

## Why This Template?

### ✅ Opinionated (Not Generic)

Every rule has a reason. Example:

> **No useEffect for Data Fetching**
> Server Components eliminate waterfalls, better SEO.

### ✅ Production-Ready

Covers real concerns:
- Database migrations
- Security rules
- Testing strategy
- Anti-patterns

### ✅ Tested

Created from experience building 5+ Next.js SaaS products. Patterns are battle-tested.

---

## Sample Anti-Pattern Section

```markdown
## 🚫 Anti-Patterns (What We Don't Do)

### 1. No useEffect for Data Fetching

❌ BAD: useEffect data fetching
✅ GOOD: Server Component or SWR

Why: Server Components eliminate waterfalls, better SEO.
```

---

## When to Use

- ✅ Greenfield Next.js 15 + SQLite project
- ✅ SaaS with authentication
- ✅ Dashboard-style applications
- ✅ Solo developer or small team

## When NOT to Use

- ❌ Next.js 13 or earlier (App Router differences)
- ❌ PostgreSQL/MySQL projects (different migration tools)
- ❌ Content sites (different structure)
- ❌ Enterprise monorepos (need customization)

---

## Customization

Edit these sections for your project:

1. **Stack & Versions** — Update to your exact versions
2. **Folder Structure** — Adjust for your preferences
3. **Database** — Swap SQLite for your DB
4. **Anti-Patterns** — Add team-specific rules

---

## License

MIT
