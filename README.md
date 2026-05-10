# Next.js 15 + SQLite SaaS Starter

A greenfield SaaS project template with production-ready CLAUDE.md for Claude Code.

## Quick Start

```bash
# Create a new project
npx create-next-app@latest my-saas --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
cd my-saas

# Add this CLAUDE.md
curl -O https://raw.githubusercontent.com/gzmh2021/claude-builders-bounty/main/CLAUDE.md

# Install deps
pnpm install
pnpm add drizzle-orm better-sqlite3 @libsql/client @auth/core next-auth@beta
pnpm add -D drizzle-kit @types/better-sqlite3

# Set up database
mkdir -p src/db/schema
cat > src/db/index.ts << 'EOF'
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';

const sqlite = new Database('data/saas.db');
export const db = drizzle(sqlite);
EOF

# Run Claude Code
claude
```

Claude will read this CLAUDE.md and understand the full stack conventions without needing clarifying questions.

## What This CLAUDE.md Covers

- **Stack & versions** — pinned Next.js 15, Drizzle ORM, Auth.js, shadcn/ui
- **Folder structure** — opinionated App Router layout with clear domain separation
- **SQL / migration rules** — Drizzle-first, no raw SQL, auto-generated migrations
- **Component patterns** — Server Components first, typed interfaces, cn() utility
- **Error handling** — Server Action pattern, error boundaries, structured logging
- **Dev commands** — pnpm scripts for everything
- **Anti-patterns** — 8 explicit things we don't do (with reasons)
