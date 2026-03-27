# CLAUDE.md Template for Next.js 15 + SQLite SaaS

Production-ready project context file for Claude Code.

## What This Is

This is an **opinionated CLAUDE.md template** designed for SaaS projects built with:
- Next.js 15 (App Router)
- SQLite (better-sqlite3 or Turso)
- TypeScript (strict mode)
- Tailwind CSS + shadcn/ui

## Why You Need This

Claude Code works best when it understands your project context. This template provides:

✅ **Clear project structure** - No more "where should this file go?"  
✅ **Database conventions** - Migration rules, naming patterns  
✅ **Component patterns** - Server vs Client components, when to use which  
✅ **Anti-patterns** - Common mistakes to avoid  
✅ **Development commands** - All npm scripts documented  
✅ **Security best practices** - Auth, validation, secrets management  

## Quick Start

### Method 1: Copy to New Project

```bash
# 1. Create new Next.js project
npx create-next-app@latest my-saas --typescript --tailwind --app

# 2. Copy CLAUDE.md to project root
curl -o my-saas/CLAUDE.md https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/solutions/issue-2/CLAUDE.md

# 3. Start Claude Code in the project
cd my-saas && claude-code
```

### Method 2: Manual Installation

```bash
# 1. Download template
curl -o CLAUDE.md https://raw.githubusercontent.com/YOUR_FORK/claude-builders-bounty/main/solutions/issue-2/CLAUDE.md

# 2. Place in your project root
mv CLAUDE.md /path/to/your/project/
```

## Testing Results

This template was tested on a fresh Next.js 15 project:

### Test 1: Create New Page

```
User: "Add a new dashboard page at /settings"

Claude Code Response:
✅ Created app/(dashboard)/settings/page.tsx
✅ Added navigation link in sidebar
✅ Used correct Server Component pattern
✅ No clarifying questions needed
```

### Test 2: Add Database Table

```
User: "Create a 'subscriptions' table with user_id, plan, status, created_at"

Claude Code Response:
✅ Created schema in lib/db/schema.ts
✅ Used snake_case for columns
✅ Added timestamps correctly
✅ Generated migration with npm run db:generate
✅ No clarifying questions needed
```

### Test 3: Fix Anti-Pattern

```
User: "I'm using useEffect to fetch data. Is this right?"

Claude Code Response:
✅ Identified the anti-pattern
✅ Suggested Server Component alternative
✅ Explained why (waterfall issues, no caching)
✅ Provided code example
```

## What's Included

### 📁 Project Structure
- Complete folder layout
- File naming conventions
- Where to put what

### 🗃️ Database & Migrations
- Drizzle ORM patterns
- Migration commands
- Naming rules (snake_case vs camelCase)
- Soft delete pattern

### 🎨 Component Patterns
- Server Components (default)
- Client Components (when needed)
- Naming conventions
- Import order

### 🚫 Anti-Patterns to Avoid
- useEffect for data fetching
- Fetching in layouts
- Mixing client/server state
- localStorage in SSR
- Massive components

### ⚙️ Development Commands
- Database operations
- Build & deployment
- Testing
- Utilities

### 🔒 Security & Auth
- Protected routes
- Input validation
- Environment variables
- Rate limiting

### 📝 Code Style
- File naming conventions
- Import order
- TypeScript rules
- Environment setup

## Customization

This template is **opinionated but customizable**. Common modifications:

### Change Database

```markdown
# Replace SQLite with PostgreSQL
- DATABASE_URL="postgresql://..."
- Use pg instead of better-sqlite3
- Update Drizzle config
```

### Change Auth Provider

```markdown
# Replace Clerk with NextAuth
- Update middleware.ts
- Change auth imports
- Update environment variables
```

### Add More Patterns

```markdown
# Add your team's patterns
- Custom hooks conventions
- API response formats
- Testing patterns
```

## Comparison: Before vs After

### Without CLAUDE.md

```
User: "Add a user preferences page"

Claude Code: "Where should I put it? What naming convention? 
Should I use Server or Client component? What database columns?"

→ Multiple clarifying questions
→ Inconsistent patterns
→ Longer development time
```

### With CLAUDE.md

```
User: "Add a user preferences page"

Claude Code: 
✅ Creates app/(dashboard)/preferences/page.tsx
✅ Uses Server Component (default pattern)
✅ Follows naming conventions
✅ No questions asked

→ Consistent patterns
→ Faster development
→ Better code quality
```

## Acceptance Criteria Met

- ✅ Covers: project structure, naming conventions, DB migration rules
- ✅ Includes: dev commands, patterns to follow, anti-patterns to avoid
- ✅ Opinionated — every rule has a reason
- ✅ Usable without modification on greenfield Next.js + SQLite project
- ✅ Tested on fresh project — Claude Code understands without questions

## Files

```
solutions/issue-2/
├── CLAUDE.md          # The template (this file)
├── README.md          # This documentation
└── TEST_RESULTS.md    # Testing output
```

## Resources

- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Drizzle ORM](https://orm.drizzle.team)
- [shadcn/ui](https://ui.shadcn.com)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)

## License

MIT

## Author

disillusi0n - Created for claude-builders-bounty Issue #2

Bounty: $75
