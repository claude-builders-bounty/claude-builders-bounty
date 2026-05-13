
# SaaS Starter

A production-ready SaaS starter built with Next.js 14, SQLite, and TypeScript.

## Setup in 3 Steps

### Step 1: Install Dependencies

```bash
npm install
```

### Step 2: Initialize Database

```bash
# Generate and apply migrations
npm run db:generate
npm run db:migrate

# (Optional) Seed with sample data
npm run db:seed
```

### Step 3: Start Development

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to see your app.

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Create production build |
| `npm run start` | Start production server |
| `npm run test` | Run tests |
| `npm run lint` | Lint code |
| `npm run db:studio` | Open database GUI |

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Database**: SQLite (better-sqlite3)
- **ORM**: Drizzle ORM
- **Styling**: Tailwind CSS
- **Testing**: Vitest
- **Language**: TypeScript

---
