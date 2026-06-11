# CLAUDE.md

## Project Setup

### Prerequisites
- Node.js >= 18
- SQLite3 >= 3.36
- npm >= 9

### Installation
```bash
npm install
npm run setup-db
```

### Development
```bash
npm run dev
```

## Code Style

- Use TypeScript for all new files
- Follow Next.js App Router conventions
- SQLite queries must use prepared statements
- Component naming: PascalCase for components, camelCase for utilities

## Database

### Schema
- Location: `prisma/schema.prisma`
- Migrations: `npm run db:migrate`

### Best Practices
- Always use parameterized queries
- Handle NULL values explicitly
- Index foreign keys

## Testing

```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration
```

## Deployment

```bash
npm run build
npm run start
```

Environment variables required:
- DATABASE_URL
- NODE_ENV=production
