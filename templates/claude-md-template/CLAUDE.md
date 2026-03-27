# CLAUDE.md - Next.js SaaS Starter Template

> AI-assisted development guide for Next.js SaaS applications

## Project Overview

This CLAUDE.md template provides context and conventions for AI assistants (Claude, GPT-4, etc.) working on Next.js SaaS applications. It ensures consistent, high-quality code that follows modern best practices.

---

## Architecture

### Tech Stack
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: PostgreSQL with Prisma ORM
- **Auth**: NextAuth.js / Clerk / Supabase Auth
- **Payments**: Stripe
- **Email**: Resend / SendGrid
- **File Storage**: AWS S3 / Cloudflare R2
- **Deployment**: Vercel / Docker

### Project Structure

```
app/
├── (auth)/              # Auth-related pages (login, signup, etc.)
│   ├── login/
│   ├── signup/
│   └── forgot-password/
├── (dashboard)/         # Protected dashboard pages
│   ├── dashboard/
│   ├── settings/
│   └── billing/
├── (marketing)/         # Public marketing pages
│   ├── page.tsx         # Landing page
│   ├── pricing/
│   └── about/
├── api/                 # API routes
│   ├── auth/
│   ├── webhooks/
│   └── stripe/
├── layout.tsx           # Root layout
└── globals.css

components/
├── ui/                  # Base UI components (Button, Input, etc.)
├── features/            # Feature-specific components
├── layouts/             # Layout components
└── providers/           # Context providers

lib/
├── auth.ts              # Auth utilities
├── db.ts                # Database client
├── stripe.ts            # Stripe utilities
├── email.ts             # Email utilities
└── utils.ts             # General utilities

prisma/
├── schema.prisma        # Database schema
├── migrations/          # Migration files
└── seed.ts              # Database seeding

types/
└── index.ts             # Shared TypeScript types

tests/
├── unit/                # Unit tests
├── integration/         # Integration tests
└── e2e/                 # End-to-end tests (Playwright)
```

---

## Key Conventions

### Naming
- **Files**: `kebab-case.tsx` for components
- **Components**: `PascalCase` for React components
- **Functions**: `camelCase` for utilities
- **Constants**: `SCREAMING_SNAKE_CASE`

### Component Structure
```tsx
// Imports (grouped)
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/lib/auth';

// Types
interface Props {
  title: string;
  onSubmit?: () => void;
}

// Component
export function MyComponent({ title, onSubmit }: Props) {
  // Hooks
  const { user } = useAuth();
  const [value, setValue] = useState('');
  
  // Handlers
  const handleSubmit = () => {
    onSubmit?.();
  };
  
  // Render
  return (
    <div className="...">
      <h1>{title}</h1>
      <Button onClick={handleSubmit}>Submit</Button>
    </div>
  );
}
```

### API Routes
```tsx
// app/api/example/route.ts
import { NextResponse } from 'next/server';
import { auth } from '@/lib/auth';

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // Logic here
    
    return NextResponse.json({ data: 'success' });
  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    );
  }
}
```

---

## Database Schema

### Common Models

```prisma
model User {
  id            String    @id @default(cuid())
  email         String    @unique
  name          String?
  emailVerified DateTime?
  image         String?
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  
  accounts      Account[]
  sessions      Session[]
  subscriptions Subscription[]
  
  @@map("users")
}

model Account {
  // NextAuth.js account model
}

model Subscription {
  id              String   @id @default(cuid())
  userId          String
  status          String   // active, canceled, past_due
  stripePriceId   String
  stripeCustomerId String
  currentPeriodEnd DateTime
  
  user            User     @relation(fields: [userId], references: [id])
  
  @@map("subscriptions")
}

model AuditLog {
  id        String   @id @default(cuid())
  userId    String
  action    String
  details   Json?
  createdAt DateTime @default(now())
  
  @@map("audit_logs")
}
```

### Migrations
```bash
# Create migration
npx prisma migrate dev --name describe_change

# Reset database (DEV ONLY)
npx prisma migrate reset

# Push without migration (prototyping)
npx prisma db push

# Generate client
npx prisma generate
```

---

## Authentication Flow

### Using NextAuth.js

```typescript
// lib/auth.ts
import { NextAuthOptions } from 'next-auth';
import { PrismaAdapter } from '@next-auth/prisma-adapter';
import GoogleProvider from 'next-auth/providers/google';
import EmailProvider from 'next-auth/providers/email';

export const authOptions: NextAuthOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    EmailProvider({
      server: process.env.EMAIL_SERVER,
      from: process.env.EMAIL_FROM,
    }),
  ],
  session: { strategy: 'jwt' },
  pages: {
    signIn: '/login',
    error: '/auth/error',
  },
  callbacks: {
    async session({ token, session }) {
      if (token) {
        session.user.id = token.id;
        session.user.name = token.name;
        session.user.email = token.email;
      }
      return session;
    },
  },
};
```

