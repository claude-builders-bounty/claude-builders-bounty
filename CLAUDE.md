# Claude Builders Bounty: Next.js + SQLite SaaS Project

## Project Overview

This is a production-ready SaaS template built with Next.js 15 App Router and SQLite, designed for rapid deployment and scalability. The template follows modern best practices for web development, with a focus on performance, security, and maintainability.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Database**: SQLite with Prisma ORM
- **Authentication**: NextAuth.js
- **Styling**: Tailwind CSS
- **Type Checking**: TypeScript
- **Deployment**: Vercel (recommended)

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   ├── auth/              # Authentication pages
│   ├── dashboard/         # Dashboard pages
│   └── globals.css        # Global styles
├── components/            # Reusable components
├── lib/                  # Utility functions
│   ├── auth.ts           # Authentication configuration
│   ├── db.ts             # Database connection
│   └── utils.ts          # Helper functions
├── prisma/               # Database schema and migrations
├── public/               # Static assets
└── types/                # TypeScript type definitions
```

## Getting Started

### Prerequisites

- Node.js 18.x or later
- npm or yarn
- SQLite (included by default)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env.local
   ```
4. Run database migrations:
   ```bash
   npx prisma migrate dev
   ```
5. Start the development server:
   ```bash
   npm run dev
   ```

## Development

### Database Management

- View database: `npx prisma studio`
- Create migration: `npx prisma migrate create <name>`
- Reset database: `npx prisma migrate reset`

### Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

Create a `.env.local` file with the following variables:

```env
# Database
DATABASE_URL="file:./dev.db"

# NextAuth
NEXTAUTH_URL="http://localhost:3000"
NEXTAUTH_SECRET="your-secret-here"

# OAuth Providers (example)
GITHUB_ID=""
GITHUB_SECRET=""
```

## Authentication

The project uses NextAuth.js for authentication with support for multiple providers:

1. Email/Password
2. OAuth (GitHub, Google, etc.)
3. Magic Links

Configuration is in `lib/auth.ts`.

## Database Schema

The database schema is defined in `prisma/schema.prisma`. Key entities include:

- `User` - User accounts
- `Account` - OAuth account links
- `Session` - User sessions
- `VerificationToken` - Email verification tokens

## API Routes

API routes are located in `app/api/` and follow REST conventions:

- `/api/auth/*` - Authentication endpoints
- `/api/users/*` - User management
- `/api/subscriptions/*` - Subscription handling

## Deployment

### Vercel (Recommended)

1. Connect your repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npx prisma generate
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Security Best Practices

- All environment variables are stored securely
- CORS is configured for production domains
- Helmet is used for security headers
- Input validation is implemented for all API routes
- Rate limiting is enabled for authentication endpoints

## Performance Optimization

- Next.js automatic static optimization
- Image optimization with Next.js Image component
- Code splitting with dynamic imports
- Database connection pooling
- Caching with Redis (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information