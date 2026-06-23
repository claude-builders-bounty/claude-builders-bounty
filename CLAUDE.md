# Next.js + SQLite Project Instructions

## Build & Run Commands
- Dev server: `npm run dev` or `pnpm dev`
- Build project: `npm run build` or `pnpm build`
- Start prod server: `npm start` or `pnpm start`
- Lint code: `npm run lint` or `pnpm lint`

## Database Commands (Prisma/Drizzle)
- Push schema changes: `npx prisma db push` or `npx drizzle-kit push:sqlite`
- Generate client: `npx prisma generate` or `npx drizzle-kit generate:sqlite`
- UI Explorer: `npx prisma studio` or `npx drizzle-kit studio`

## Coding Style & Conventions
- Use **Next.js App Router** (`app/` directory) as the default architecture.
- Use **TypeScript** with strict mode enabled for all new files.
- Use **Tailwind CSS** for styling, avoid raw CSS/SCSS files unless necessary.
- **Server Actions:** Place database mutations in `actions.ts` files. Keep components clean.
- **Components:** Default to React Server Components (RSC). Add `'use client'` at the top ONLY when you need interactivity (hooks, state, event listeners).
- **SQLite Configuration:** Use absolute path or relative `./` for DB connection in dev (e.g., `file:./dev.db`). 
- **Git:** Never commit `*.db` or `*.sqlite` files to the repository. Ensure they are in `.gitignore`.
- Export components as default exports.
- Follow functional programming paradigms where possible.

## Formatting & Linting
- Use Prettier for formatting.
- Double quotes for strings (unless configured otherwise), 2 spaces for indentation.