### Protected Routes
```typescript
// middleware.ts
import { auth } from '@/lib/auth';
import { NextResponse } from 'next/server';

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthPage = req.nextUrl.pathname.startsWith('/login');
  
  if (!isLoggedIn && !isAuthPage) {
    return NextResponse.redirect(new URL('/login', req.url));
  }
  
  return NextResponse.next();
});

export const config = {
  matcher: ['/dashboard/:path*', '/settings/:path*'],
};
```

---

## API Routes Reference

### Common Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user` | Get current user |
| PATCH | `/api/user` | Update user profile |
| DELETE | `/api/user` | Delete account |
| POST | `/api/stripe/checkout` | Create checkout session |
| POST | `/api/stripe/webhook` | Stripe webhook handler |
| GET | `/api/subscriptions` | Get subscription status |
| POST | `/api/webhooks` | Generic webhook handler |

### Webhook Security
```typescript
import { headers } from 'next/headers';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(request: Request) {
  const body = await request.text();
  const signature = headers().get('stripe-signature')!;
  
  const event = stripe.webhooks.constructEvent(
    body,
    signature,
    process.env.STRIPE_WEBHOOK_SECRET!
  );
  
  // Handle event
  switch (event.type) {
    case 'checkout.session.completed':
      // Handle successful checkout
      break;
  }
  
  return NextResponse.json({ received: true });
}
```

---

## Testing Strategy

### Unit Tests (Jest + Testing Library)
```typescript
// __tests__/components/Button.test.tsx
import { render, screen } from '@testing-library/react';
import { Button } from '@/components/ui/button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
});
```

### Integration Tests
```typescript
// __tests__/api/user/route.test.ts
import { GET } from '@/app/api/user/route';
import { mockAuth } from '@/lib/test-utils';

describe('GET /api/user', () => {
  it('returns 401 for unauthenticated users', async () => {
    mockAuth(null);
    const response = await GET();
    expect(response.status).toBe(401);
  });
});
```

### E2E Tests (Playwright)
```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

### Run Tests
```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Coverage
npm run test:coverage
```

---

## Deployment

### Environment Variables

```bash
# Database
DATABASE_URL="postgresql://..."

# Auth
NEXTAUTH_SECRET="..."
NEXTAUTH_URL="https://your-domain.com"
GOOGLE_CLIENT_ID="..."
GOOGLE_CLIENT_SECRET="..."

# Stripe
STRIPE_SECRET_KEY="sk_..."
STRIPE_WEBHOOK_SECRET="whsec_..."
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_..."

# Email
EMAIL_SERVER="smtp://..."
EMAIL_FROM="noreply@yourdomain.com"

# Storage
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
AWS_REGION="us-east-1"
AWS_S3_BUCKET="..."
```

### Vercel Deployment
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

CMD ["node", "server.js"]
```

---

## Example Prompts

### Create a New Feature
```
Create a new feature for [feature name] that includes:
1. Database model with [fields]
2. API routes for CRUD operations
3. Dashboard page with [functionality]
4. Tests for the API routes

Follow the project conventions in CLAUDE.md.
```

### Add Authentication
```
Implement authentication using NextAuth.js with:
- Google OAuth provider
- Email magic link
- Protected routes for /dashboard/*
- User model in Prisma schema

Follow the authentication flow section in CLAUDE.md.
```

### Create API Endpoint
```
Create a POST endpoint at /api/[endpoint-name] that:
- Validates input using Zod
- Checks authentication
- Performs [action]
- Returns [response format]

Follow the API routes reference in CLAUDE.md.
```

### Add Stripe Integration
```
Implement Stripe integration for [product/subscription]:
- Create checkout session endpoint
- Handle webhook events
- Update subscription status in database

Use the webhook security pattern from CLAUDE.md.
```

### Write Tests
```
Write tests for [component/feature]:
- Unit tests for [specific functionality]
- Integration tests for API route
- E2E test for user flow

Follow the testing strategy in CLAUDE.md.
```

---

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check DATABASE_URL
   npx prisma db pull
   
   # Regenerate client
   npx prisma generate
   ```

2. **Authentication Not Working**
   - Check NEXTAUTH_SECRET is set
   - Verify callback URLs in OAuth provider
   - Check middleware matcher patterns

3. **Stripe Webhook Failing**
   - Verify STRIPE_WEBHOOK_SECRET
   - Check webhook URL is accessible
   - Verify event type handling

4. **Build Errors**
   ```bash
   # Clear Next.js cache
   rm -rf .next
   
   # Reinstall dependencies
   rm -rf node_modules package-lock.json
   npm install
   ```

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [Prisma Documentation](https://www.prisma.io/docs)
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [Stripe Documentation](https://stripe.com/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Testing Library Documentation](https://testing-library.com/docs)

---

**Template Version**: 1.0.0  
**Last Updated**: 2026-03-27  
**Compatible With**: Next.js 14+, create-next-app, Nextacular, Shipfast
