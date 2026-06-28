# CLAUDE.md Template for Next.js + SQLite Projects

Ready-to-use CLAUDE.md template for Claude Code when working with Next.js + SQLite applications.

## What's Included

✅ Complete development commands reference  
✅ Architecture overview with directory structure  
✅ Database layer patterns (better-sqlite3)  
✅ API route conventions  
✅ Code style & naming conventions  
✅ Testing patterns (Vitest + RTL)  
✅ Common tasks workflow  
✅ Debugging techniques  
✅ Deployment guides (Vercel + Docker)  
✅ Security checklist  

## Installation

```bash
# Copy to your project root
cp templates/CLAUDE.md /path/to/your/project/CLAUDE.md
```

## Customization

Edit the template to match your project:

1. **Tech Stack**: Update versions (Next.js, TypeScript, etc.)
2. **Database**: Change table names, add your schema
3. **API Routes**: Update examples to match your endpoints
4. **Testing**: Adjust test framework if different
5. **Deployment**: Remove sections you don't need

## Why Use This?

Claude Code reads CLAUDE.md to understand your project context. This template provides:

- **Faster onboarding**: Claude knows your conventions immediately
- **Consistent code**: Follows established patterns
- **Fewer mistakes**: Aware of gotchas and best practices
- **Better suggestions**: Context-aware recommendations

## Template Structure

```markdown
# CLAUDE.md

## Project Overview
## Development Commands
## Architecture
  - Tech Stack
  - Directory Structure
  - Database Layer
  - API Routes
  - Environment Variables
## Code Style & Conventions
## Testing
## Common Tasks
## Debugging
## Deployment
## Gotchas
## Security Checklist
## Resources
```

## Example Usage

After adding CLAUDE.md to your project:

```bash
# Claude Code will now understand your project
claude "Add a new user profile feature"
claude "Fix the database connection issue"
claude "Write tests for the API routes"
```

Claude will follow your conventions, use correct patterns, and avoid common mistakes.

## License

MIT — Use freely in your projects
