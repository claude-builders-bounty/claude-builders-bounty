# CLAUDE.md — Next.js + SQLite SaaS Starter

## Project Overview
Full-stack SaaS application with Next.js 14 (App Router), SQLite via better-sqlite3, and Tailwind CSS.

## Tech Stack
- **Frontend:** Next.js 14, React 18, Tailwind CSS, shadcn/ui
- **Backend:** Next.js API routes, better-sqlite3
- **Auth:** NextAuth.js with credentials + OAuth providers
- **Payments:** Stripe checkout sessions
- **Email:** Resend for transactional emails
- **Deployment:** Vercel (frontend) + optional Docker (SQLite persistence)

## Project Structure
```
/
├── app/                  # Next.js App Router
│   ├── api/              # API routes (auth, stripe, users)
│   ├── (auth)/           # Auth pages (login, register)
│   ├── dashboard/        # Protected dashboard routes
│   └── layout.tsx        # Root layout
├── components/           # React components
│   ├── ui/               # shadcn/ui components
│   └── forms/            # Form components
├── lib/                  # Utility functions
│   ├── db.ts             # SQLite database client
│   ├── auth.ts           # NextAuth configuration
│   └── stripe.ts         # Stripe client
├── prisma/               # Prisma schema (if using ORM)
├── public/               # Static assets
├── .env.example          # Environment variables template
├── tailwind.config.ts    # Tailwind configuration
└── package.json          # Dependencies
```

## Commands
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run database migrations
npm run db:migrate

# Seed database
npm run db:seed

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format
```

## Database
SQLite database is stored at `./data/app.db`. Use better-sqlite3 directly:
```typescript
import Database from 'better-sqlite3';
const db = new Database('./data/app.db');
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');
```

For production with Docker, mount a volume at `/app/data` to persist the database.

## Environment Variables
Required in `.env`:
```
DATABASE_URL="file:./data/app.db"
NEXTAUTH_SECRET="generate-random-secret"
NEXTAUTH_URL="http://localhost:3000"
GITHUB_ID=""
GITHUB_SECRET=""
GOOGLE_ID=""
GOOGLE_SECRET=""
STRIPE_SECRET_KEY=""
STRIPE_WEBHOOK_SECRET=""
RESEND_API_KEY=""
```

## Key Patterns

### API Route with Auth
```typescript
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export async function GET(request: Request) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return Response.json({ error: 'Unauthorized' }, { status: 401 });
  }
  // ... your logic
}
```

### Database Query
```typescript
import { db } from '@/lib/db';

export function getUserById(id: string) {
  return db.prepare('SELECT * FROM users WHERE id = ?').get(id);
}
```

### Protected Page
```typescript
import { redirect } from 'next/navigation';
import { getServerSession } from 'next-auth';

export default async function DashboardPage() {
  const session = await getServerSession();
  if (!session) redirect('/login');
  return <div>Welcome {session.user?.name}</div>;
}
```

## Testing
- Unit tests: Vitest
- E2E tests: Playwright
- API tests: supertest + vitest

```bash
npm test              # Run all tests
npm run test:e2e      # Run E2E tests
npm run test:coverage # Coverage report
```

## Deployment
1. Push to GitHub
2. Connect to Vercel
3. Set environment variables in Vercel dashboard
4. Deploy

For SQLite persistence, use Vercel KV or switch to Turso/LibSQL for edge-compatible SQLite.
